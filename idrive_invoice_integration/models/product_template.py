# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _description = "Product Template"

    idrive_product_id = fields.Char(string="IDrive Product")
