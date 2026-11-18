from flask import Blueprint
from .users_data import get_user
from .users_data import create_user
bp = Blueprint("v2", __name__, url_prefix="/users")

@bp.route("/<int:uid>")
def get(uid):
    u = get_user(uid)
    if not u: return {"error": "nf"}, 404
    return {"id": uid,
            "first_name": u["first_name"],
            "last_name": u["last_name"],
            "email": u["email"]}

@bp.route("/", methods=["POST"])
def post_user():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not all(
            data.get(k) for k in ("first_name", "last_name", "email")
    ):
        return {"error": "Missing required fields"}, 400

    uid, user = create_user(data)

    return {
        "id": uid,
        **user
    }, 201