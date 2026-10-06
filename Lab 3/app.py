

import base64
import json
import random
from datetime import datetime, timedelta

from flask import Flask, jsonify, request

app = Flask(__name__)

STATUSES = ("pending", "paid", "shipped", "cancelled")
FIELDS = {"id", "customer_id", "status", "total", "created_at"}
SORTABLE = {"id", "total", "created_at"}
DEFAULT_LIMIT = 10
MAX_LIMIT = 100


def _seed(n=40):
    rnd = random.Random(42)
    base = datetime(2026, 1, 1)
    return [
        {
            "id": i,
            "customer_id": rnd.randint(1, 5),
            "status": rnd.choice(STATUSES),
            "total": rnd.choice([10, 20, 30, 50, 100]),  # cố ý để trùng giá trị
            "created_at": (base + timedelta(hours=i * 7)).isoformat(),
        }
        for i in range(1, n + 1)
    ]


ORDERS = _seed()


class BadRequest(Exception):
    def __init__(self, detail):
        super().__init__(detail)
        self.detail = detail


@app.errorhandler(BadRequest)
def handle_bad_request(err):
    resp = jsonify(
        {
            "type": "about:blank",
            "title": "Bad Request",
            "status": 400,
            "detail": err.detail,
            "instance": request.path,
        }
    )
    resp.status_code = 400
    resp.mimetype = "application/problem+json"
    return resp



def encode_cursor(sort, order):
    name = sort.lstrip("-")
    payload = {"sort": sort, "v": order[name], "id": order["id"]}
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(token, sort):
    try:
        padded = token + "=" * (-len(token) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
        if not isinstance(data, dict) or not {"sort", "v", "id"} <= data.keys():
            raise ValueError
        if not isinstance(data["id"], int) or isinstance(data["id"], bool):
            raise ValueError
    except ValueError:  # gồm cả binascii.Error, UnicodeDecodeError, JSONDecodeError
        raise BadRequest("Invalid cursor.")
    if data["sort"] != sort:
        raise BadRequest("Cursor does not match the requested sort.")
    return data["v"], data["id"]



def parse_int(name, default=None, minimum=None, maximum=None):
    raw = request.args.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise BadRequest(f"'{name}' must be an integer.")
    if minimum is not None and value < minimum:
        raise BadRequest(f"'{name}' must be >= {minimum}.")
    if maximum is not None and value > maximum:
        raise BadRequest(f"'{name}' must be <= {maximum}.")
    return value


def parse_sort():
    sort = request.args.get("sort", "id")  # "total" = tăng dần, "-total" = giảm dần
    if sort.lstrip("-") not in SORTABLE or sort.count("-") > 1 or sort.startswith("--"):
        raise BadRequest(f"'sort' must be one of: {', '.join(sorted(SORTABLE))} "
                         "(prefix '-' for descending).")
    return sort


def parse_fields():
    raw = request.args.get("fields")
    if raw is None:
        return None
    wanted = [f.strip() for f in raw.split(",") if f.strip()]
    unknown = set(wanted) - FIELDS
    if not wanted or unknown:
        raise BadRequest(f"Unknown fields: {sorted(unknown)}. "
                         f"Allowed: {sorted(FIELDS)}.")
    return wanted



@app.get("/orders")
def list_orders():
    limit = parse_int("limit", DEFAULT_LIMIT, minimum=1, maximum=MAX_LIMIT)
    customer_id = parse_int("customer_id")
    status = request.args.get("status")
    if status is not None and status not in STATUSES:
        raise BadRequest(f"'status' must be one of: {', '.join(STATUSES)}.")
    sort = parse_sort()
    fields = parse_fields()
    cursor = request.args.get("cursor")

    items = [
        o for o in ORDERS
        if (status is None or o["status"] == status)
           and (customer_id is None or o["customer_id"] == customer_id)
    ]

    name, desc = sort.lstrip("-"), sort.startswith("-")
    items.sort(key=lambda o: (o[name], o["id"]), reverse=desc)

    if cursor:
        last = decode_cursor(cursor, sort)
        try:
            if desc:
                items = [o for o in items if (o[name], o["id"]) < last]
            else:
                items = [o for o in items if (o[name], o["id"]) > last]
        except TypeError:
            raise BadRequest("Invalid cursor.")

    page = items[: limit + 1]
    has_more = len(page) > limit
    page = page[:limit]
    next_cursor = encode_cursor(sort, page[-1]) if has_more else None

    if fields:
        page = [{k: o[k] for k in fields} for o in page]

    return jsonify({"data": page, "next_cursor": next_cursor, "has_more": has_more})


if __name__ == "__main__":
    app.run(port=5000, debug=False)