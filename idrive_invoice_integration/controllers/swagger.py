import os
import yaml
import json

from odoo import http
from odoo.http import request
from odoo.modules.module import get_module_path
from werkzeug.exceptions import NotFound

from ..utils.json_response import json_response

import logging

_logger = logging.getLogger(__name__)


class Swagger(http.Controller):

    @http.route(
        ["/v1/api/idrive/swagger"],
        type="http",
        auth="none",
    )
    def swagger_ui(self):
        env_type = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("system.env", default="test")
        ).lower()

        if env_type == "production":
            return NotFound()

        # if request.env.cr.dbname in ["test"]:
        #     return json_response("Swagger disabled in production", "error", 403)

        module_path = get_module_path("idrive_invoice_integration")
        html_path = os.path.join(module_path, "static/src/html/swagger.html")
        with open(html_path, "r") as f:
            html_content = f.read()
        return html_content

    @http.route("/v1/api/swagger.json", type="http", auth="none")
    def swagger_spec(self):

        env_type = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("system.env", default="test")
        ).lower()

        if env_type == "production":
            return NotFound()

        # if request.env.cr.dbname in ["test"]:
        #     return json_response("Swagger disabled in production", "error", 403)

        module_path = get_module_path("idrive_invoice_integration")
        docs_path = os.path.join(module_path, "controllers", "docs")
        yaml_files = sorted(
            [f for f in os.listdir(docs_path) if f.lower().endswith((".yml", ".yaml"))],
            key=lambda x: yaml.safe_load(open(os.path.join(docs_path, x))).get(
                "sequence", 999
            ),
        )
        spec = {
            "openapi": "3.0.2",
            "info": {"title": "IDrive Invoice Integration API", "version": "V1.0"},
            "paths": {},
            "components": {
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "Token",
                    }
                },
            },
            "security": [{"BearerAuth": []}],
        }
        for file_name in yaml_files:
            full_path = os.path.join(docs_path, file_name)
            if os.path.exists(full_path):
                with open(full_path, "r") as stream:
                    data = yaml.safe_load(stream)
                    spec["paths"].update(data.get("paths", {}))
                    spec["components"].update(data.get("components", {}))
            else:
                _logger.warning(f"Swagger YAML file not found: {full_path}")
        return http.Response(json.dumps(spec), content_type="application/json")
