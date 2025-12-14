from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    global_discount_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Global Discount Product",
        help="This product will be used to apply discount to the invoice from iDrive application",
        config_parameter="idrive_invoice_integration.global_discount_product",
        readonly=False,
    )
