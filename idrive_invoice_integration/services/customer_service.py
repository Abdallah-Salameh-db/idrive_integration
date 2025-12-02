from odoo import api, fields, models, _
import json
from ..utils import data_response

from odoo.api import SUPERUSER_ID

import logging
import re

_logger = logging.getLogger(__name__)


def check_or_create_customer(request):
    """Create a new partner record with the provided details.
    Returns a success message with the partner's ID or an error message if the required fields are missing
    or if the partner already exists with the same ch_platform."""
    try:
        _logger.info("<--- Service Creating customer --->")
        data = json.loads(request.httprequest.data)
        _logger.info(f"Data: {data}")
        env = request.env
        if "is_company" not in data:
            _logger.error("Missing required field is_company")
            res = {
                "message": "Missing required field is_company",
                "status": "BadRequest",
                "status_code": 400,
            }
            return data_response(res, 400)
        is_company = data.get("is_company")
        required_fields = [
            "idrive_user_id",
            "name",
            "email",
            "phone",
            "address",
        ]
        if is_company == True:
            required_fields.extend(
                [
                    "tax_type",
                    "tax_number",
                    "cr_number",
                ]
            )
        if not all(field in data for field in required_fields):
            missing_fields = [field for field in required_fields if field not in data]
            _logger.error(f"Missing required fields: {', '.join(missing_fields)}")
            res = {
                "message": f"Missing required fields: {', '.join(missing_fields)}",
                "status": "BadRequest",
                "status_code": 400,
            }
            return data_response(res, 400)
        address = data.get("address")
        required_address_fields = [
            "street",
            "neighborhood",
            "city",
            "state_code",
            "zip",
        ]
        if is_company == True:
            required_address_fields.extend(
                [
                    "building_number",
                    "plot_id",
                ]
            )
        if not all(field in address for field in required_address_fields):
            missing_address_fields = [
                field for field in required_address_fields if field not in address
            ]
            _logger.error(
                f"Missing required address fields: {', '.join(missing_address_fields)}"
            )
            res = {
                "message": f"Missing required address fields: {', '.join(missing_address_fields)}",
                "status": "BadRequest",
                "status_code": 400,
            }
            return data_response(res, 400)

        idrive_user_id = data.get("idrive_user_id")
        existing_customer = request.env["res.partner"].search(
            [("idrive_user_id", "=", idrive_user_id)], limit=1
        )
        if existing_customer:
            _logger.info("IDrive customer already exists")
            return_customer_data = {
                "id": existing_customer.id,
                "name": existing_customer.name,
                "email": existing_customer.email,
                "phone": existing_customer.phone,
                "address": {
                    "street": existing_customer.street,
                    "neighborhood": existing_customer.street2,
                    "city": existing_customer.city,
                    "zip": existing_customer.zip,
                    "state_code": existing_customer.state_id.code,
                    "building_number": existing_customer.l10n_sa_edi_building_number,
                    "plot_id": existing_customer.l10n_sa_edi_plot_identification,
                },
                "tax_type": existing_customer.l10n_sa_additional_identification_scheme,
                "tax_number": existing_customer.vat,
                "cr_number": existing_customer.l10n_sa_additional_identification_number,
            }
            res = {
                "message": "IDrive customer already exists",
                "status": "Exist",
                "customer_data": return_customer_data,
                "status_code": 200,
            }
            return data_response(res, 200)

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        tax_type = data.get("tax_type") if is_company == True else None
        tax_number = data.get("tax_number") if is_company == True else None
        cr_number = data.get("cr_number") if is_company == True else None

        address = data.get("address")

        # Validate phone 9 digits numbers prefix with +966, start with 5 and just numbers
        if phone and not re.match(r"^\+9665\d{8}$", phone):
            _logger.error(
                f"Invalid phone: {phone} must be 9 digits prefix with +966, start with 5 and just numbers (+9665xxxxxxxx)"
            )
            res = {
                "message": f"Invalid phone: {phone} must be 9 digits prefix with +966, start with 5 and just numbers (+9665xxxxxxxx)",
                "status": "BadRequest",
                "status_code": 400,
            }
            return data_response(res, 400)
        # Validate address state_code if existing in database
        state = None
        country = env["res.country"].search([("code", "=", "SA")], limit=1)
        if address and address.get("state_code"):
            state = env["res.country.state"].search(
                [
                    ("code", "=", address.get("state_code")),
                    ("country_id", "=", country.id),
                ],
                limit=1,
            )
            if not state:
                _logger.error(
                    f"Invalid state_code: {address.get("state_code")} must be existing in database"
                )
                res = {
                    "message": f"Invalid state_code: {address.get("state_code")} must be existing in database",
                    "status": "BadRequest",
                    "status_code": 400,
                }
                return data_response(res, 400)

        # Validate tax_type
        if is_company == True:
            if tax_type not in [
                "TIN",
                "CRN",
                "MOM",
                "MLS",
                "700",
                "SAG",
                "NAT",
                "GCC",
                "IQA",
                "PAS",
                "OTH",
            ]:
                _logger.error(f"Invalid tax_type: {tax_type}")
                res = {
                    "message": f"Invalid tax_type: {tax_type}",
                    "status": "BadRequest",
                    "status_code": 400,
                }
                return data_response(res, 400)
            # Validate tax_number 15 digits start with 3 end with 3 and just numbers
            if tax_number and not re.match(r"^3\d{13}3$", tax_number):
                _logger.error(
                    f"Invalid tax_number: {tax_number} must be 15 digits start with 3 end with 3 and just numbers"
                )
                res = {
                    "message": f"Invalid tax_number: {tax_number} must be 15 digits start with 3 end with 3 and just numbers",
                    "status": "BadRequest",
                    "status_code": 400,
                }
                return data_response(res, 400)
            # Validate cr_number 10 digits numbers
            if cr_number and not re.match(r"^\d{10}$", cr_number):
                _logger.error(
                    f"Invalid cr_number: {cr_number} must be 10 digits and just numbers"
                )
                res = {
                    "message": f"Invalid cr_number: {cr_number} must be 10 digits and just numbers",
                    "status": "BadRequest",
                    "status_code": 400,
                }
                return data_response(res, 400)

        customer_data = {
            "is_company": is_company,
            "idrive_user_id": idrive_user_id,
            "name": name,
            "email": email,
            "phone": phone,
            "street": address.get("street"),
            "street2": address.get("neighborhood"),
            "city": address.get("city"),
            "zip": address.get("zip"),
            "country_id": country.id,
            "state_id": state.id if state else None,
        }
        if is_company == True:
            customer_data.update(
                {
                    "l10n_sa_edi_building_number": address.get("building_number"),
                    "l10n_sa_edi_plot_identification": address.get("plot_id"),
                    "l10n_sa_additional_identification_scheme": tax_type,
                    "l10n_sa_additional_identification_number": cr_number,
                    "vat": tax_number,
                }
            )
        new_customer = request.env["res.partner"].create(customer_data)
        return_customer_data = {
            "id": new_customer.id,
            "name": new_customer.name,
            "email": new_customer.email,
            "phone": new_customer.phone,
            "address": {
                "street": new_customer.street,
                "neighborhood": new_customer.street2,
                "city": new_customer.city,
                "zip": new_customer.zip,
                "state_code": new_customer.state_id.code,
                "building_number": new_customer.l10n_sa_edi_building_number,
                "plot_id": new_customer.l10n_sa_edi_plot_identification,
            },
            "tax_type": new_customer.l10n_sa_additional_identification_scheme,
            "tax_number": new_customer.vat,
            "cr_number": new_customer.l10n_sa_additional_identification_number,
        }
        res = {
            "message": "Customer created successfully",
            "status": "Created",
            "customer_data": return_customer_data,
            "status_code": 201,
        }
        return data_response(res, 201)

    except Exception as e:
        _logger.error(f"Error: {e}")
        res = {
            "message": str(e),
            "status": "Error",
            "status_code": 500,
        }
        return data_response(res, 500)
