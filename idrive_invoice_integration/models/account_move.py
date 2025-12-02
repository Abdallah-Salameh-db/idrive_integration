# -*- coding: utf-8 -*-

import uuid
from odoo import models, fields, api


class IDriveInvoice(models.Model):
    _inherit = "account.move"
    _description = "IDrive Invoice"

    idrive_invoice_id = fields.Char(string="IDrive Invoice")
    idrive_uuid_certificate = fields.Char(string="IDrive UUID Certificate")
    idrive_invoice_url = fields.Char(string="IDrive Invoice URL")

    _sql_constraints = [
        (
            "unique_idrive_uuid_certificate",
            "UNIQUE(idrive_uuid_certificate)",
            "The IDrive UUID must be unique!",
        )
    ]

    def _compute_idrive_invoice_url(self):
        for invoice in self:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            invoice.idrive_invoice_url = (
                f"{base_url}"
                + "/invoice_report/"
                + f"{invoice.idrive_uuid_certificate}"
            )

    # def regenerate_uuid_certificate(self):
    #     for invoice in self:
    #         if not invoice.idrive_uuid_certificate:
    #             invoice.idrive_uuid_certificate = str(uuid.uuid4().hex)
    #             invoice._compute_idrive_invoice_url()
    def regenerate_uuid_certificate(self):
        for invoice in self:
            if not invoice.idrive_uuid_certificate:
                while True:
                    new_uuid = str(uuid.uuid4())
                    if not self.search([("idrive_uuid_certificate", "=", new_uuid)]):
                        invoice.idrive_uuid_certificate = new_uuid
                        break
                invoice._compute_idrive_invoice_url()
