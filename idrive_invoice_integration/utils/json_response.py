import json
from odoo.http import Response


def json_response(message, status, status_code):
    """Create a generic response with the given message, status and status code."""
    res = {"message": message, "status": status, "status_code": status_code}
    return Response(
        json.dumps(res, sort_keys=True, indent=4),
        content_type="application/json;charset=utf-8",
        status=status_code,
    )


def data_response(data, status_code=200):
    """Create a response with the given data, status and status code."""
    # res = {"data": data, "status_code": status_code}
    return Response(
        json.dumps(data, sort_keys=True, indent=4),
        content_type="application/json;charset=utf-8",
        status=status_code,
    )
