from .json_response import json_response


def validate_user_data(request):
    uid = request.httprequest.headers.get("X-Uid")
    if not uid:
        return json_response("Missing required header: X-Uid", "BadRequest", 400)
    user = request.env["third.party.employees"].search(
        [("third_employee_id", "=", uid)]
    )
    if not user:
        return json_response("User not found", "BadRequest", 400)

    employee_ids_string = request.httprequest.headers.get("X-Employ-Ids")
    if not employee_ids_string:
        return json_response("Missing required header: X-Employ-Ids", "BadRequest", 400)
    employee_ids_header = [
        int(e.strip()) for e in employee_ids_string.split(",") if e.strip().isdigit()
    ]

    employee_ids = (
        request.env["hr.employee"]
        .sudo()
        .search(
            [
                ("id", "in", employee_ids_header),
                ("third_party_employee_id", "=", user.id),
            ]
        )
    ).ids
    if not employee_ids:
        return json_response("No employees found", "NotFound", 404)
    return {"user": user, "employee_ids": employee_ids}
