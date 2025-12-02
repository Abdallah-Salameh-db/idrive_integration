import functools
from odoo.http import request


def authenticate_token(func):
    @functools.wraps(func)
    def wrap(*args, **kwargs):
        IrHttp = request.env["ir.http"].sudo()
        IrHttp._auth_method_outlook()
        return func(*args, **kwargs)

    return wrap
