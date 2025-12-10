import json
from ..utils import data_response


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
        required_address_fields = []
        if is_company == True:
            required_address_fields = [
                "building_number",
                "plot_id",
                "street",
                "neighborhood",
                "city",
                "state_code",
                "zip",
            ]

        if address and not all(field in address for field in required_address_fields):
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
            "street": address.get("street") if address.get("street") else "",
            "street2": (
                address.get("neighborhood") if address.get("neighborhood") else ""
            ),
            "city": address.get("city") if address.get("city") else "",
            "zip": address.get("zip") if address.get("zip") else "",
            "country_id": country.id,
            "state_id": state.id if state else None,
        }
        if is_company == True:
            customer_data.update(
                {
                    "l10n_sa_edi_building_number": (
                        address.get("building_number")
                        if address.get("building_number")
                        else ""
                    ),
                    "l10n_sa_edi_plot_identification": (
                        address.get("plot_id") if address.get("plot_id") else ""
                    ),
                    "l10n_sa_additional_identification_scheme": tax_type,
                    "l10n_sa_additional_identification_number": cr_number,
                    "vat": tax_number,
                }
            )
        customer = request.env["res.partner"].search(
            [("idrive_user_id", "=", idrive_user_id)], limit=1
        )
        if customer:
            _logger.info("IDrive customer already exists")
            customer.write(customer_data)
            msg = "IDrive customer already exists"
            status = "Exist"
            status_code = 200
        else:
            customer = request.env["res.partner"].create(customer_data)
            msg = "Customer created successfully"
            status = "Created"
            status_code = 201

        return_customer_data = {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "address": {
                "street": customer.street,
                "neighborhood": customer.street2,
                "city": customer.city,
                "zip": customer.zip,
                "state_code": customer.state_id.code,
                "building_number": customer.l10n_sa_edi_building_number,
                "plot_id": customer.l10n_sa_edi_plot_identification,
            },
            "tax_type": customer.l10n_sa_additional_identification_scheme,
            "tax_number": customer.vat,
            "cr_number": customer.l10n_sa_additional_identification_number,
        }
        res = {
            "message": msg,
            "status": status,
            "customer_data": return_customer_data,
            "status_code": status_code,
        }
        return data_response(res, status_code)

    except Exception as e:
        _logger.error(f"Error: {e}")
        res = {
            "message": str(e),
            "status": "Error",
            "status_code": 500,
        }
        return data_response(res, 500)
