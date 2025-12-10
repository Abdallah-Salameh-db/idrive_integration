from odoo import api, fields, models, _
import json
from ..utils import data_response

from odoo.api import SUPERUSER_ID

import logging

_logger = logging.getLogger(__name__)


def check_or_create_invoice(request):
    try:
        data = json.loads(request.httprequest.data)
        _logger.info(f"Data: {data}")
    except ValueError:
        _logger.error("Invalid JSON data")
        return data_response("Invalid JSON data", 400)

    if not all(
        field in data
        for field in [
            "idrive_invoice_id",
            "invoice_date",
            "idrive_user_id",
            "product_lines",
        ]
    ):
        _logger.error("Missing required fields")
        requeued_fields = {
            "idrive_invoice_id": data.get("idrive_invoice_id"),
            "invoice_date": data.get("invoice_date"),
            "idrive_user_id": data.get("idrive_user_id"),
            "product_lines": data.get("product_lines"),
        }

        # Check for missing required fields
        missing_requeued_fields = [
            field for field, value in requeued_fields.items() if not value
        ]
        _logger.error(f"Missing required fields: {', '.join(missing_requeued_fields)}")
        return data_response(
            {
                "message": f"Missing required fields: {', '.join(missing_requeued_fields)}",
                "required_fields": missing_requeued_fields,
            },
            400,
        )
    env = api.Environment(request.cr, SUPERUSER_ID, {"active_test": False})

    invoice_date = data.get("invoice_date")
    idrive_invoice_id = data.get("idrive_invoice_id")
    idrive_user_id = data.get("idrive_user_id")
    product_lines = data.get("product_lines")
    # Validate and fetch journal
    journal = env["account.journal"].browse(9)
    if not journal.exists():
        _logger.error("Journal not found")
        return data_response("Journal not found", 404)

    customer = request.env["res.partner"].search(
        [("idrive_user_id", "=", idrive_user_id)]
    )
    if not customer:
        _logger.error("Customer not found")
        return data_response(
            {
                "message": "Customer not found",
                "status": "NotFound",
                "status_code": 404,
            },
            404,
        )
    vat = 15.0
    tax = (
        env["account.tax"]
        .sudo()
        .search(
            [
                ("amount", "=", vat),
                ("type_tax_use", "=", "sale"),
                ("amount_type", "=", "percent"),
                ("price_include", "=", False),
                ("company_id", "=", env.company.id),
            ],
            limit=1,
        )
    )
    if not tax:
        _logger.error(f"Tax {vat} with price included not found for the company")
        return data_response(
            {
                "message": f"Tax {vat} with price included not found for the company",
                "status": "NotFound",
                "status_code": 404,
            },
            404,
        )
    product_line_fields = [
        "product_id",
        "quantity",
        "description",
        "price",
        "is_tax_included",
    ]
    for line in product_lines:
        if not all(field in line for field in product_line_fields):
            _logger.error(f"Invalid product_lines item: {line}")
            return data_response(
                {
                    "message": f"one or more fields are missing in the product lines item: {line}",
                    "status": "BadRequest",
                    "status_code": 400,
                },
                400,
            )

    idrive_invoice = request.env["account.move"].search(
        [("idrive_invoice_id", "=", idrive_invoice_id)]
    )
    if idrive_invoice:
        _logger.info("IDrive invoice already exists")
        return data_response(
            {
                "message": "IDrive invoice already exists",
                "invoice_data": {
                    "invoice_id": idrive_invoice.id,
                    "idrive_invoice_id": idrive_invoice.idrive_invoice_id,
                    "invoice_number": idrive_invoice.name,
                    "invoice_date": str(
                        idrive_invoice.invoice_date
                    ),  # Convert to string
                    "invoice_date_due": str(
                        idrive_invoice.invoice_date_due
                    ),  # Convert to string
                    "delivery_date": str(
                        idrive_invoice.delivery_date
                    ),  # Convert to string
                    "link": f"{idrive_invoice.idrive_invoice_url}",
                },
                "status": "Exists",
                "status_code": 200,
            },
            200,
        )

    lines = []
    for line in product_lines:
        product = env["product.template"].search(
            [("idrive_product_id", "=", line["product_id"])]
        )
        if not product or not product.exists():
            _logger.error(f"Product with ID {line['product_id']} not found")
            return data_response(
                {
                    "message": f"Product with idrive id {line['product_id']} not found",
                    "status": "NotFound",
                    "status_code": 404,
                },
                404,
            )

        price_unit = line.get("price")
        quantity = line.get("quantity")
        description = line.get("description")
        is_tax_included = line.get("is_tax_included")
        discount = line.get("discount_percentage", 0.0)
        discount_type = line.get("discount_percentage", 0.0) # percentage or fixed
        # Add the 'name' field with the description from the request
        lines.append(
            (
                0,
                0,
                {
                    "product_id": product.id,
                    "name": description,
                    "quantity": quantity,
                    "price_unit": price_unit,
                    "discount": discount,
                    "tax_ids": ([(6, 0, [tax.id])] if is_tax_included else []),
                },
            )
        )

    # Invoice creation values
    invoice_values = {
        "move_type": "out_invoice",
        "partner_id": customer.id,
        "invoice_date": invoice_date,
        "invoice_payment_term_id": False,
        "invoice_line_ids": lines,
        "journal_id": journal.id,
        "company_id": env.company.id,  # Add company_id to invoice values
        "idrive_invoice_id": idrive_invoice_id,
    }

    # If invoice_date_due is provided, add it to the invoice and set delivery_date to the same value
    invoice_date_due = invoice_date
    if invoice_date_due:
        invoice_values["invoice_date_due"] = invoice_date_due
        # Set delivery_date the same as invoice_date_due
        invoice_values["delivery_date"] = invoice_date_due

    # Create the invoice
    invoice = env["account.move"].create(invoice_values)

    # Post the invoice
    invoice.action_post()
    invoice.regenerate_uuid_certificate()
    # reversal_action = invoice.action_register_payment()
    # payment_details = []

    invoice_details = {
        "invoice_id": invoice.id,
        "invoice_number": invoice.name,  # Serial number
        "invoice_date": (str(invoice.invoice_date) if invoice.invoice_date else None),
        "invoice_date_due": (
            str(invoice.invoice_date_due) if invoice.invoice_date_due else None
        ),
        # Convert to string
        "delivery_date": (
            str(invoice.delivery_date) if invoice.delivery_date else None
        ),
        "link": f"{invoice.idrive_invoice_url}",
    }
    res = {
        "message": "Your invoice was created successfully",
        "invoice_data": invoice_details,
        "status": "created",
        "status_code": 201,
    }
    # if payment_details:
    #     res["payment"] = payment_details
    _logger.info(res)
    return data_response(res, 201)
