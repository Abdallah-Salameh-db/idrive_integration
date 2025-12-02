# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from ..services import check_or_create_customer

from ..utils import (
    data_response,
    authenticate_token,
)


class CustomerController(http.Controller):

    @authenticate_token
    @http.route(
        "/v1/api/idrive/customer",
        auth="none",
        type="http",
        methods=["POST"],
        csrf=False,
    )
    def check_or_create_customer(self):
        try:
            return check_or_create_customer(request)
        except Exception as e:
            return data_response(str(e), 500)

    @authenticate_token
    @http.route(
        ["/v1/api/idrive/states"],
        auth="none",
        type="http",
        methods=["GET"],
        csrf=False,
    )
    def get_states(self):
        states = request.env["res.country.state"].search(
            [("country_id.code", "=", "SA")],
            order="name ASC",
        )
        states_list = []
        for state in states:
            states_list.append(
                {
                    "id": state.id,
                    "name": state.name,
                    "code": state.code,
                }
            )
        states = states_list
        return data_response(
            {
                "message": "States retrieved successfully",
                "status": "success",
                "states": states,
                "status_code": 200,
            },
            200,
        )
