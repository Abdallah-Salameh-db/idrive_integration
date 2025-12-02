# -*- coding: utf-8 -*-
{
    "name": "IDrive Invoice Integration",
    "summary": "Integration with IDrive for invoice management",
    "description": """
        Integration with IDrive for invoice management
    """,
    "images": ["/static/description/icon.png"],
    "author": "Abdallah Salameh",
    "category": "Accounting",
    "version": "1.0",
    "depends": ["base", "account", "product", "base", "mail_plugin"],
    "data": [
        "views/account_move.xml",
        "views/product_template.xml",
        "views/res_partner.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
