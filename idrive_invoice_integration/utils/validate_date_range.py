from datetime import datetime, timedelta
from ..utils.json_response import json_response


def validate_date_range(params):
    date_from = params.get("date_from", "")
    date_to = params.get("date_to", "")
    if not date_from or not date_to:
        return json_response("date_from and date_to are required", "BadRequest", 400)
    try:
        date_from = datetime.strptime(date_from, "%Y/%m/%d").date()
        date_to = datetime.strptime(date_to, "%Y/%m/%d").date()
    except ValueError:
        return json_response("Invalid date format. Use YYYY/MM/DD", "BadRequest", 400)
    if date_from > date_to:
        return json_response(
            "date_from must be before or equal to date_to", "BadRequest", 400
        )
    if date_to - date_from > timedelta(days=31):
        return json_response(
            "date_from and date_to must be within 31 days of each other or less",
            "BadRequest",
            400,
        )
    return {"date_from": date_from, "date_to": date_to}
