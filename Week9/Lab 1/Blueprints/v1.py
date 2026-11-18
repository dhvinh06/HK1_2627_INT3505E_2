from flask import Blueprint
from .users_data import get_user
bp = Blueprint("v1", __name__, url_prefix="/users")


@bp.after_request
def add_sunset_header(response):
    response.headers["Sunset"] = "Fri, 01 Jan 2027 00:00:00 GMT"
    return response

@bp.route("/<int:uid>")
def get(uid):
    u = get_user(uid)
    if not u: return {"error": "nf"}, 404
    return {"id": uid,
            "full_name": f"{u['first_name']} {u['last_name']}",
            "email": u["email"]}
