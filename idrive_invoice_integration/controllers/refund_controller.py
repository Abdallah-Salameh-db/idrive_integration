# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from ..services import (
    check_or_create_refund_transaction,
    check_or_create_partial_refund_transaction,
)

from ..utils import (
    data_response,
    authenticate_token,
)

import logging

_logger = logging.getLogger(__name__)


class RefundTransactionController(http.Controller):

    @authenticate_token
    @http.route(
        "/v1/api/idrive/refund_transaction",
        auth="none",
        type="http",
        methods=["POST"],
        csrf=False,
    )
    def check_or_create_refund_transaction(self):
        try:
            _logger.info(
                "<----- Checking or creating refund transaction API Called ----->"
            )
            return check_or_create_refund_transaction(request)
        except Exception as e:
            return data_response(str(e), 500)

    @authenticate_token
    @http.route(
        "/v1/api/idrive/partial_refund_transaction",
        auth="none",
        type="http",
        methods=["POST"],
        csrf=False,
    )
    def check_or_create_partial_refund_transaction(self):
        try:
            _logger.info(
                "<----- Checking or creating partial refund transaction API Called ----->"
            )
            return check_or_create_partial_refund_transaction(request)
        except Exception as e:
            return data_response(str(e), 500)
