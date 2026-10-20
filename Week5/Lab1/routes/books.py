import base64
import json
from collections import namedtuple
from pathlib import Path

from flask import Blueprint, jsonify, request
from jsonschema import ValidationError, validate
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from models import Author, Book, BookAuthor, Category, Review, User, db

bp = Blueprint("books", __name__)

DEFAULT_LIMIT, MAX_LIMIT = 20, 100
SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
BOOK_INPUT = json.loads((SCHEMA_DIR / "book_input.json").read_text(encoding="utf-8"))

AUTHOR_LINK_INPUT = {
    "type": "object",
    "required": ["authorId"],
    "additionalProperties": False,
    "properties": {
        "authorId": {"type": "integer"},
        "role": {"enum": ["lead", "co", "ed"]},
    },
}
REVIEW_INPUT = {
    "type": "object",
    "required": ["userId", "rating"],
    "additionalProperties": False,
    "properties": {
        "userId": {"type": "integer"},
        "rating": {"type": "integer", "minimum": 1, "maximum": 5},
        "comment": {"type": "string", "maxLength": 2000},
    },
}


# ---------------------------------------------------------------- helpers
class BadRequest(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code, self.message = code, message


def error(code, message, status, **extra):
    return jsonify({"error": code, "message": message, **extra}), status


def read_json(schema):
    """Return (payload, None) hoac (None, response_400)."""
    payload = request.get_json(silent=True)
    try:
        validate(payload, schema)
    except ValidationError as e:
        return None, error("validation_failed", e.message, 400, field=list(e.path))
    return payload, None


def clamp(n, lo, hi):
    return max(lo, min(n, hi))


def parse_book_id(raw):
    if raw.startswith("book_") and raw[5:].isdigit():
        return int(raw[5:])
    return None


def load_book(bid):
    n = parse_book_id(bid)
    return db.session.get(Book, n) if n is not None else None


def book_not_found():
    return error("not_found", "Book not found", 404)


def apply_payload(book, p):
    """Gan payload da validate vao Book. Tra ve response loi hoac None."""
    cat_id = p.get("categoryId")
    if cat_id is not None and db.session.get(Category, cat_id) is None:
        return error("category_not_found", f"Category {cat_id} does not exist", 400)
    book.title = p["title"]
    book.isbn = p.get("isbn")
    book.price_vnd = p["price"]["amount"]
    book.stock = p.get("stock", 0)
    book.category_id = cat_id
    return None


def save(book, status):
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("conflict", "Constraint violated (isbn must be unique)", 409)
    return jsonify(book.to_dict()), status


# ------------------------------------------------- Lab 2: sort / cursor
SORTABLE = {  # whitelist: ten public -> (ten attribute, cot)
    "id": ("id", Book.id),
    "price": ("price_vnd", Book.price_vnd),
    "title": ("title", Book.title),
    "stock": ("stock", Book.stock),
}
SortKey = namedtuple("SortKey", "name attr col desc")


def parse_sort(raw):
    """'-price,title' -> [SortKey(price, desc), SortKey(title, asc), SortKey(id, desc)]"""
    keys, seen = [], set()
    for part in raw.split(","):
        desc = part.startswith("-")
        name = part[1:] if desc else part
        if name not in SORTABLE or name in seen:
            raise BadRequest("bad_sort", f"Invalid sort key: {part!r}")
        seen.add(name)
        attr, col = SORTABLE[name]
        keys.append(SortKey(name, attr, col, desc))
    if len(keys) > 3:
        raise BadRequest("bad_sort", "At most 3 sort keys")
    if "id" not in seen:  # tie-break: id luon la key cuoi cung
        keys.append(SortKey("id", "id", Book.id, keys[0].desc))
    return keys


def canonical_sort(keys):
    return ",".join(("-" if k.desc else "") + k.name for k in keys)


def parse_filters():
    a = request.args
    f = {
        "genre": a.get("genre"),  # = category.slug
        "category": a.get("category", type=int),
        "price_min": a.get("price_min", type=int),
        "price_max": a.get("price_max", type=int),
        "in_stock": None,
    }
    raw = a.get("in_stock")
    if raw is not None:
        if raw not in ("true", "false"):
            raise BadRequest("bad_filter", "in_stock must be 'true' or 'false'")
        f["in_stock"] = raw == "true"
    return {k: v for k, v in f.items() if v is not None}


def apply_filters(stmt, f):
    if "genre" in f:
        stmt = stmt.where(Book.category.has(Category.slug == f["genre"]))
    if "category" in f:
        stmt = stmt.where(Book.category_id == f["category"])
    if "price_min" in f:
        stmt = stmt.where(Book.price_vnd >= f["price_min"])
    if "price_max" in f:
        stmt = stmt.where(Book.price_vnd <= f["price_max"])
    if "in_stock" in f:
        stmt = stmt.where(Book.stock > 0 if f["in_stock"] else Book.stock == 0)
    return stmt


def _enc(obj):
    raw = json.dumps(obj, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _dec(token):
    try:
        pad = "=" * (-len(token) % 4)
        return json.loads(base64.urlsafe_b64decode(token + pad))
    except ValueError:  # base64 / utf-8 / json deu ke thua ValueError
        raise BadRequest("bad_cursor", "Malformed cursor")


def keyset_condition(keys, values):
    """(k1,k2,id) sau (v1,v2,vi) theo tung chieu rieng:
    (k1 ? v1) OR (k1 = v1 AND k2 ? v2) OR (k1 = v1 AND k2 = v2 AND id ? vi)
    Voi 1 key cung chieu, day tuong duong tuple_(col, id) < / > (v, i) cua slide."""
    ors = []
    for i, k in enumerate(keys):
        ands = [keys[j].col == values[j] for j in range(i)]
        ands.append(k.col < values[i] if k.desc else k.col > values[i])
        ors.append(and_(*ands))
    return or_(*ors)


def apply_cursor(stmt, raw, keys, ctx):
    c = _dec(raw)
    if not isinstance(c, dict):
        raise BadRequest("bad_cursor", "Malformed cursor")
    if c.get("ctx") != ctx:  # cursor chi hop le voi dung sort + filter da tao ra no
        raise BadRequest("cursor_mismatch", "Cursor does not match current sort/filter")
    vals = c.get("v")
    if (
        not isinstance(vals, list)
        or len(vals) != len(keys)
        or not all(isinstance(v, (int, str)) for v in vals)
    ):
        raise BadRequest("bad_cursor", "Malformed cursor")
    return stmt.where(keyset_condition(keys, vals))


def build_response(items, pagination):
    return jsonify({"data": [b.to_dict() for b in items], "pagination": pagination})


# Eager-load chong N+1 khi embed category + authors
EAGER = (
    joinedload(Book.category),
    selectinload(Book.author_links).joinedload(BookAuthor.author),
)


def list_offset(stmt, order, lim):
    offset = max(0, request.args.get("offset", 0, type=int))
    total = db.session.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.session.scalars(
        stmt.options(*EAGER).order_by(*order).offset(offset).limit(lim)
    ).all()
    return build_response(
        rows,
        {
            "strategy": "offset",
            "offset": offset,
            "limit": lim,
            "total": total,
            "hasMore": offset + len(rows) < total,
        },
    )


def list_cursor(stmt, order, lim, keys, filters):
    ctx = {"sort": canonical_sort(keys), **filters}
    raw = request.args.get("cursor")
    if raw:
        stmt = apply_cursor(stmt, raw, keys, ctx)
    rows = db.session.scalars(stmt.options(*EAGER).order_by(*order).limit(lim + 1)).all()
    more = len(rows) > lim  # +1 trick
    rows = rows[:lim]
    nxt = None
    if rows and more:
        last = rows[-1]
        nxt = _enc({"ctx": ctx, "v": [getattr(last, k.attr) for k in keys]})
    return build_response(
        rows, {"strategy": "cursor", "limit": lim, "nextCursor": nxt, "hasMore": more}
    )


# ----------------------------------------------------------- books CRUD
@bp.get("", strict_slashes=False)
def list_books():
    try:
        strategy = request.args.get("strategy", "cursor")
        if strategy not in ("cursor", "offset"):
            raise BadRequest("bad_strategy", "strategy must be 'cursor' or 'offset'")
        lim = clamp(request.args.get("limit", DEFAULT_LIMIT, type=int), 1, MAX_LIMIT)
        keys = parse_sort(request.args.get("sort", "-id"))
        filters = parse_filters()
        order = [k.col.desc() if k.desc else k.col.asc() for k in keys]
        stmt = apply_filters(select(Book), filters)
        if strategy == "offset":
            return list_offset(stmt, order, lim)
        return list_cursor(stmt, order, lim, keys, filters)
    except BadRequest as e:
        return error(e.code, e.message, 400)


@bp.post("", strict_slashes=False)
def create_book():
    payload, err = read_json(BOOK_INPUT)
    if err:
        return err
    book = Book()
    err = apply_payload(book, payload)
    if err:
        return err
    db.session.add(book)
    return save(book, 201)


@bp.get("/<bid>")
def get_book(bid):
    book = load_book(bid)
    if book is None:
        return book_not_found()
    return jsonify(book.to_dict())


@bp.put("/<bid>")
def replace_book(bid):
    book = load_book(bid)
    if book is None:
        return book_not_found()
    payload, err = read_json(BOOK_INPUT)
    if err:
        return err
    err = apply_payload(book, payload)
    if err:
        return err
    return save(book, 200)


@bp.delete("/<bid>")
def delete_book(bid):
    book = load_book(bid)
    if book is None:
        return book_not_found()
    db.session.delete(book)  # cascade xoa BookAuthor + Review
    db.session.commit()
    return "", 204


# -------------------------------------------- N:M nested + pair (slide 11)
@bp.post("/<bid>/authors")
def add_author(bid):
    book = load_book(bid)
    if book is None:
        return book_not_found()
    payload, err = read_json(AUTHOR_LINK_INPUT)
    if err:
        return err
    author = db.session.get(Author, payload["authorId"])
    if author is None:
        return error("author_not_found", "Author does not exist", 400)
    if db.session.get(BookAuthor, (book.id, author.id)):
        return error("conflict", "Author already linked to this book", 409)
    link = BookAuthor(book_id=book.id, author_id=author.id, role=payload.get("role", "co"))
    db.session.add(link)
    db.session.commit()
    return jsonify({"id": author.id, "name": author.name, "role": link.role}), 201


@bp.get("/<bid>/authors")
def list_authors(bid):
    book = load_book(bid)
    if book is None:
        return book_not_found()
    rows = db.session.execute(
        select(Author, BookAuthor.role)
        .join(BookAuthor, BookAuthor.author_id == Author.id)
        .where(BookAuthor.book_id == book.id)
    ).all()
    return jsonify({"data": [{"id": a.id, "name": a.name, "role": r} for a, r in rows]})


@bp.delete("/<bid>/authors/<int:aid>")
def remove_author(bid, aid):
    book = load_book(bid)
    if book is None:
        return book_not_found()
    link = db.session.get(BookAuthor, (book.id, aid))
    if link is None:
        return error("not_found", "Author is not linked to this book", 404)
    db.session.delete(link)
    db.session.commit()
    return "", 204


# ------------------------------------------- reviews (strong containment)
@bp.get("/<bid>/reviews")
def list_reviews(bid):
    book = load_book(bid)
    if book is None:
        return book_not_found()
    lim = clamp(request.args.get("limit", DEFAULT_LIMIT, type=int), 1, MAX_LIMIT)
    rows = db.session.scalars(
        select(Review)
        .where(Review.book_id == book.id)
        .options(joinedload(Review.user))
        .order_by(Review.id.desc())
        .limit(lim)
    ).all()
    return jsonify({"data": [r.to_dict() for r in rows]})


@bp.post("/<bid>/reviews")
def create_review(bid):
    book = load_book(bid)
    if book is None:
        return book_not_found()
    payload, err = read_json(REVIEW_INPUT)
    if err:
        return err
    if db.session.get(User, payload["userId"]) is None:
        return error("user_not_found", "User does not exist", 400)
    review = Review(
        book_id=book.id,
        user_id=payload["userId"],
        rating=payload["rating"],
        comment=payload.get("comment"),
    )
    db.session.add(review)
    db.session.commit()
    return jsonify(review.to_dict()), 201
