import json
from ..utils import data_response


import logging

_logger = logging.getLogger(__name__)


def check_or_create_refund_transaction(request):
    _logger.info("<--- Service Creating a new refund transaction --->")
    try:
        data = json.loads(request.httprequest.data)
        _logger.info(f"Data: {data}")
    except ValueError:
        _logger.error("Invalid JSON data")
        return data_response("Invalid JSON data", 400)

    if not all(
        field in data
        for field in [
            "idrive_refund_id",
            "idrive_invoice_id",
            "refund_date",
            "refund_reason",
        ]
    ):
        _logger.error("Missing required fields")
        requeued_fields = {
            "idrive_refund_id": data.get("idrive_refund_id"),
            "idrive_invoice_id": data.get("idrive_invoice_id"),
            "refund_date": data.get("refund_date"),
            "refund_reason": data.get("refund_reason"),
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
    env = request.env

    refund_date = data.get("refund_date")
    idrive_refund_id = data.get("idrive_refund_id")
    idrive_invoice_id = data.get("idrive_invoice_id")
    refund_reason = data.get("refund_reason")

    # Check if the invoice exists
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

    # Create a new refund
    _logger.info("Creating a new refund")
    action = invoice_to_refund.action_reverse()
    _logger.info("Action Fetched Successfully")
    reversal_wizard = (
        env[action["res_model"]]
        .with_context(
            active_ids=invoice_to_refund.ids,
            active_model="account.move",
        )
        .create(
            {
                "journal_id": invoice_to_refund.journal_id.id,  # Field is not precomputed but required
                "reason": refund_reason,
                "date": refund_date,
            }
        )
    )
    _logger.info("Wizard Created Successfully")
    action = reversal_wizard.refund_moves()
    _logger.info("Refund Moves Created Successfully")
    reversal_move = env["account.move"].browse(action["res_id"])
    reversal_move.regenerate_uuid_certificate()
    _logger.info("UUID Certificate Regenerated Successfully")
    reversal_move.write({"idrive_invoice_id": idrive_refund_id})
    _logger.info("IDrive Refund ID Written Successfully")
    reversal_move.action_post()
    _logger.info("Refund Posted Successfully")
    refund_details = {
        "refund_id": reversal_move.id,
        "idrive_refund_id": reversal_move.idrive_invoice_id,
        "refund_number": reversal_move.name,
        "refund_date": str(reversal_move.invoice_date),
        "link": f"{reversal_move.idrive_invoice_url}",
    }
    res = {
        "message": "Your refund was created successfully",
        "refund_data": refund_details,
        "status": "Created",
        "status_code": 201,
    }
    return data_response(res, 201)
