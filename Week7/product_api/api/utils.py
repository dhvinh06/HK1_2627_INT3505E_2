from flask import request

from ..errors import ApiError
from ..extensions import db
from ..schemas import PageQuery
from sqlalchemy import func, select


def get_json_body():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ApiError("body must be a JSON object", code="bad_request", status=400)
    return body


def get_page_args():
    q = PageQuery().load(request.args.to_dict())
    return q["page"], q["size"]


def count(stmt_where_model, *conditions):
    return db.session.scalar(
        select(func.count()).select_from(stmt_where_model).where(*conditions))
