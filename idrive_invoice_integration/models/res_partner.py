# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"
    _description = "Res Partner"

    idrive_user_id = fields.Char(string="IDrive Customer")
