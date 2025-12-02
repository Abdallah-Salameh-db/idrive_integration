# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from ..services import check_or_create_invoice

from ..utils import (
    data_response,
    authenticate_token,
)

import logging

_logger = logging.getLogger(__name__)


class InvoiceController(http.Controller):

    @authenticate_token
    @http.route(
        "/v1/api/idrive/check_or_create_invoice",
        auth="none",
        type="http",
        methods=["POST"],
        csrf=False,
    )
    def check_or_create_invoice(self):
        try:
            _logger.info("<----- Checking or creating invoice API Called ----->")
            return check_or_create_invoice(request)
        except Exception as e:
            return data_response(str(e), 500)

    @http.route(
        ["/invoice_report/<string:idrive_invoice_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def get_invoice_report(
        self, uuid, access_token=None, report_type=None, download=False, **kw
    ):
        invoice = (
            request.env["account.move"]
            .sudo()
            .search([("idrive_uuid_certificate", "=", uuid)], limit=1)
        )
        if not invoice:
            return request.not_found()
        if invoice.move_type in ["out_refund", "in_refund"]:
            return self._show_report(
                model=invoice,
                report_type="pdf",
                report_ref="saudi_quotation.credit_note_report",
                download=download,
            )
        if invoice.partner_id.is_company:
            return self._show_report(
                model=invoice,
                report_type="pdf",
                report_ref="cloud_hosting_api_1.cloud_report_tax_invoice",
                download=download,
            )
        return self._show_report(
            model=invoice,
            report_type="pdf",
            report_ref="saudi_einvoice_knk.report_simplified_tax_invoice",
            download=download,
        )
