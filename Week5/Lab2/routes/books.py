import base64
import json

from flask import Blueprint, jsonify, request
from sqlalchemy import select, tuple_

from models import Book, db

bp = Blueprint("books", __name__)

# ---------------------------------------------------------- parse + filter
SORT = {"id": Book.id, "price": Book.price_vnd}  # whitelist, khong bao gio dung raw ten cot


def parse_sort(raw):
    """'-price' -> (cot, [order_by cols], desc). Loi -> (None, code, status)."""
    desc = raw.startswith("-")
    key = raw[1:] if desc else raw
    if key not in SORT:
        return None, "bad_sort", 400
    p = SORT[key]
    cols = [
        p.desc() if desc else p.asc(),
        Book.id.desc() if desc else Book.id.asc(),  # tie-break bang id
    ]
    return p, cols, desc


# ------------------------------------------------------------------ cursor
def _enc(s):
    return base64.urlsafe_b64encode(json.dumps(s).encode()).decode().rstrip("=")


def apply_cursor(q, raw, sort, p, desc):
    """Tra ve (query, error_code, status)."""
    if not raw:
        return q, None, 200
    try:
        pad = "=" * (-len(raw) % 4)
        c = json.loads(base64.urlsafe_b64decode(raw + pad))
        if c.get("s") != sort:
            return None, "sort_chg", 400
        v, i = c["v"], c["i"]
    except (ValueError, KeyError, TypeError, AttributeError):
        return None, "bad_cursor", 400
    # (sort_value, id) < (v, i)  voi desc,  > voi asc
    cur = tuple_(v, i)
    condition = tuple_(p, Book.id) < cur if desc else tuple_(p, Book.id) > cur
    return q.where(condition), None, 200


def build_response(items, lim, sort, p, more):
    nxt = None
    if items and more:
        last = items[-1]
        nxt = _enc({"s": sort, "v": getattr(last, p.key), "i": last.id})
    return jsonify(
        {"data": [b.to_dict() for b in items], "page": {"next": nxt, "more": more}}
    )


# ------------------------------------------------------------------- route
@bp.get("", strict_slashes=False)
def list_books():
    raw = request.args.get("cursor")
    lim = max(1, min(request.args.get("limit", 20, type=int), 100))
    sort = request.args.get("sort", "-id")
    cat = request.args.get("category", type=int)

    p, cols, desc = parse_sort(sort)
    if p is None:
        return jsonify({"error": cols}), 400

    q = select(Book).order_by(*cols)
    if cat:
        q = q.where(Book.category_id == cat)

    q, err, code = apply_cursor(q, raw, sort, p, desc)
    if err:
        return jsonify({"error": err}), code

    rows = db.session.scalars(q.limit(lim + 1)).all()  # +1 trick
    return build_response(rows[:lim], lim, sort, p, len(rows) > lim)
