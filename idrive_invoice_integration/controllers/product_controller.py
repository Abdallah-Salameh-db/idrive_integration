# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from ..services import check_or_create_product, check_or_create_multiple_products

from ..utils import (
    data_response,
    authenticate_token,
)

import logging

_logger = logging.getLogger(__name__)


class ProductController(http.Controller):

    @authenticate_token
    @http.route(
        "/v1/api/idrive/product",
        auth="none",
        type="http",
        methods=["POST"],
        csrf=False,
    )
    def check_or_create_product(self):
        """
        Create a new product if it does not already exist.
        """
        try:
            return check_or_create_product(request)
        except Exception as e:
            return data_response(str(e), 500)

    @authenticate_token
    @http.route(
        "/v1/api/idrive/products",
        auth="none",
        type="http",
        methods=["POST"],
        csrf=False,
    )
    def api_create_products(self):
        """
        Create multiple new products if they do not already exist.
        """
        try:
            _logger.info("<--- Creating multiple products --->")
            return check_or_create_multiple_products(request)
        except Exception as e:
            return data_response(str(e), 500)
