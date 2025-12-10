import json
from ..utils import data_response

import logging

_logger = logging.getLogger(__name__)


def check_or_create_partial_refund_transaction(request):
    """
    Process a refund for specific lines in an invoice.
    """

    _logger.info("<--- Service Creating a partial refund transaction --->")
    try:
        data = json.loads(request.httprequest.data)
        _logger.info(f"Data for partial refund transaction\n: {data}")
    except ValueError:
        _logger.error("Invalid JSON data")
        return data_response("Invalid JSON data", 400)

    env = request.env
    required_fields = [
        "idrive_refund_id",
        "idrive_invoice_id",
        "refund_date",
        "refund_reason",
        "product_lines",
    ]

    if not all(field in data for field in required_fields):
        missing_requeued_fields = [field for field, value in data.items() if not value]
        _logger.error(f"Missing required fields: {', '.join(missing_requeued_fields)}")
        return data_response(
            {
                "message": f"Missing required fields: {', '.join(missing_requeued_fields)}",
                "required_fields": missing_requeued_fields,
                "status": "BadRequest",
                "status_code": 400,
            },
            400,
        )

    idrive_refund_id = data.get("idrive_refund_id")
    idrive_invoice_id = data.get("idrive_invoice_id")
    refund_date = data.get("refund_date")
    refund_reason = data.get("refund_reason")
    product_lines = data.get("product_lines")

    product_required_fields = [
        "idrive_product_id",
        "quantity",
        "price_unit",
        "description",
    ]
    if not all(field in product_lines for field in product_required_fields):
        missing_requeued_fields = [
            field for field, value in product_lines.items() if not value
        ]
        _logger.error(f"Missing required fields: {', '.join(missing_requeued_fields)}")
        return data_response(
            {
                "message": f"Missing required fields: {', '.join(missing_requeued_fields)}",
                "required_fields": missing_requeued_fields,
                "status": "BadRequest",
                "status_code": 400,
            },
            400,
        )

    invoice_to_refund = env["account.move"].search(
        [("idrive_invoice_id", "=", idrive_invoice_id)]
    )
    if not invoice_to_refund:
        _logger.error("Invoice to refund not found")
        return data_response(
            {
                "message": "Invoice to refund not found",
                "status": "NotFound",
                "status_code": 404,
            },
            404,
        )

    # Check if the refund already exists
    existing_refund = env["account.move"].search(
        [("idrive_invoice_id", "=", idrive_refund_id)]
    )
    if existing_refund:
        _logger.info("IDrive refund already exists")
        return data_response(
            {
                "message": "IDrive refund already exists",
                "refund_data": {
                    "refund_id": existing_refund.id,
                    "idrive_refund_id": existing_refund.idrive_invoice_id,
                    "refund_number": existing_refund.name,
                    "refund_date": str(
                        existing_refund.invoice_date
                    ),  # Convert to string
                    "refund_date_due": str(existing_refund.invoice_date_due),
                    "link": f"{existing_refund.idrive_invoice_url}",
                },
                "status": "Exists",
                "status_code": 200,
            },
            200,
        )

    product_map = {
        (pl.get("idrive_product_id"), pl.get("description").strip()): pl
        for pl in product_lines
    }

    _logger.info(f"Product map: {product_map}")

    # Create Credit Note
    action = invoice_to_refund.sudo().action_reverse()
    reversal_wizard = (
        request.env[action["res_model"]]
        .with_context(
            active_ids=invoice_to_refund.ids,
            active_model="account.move",
        )
        .create(
            {
                "journal_id": invoice_to_refund.journal_id.id,
                "reason": refund_reason,
                "date": refund_date,
            }
        )
    )
    _logger.info("Reversal wizard fetched successfully")

    action = reversal_wizard.refund_moves()
    reversal_move = request.env["account.move"].browse(action["res_id"])
    reversal_move.write({"idrive_invoice_id": idrive_refund_id})

    reversal_move.write({"delivery_date": refund_date})

    _logger.info("Refund created")

    # Remove lines not matching product_id and name
    lines_to_remove = []

    for line in reversal_move.invoice_line_ids:
        key = (line.idrive_product_id, line.name.strip())
        product_data = product_map.get(key)
        if not product_data:
            lines_to_remove.append(line)
        else:
            qty = product_data.get("quantity", line.quantity)
            price = product_data.get("price_unit", line.price_unit)
            line.write(
                {
                    "quantity": qty,
                    "price_unit": price,
                }
            )

    if lines_to_remove:
        # lines_to_remove ممكن تكون list، حولها لـ recordset
        lines_to_remove_rs = request.env["account.move.line"].browse(
            [l.id for l in lines_to_remove]
        )
        reversal_move.invoice_line_ids -= lines_to_remove_rs

    _logger.info("Lines removed successfully")

    reversal_move.regenerate_uuid_certificate()
    reversal_move.action_post()

    refund_details = {
        "refund_id": reversal_move.id,
        "refund_number": reversal_move.name,  # Serial number
        "refund_date_due": (
            str(reversal_move.invoice_date_due)
            if reversal_move.invoice_date_due
            else None
        ),
        # Convert to string
        "delivery_date": (
            str(reversal_move.delivery_date) if reversal_move.delivery_date else None
        ),
        "link": f"{reversal_move.ch_custom_portal_url}",
    }
    _logger.info("Refund details fetched successfully")
    res = {
        "message": "Refund processed successfully",
        "refund": refund_details,
        "status_code": 200,
        "status": "Created",
    }

    return data_response(res, 200)
