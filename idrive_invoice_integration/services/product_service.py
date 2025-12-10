import json
from ..utils import data_response


import logging

_logger = logging.getLogger(__name__)


def check_or_create_product(request):
    """
    Create a new product if it does not already exist.
    """
    try:
        data = json.loads(request.httprequest.data)

        env = request.env
        required_fields = ["idrive_product_id", "name", "list_price"]
        if not all(field in data for field in required_fields):
            _logger.error("Missing required fields for product creation")
            return data_response(
                {
                    "message": "Missing required fields for product creation",
                    "required_fields": required_fields,
                    "status": "BadRequest",
                    "status_code": 400,
                },
                400,
            )
        tax = 15.0
        tax = (
            env["account.tax"]
            .sudo()
            .search(
                [
                    ("amount", "=", tax),
                    ("type_tax_use", "=", "sale"),
                    ("amount_type", "=", "percent"),
                    ("price_include", "=", False),
                    ("company_id", "=", env.company.id),
                ],
                limit=1,
            )
        )
        if not tax:
            _logger.error(f"Tax {tax} with price included not found for the company")
            return data_response(
                {
                    "message": f"Tax {tax} with price included not found for the company",
                    "status": "NotFound",
                    "status_code": 404,
                },
                404,
            )
        idrive_product_id = data.get("idrive_product_id")
        name = data.get("name")
        list_price = data.get("list_price")

        product = env["product.template"].search(
            [("idrive_product_id", "=", idrive_product_id)], limit=1
        )
        if product:
            # Update the product if it already exists
            product.write(
                {
                    "name": name,
                    "list_price": list_price,
                    "taxes_id": [(6, 0, [tax.id])] if tax else [],
                }
            )
        else:
            # Create a new product if it does not already exist
            product = env["product.template"].create(
                {
                    "name": name,
                    "idrive_product_id": idrive_product_id,
                    "list_price": list_price,
                    "type": "service",
                    "company_id": env.company.id,
                    "categ_id": env.ref("product.product_category_all").id,
                    "taxes_id": [(6, 0, [tax.id])] if tax else [],
                }
            )

        res = {
            "message": "Product processed successfully",
            "product": {
                "name": product.name,
                "product_id": product.id,
                "idrive_product_id": product.idrive_product_id,
                "list_price": product.list_price,
            },
            "status_code": 201,
            "status": "Created",
        }
        return data_response(res, 201)

    except Exception as e:
        res = {
            "message": str(e),
            "status": "Error",
            "status_code": 500,
        }
        return data_response(res, 500)


def check_or_create_multiple_products(request):
    """
    Create multiple new products if they do not already exist.
    """
    try:
        _logger.info("<--- Service Creating multiple products --->")
        data = json.loads(request.httprequest.data)
        _logger.info(f"Data: {data}")
        post_products = data.get("products", [])

        if not post_products:
            _logger.error("No products data provided")
            return data_response("No products data provided", 400)

        env = request.env
        required_fields = ["idrive_product_id", "name", "list_price"]
        for product_data in post_products:
            _logger.info(f"Product data: {product_data}")
            if not all(field in product_data for field in required_fields):
                _logger.error("Missing required fields for product creation")
                return data_response(
                    {
                        "message": "Missing required fields for product creation",
                        "required_fields": required_fields,
                        "status": "BadRequest",
                        "status_code": 400,
                    },
                    400,
                )
        tax = 15.0
        tax = (
            env["account.tax"]
            .sudo()
            .search(
                [
                    ("amount", "=", tax),
                    ("type_tax_use", "=", "sale"),
                    ("amount_type", "=", "percent"),
                    ("price_include", "=", False),
                    ("company_id", "=", env.company.id),
                ],
                limit=1,
            )
        )
        _logger.info(f"Tax: {tax}")
        if not tax:
            _logger.error(f"Tax {tax} with price included not found for the company")
            return data_response(
                {
                    "message": f"Tax {tax} with price included not found for the company",
                    "status": "NotFound",
                    "status_code": 404,
                },
                404,
            )
        products = []
        for product_data in post_products:

            idrive_product_id = product_data.get("idrive_product_id")
            name = product_data.get("name")
            list_price = product_data.get("list_price")
            _logger.info(
                f"Fetching existing product with idrive product id: {idrive_product_id}"
            )
            existing_product = request.env["product.template"].search(
                [("idrive_product_id", "=", idrive_product_id)], limit=1
            )

            if existing_product:
                # Update the product if it already exists
                existing_product.write(
                    {
                        "name": name,
                        "list_price": list_price,
                        "taxes_id": [(6, 0, [tax.id])] if tax else [],
                    }
                )
                products.append(
                    {
                        "name": existing_product.name,
                        "product_id": existing_product.id,
                        "idrive_product_id": existing_product.idrive_product_id,
                        "list_price": existing_product.list_price,
                    }
                )
            else:
                # Create a new product if it does not already exist
                _logger.info(
                    f"Creating new product with idrive product id: {idrive_product_id}"
                )
                new_product = env["product.template"].create(
                    {
                        "name": name,
                        "idrive_product_id": idrive_product_id,
                        "list_price": list_price,
                        "type": "service",
                        "company_id": env.company.id,
                        "categ_id": env.ref("product.product_category_all").id,
                        "taxes_id": [(6, 0, [tax.id])] if tax else [],
                    }
                )
                products.append(
                    {
                        "name": new_product.name,
                        "product_id": new_product.id,
                        "idrive_product_id": new_product.idrive_product_id,
                        "list_price": new_product.list_price,
                    }
                )

        _logger.info(f"Products: {products}")
        res = {
            "message": "Products processed successfully",
            "products": products,
            "status_code": 201,
            "status": "Created",
        }
        return data_response(res, 201)

    except Exception as e:
        res = {
            "message": str(e),
            "status": "Error",
            "status_code": 500,
        }
        return data_response(res, 500)
