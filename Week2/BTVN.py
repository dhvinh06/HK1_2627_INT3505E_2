from flask import Flask, jsonify, request, g
import sqlite3

app = Flask(__name__)

DB_PATH = "books.db"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS books (
                                                      id     INTEGER PRIMARY KEY AUTOINCREMENT,
                                                      title  TEXT NOT NULL,
                                                      author TEXT NOT NULL,
                                                      year   INTEGER NOT NULL
                 )
                 """)
    count = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    if count == 0:
        conn.execute(
            "INSERT INTO books (title, author, year) VALUES (?, ?, ?)",
            ("Clean Code", "R. Martin", 2008)
        )
    conn.commit()
    conn.close()


def validate_year(value):
    if value is None:
        return False, "year là bắt buộc"
    if not isinstance(value, int) or isinstance(value, bool):
        return False, "year phải là số nguyên"
    if value < 1900:
        return False, "year phải >= 1900"
    return True, None


# LIST — GET /books
@app.route("/books", methods=["GET"])
def list_books():
    db = get_db()
    q = request.args.get("q", "").strip().lower()
    sort = request.args.get("sort", "").strip()
    limit = int(request.args.get("limit", 100))

    sql = "SELECT * FROM books"
    params = []
    if q:
        sql += " WHERE LOWER(title) LIKE ?"
        params.append(f"%{q}%")

    allowed_fields = {"id", "title", "author", "year"}
    if sort:
        reverse = sort.startswith("-")
        field = sort[1:] if reverse else sort
        if field in allowed_fields:
            sql += f" ORDER BY {field} {'DESC' if reverse else 'ASC'}"

    sql += " LIMIT ?"
    params.append(limit)

    rows = db.execute(sql, params).fetchall()
    return jsonify([dict(r) for r in rows]), 200


# DETAIL — GET /books/<int:id>
@app.route("/books/<int:bid>", methods=["GET"])
def get_book(bid):
    db = get_db()
    row = db.execute("SELECT * FROM books WHERE id = ?", (bid,)).fetchone()
    if row is None:
        return {"error": "not found"}, 404
    return jsonify(dict(row)), 200


# CREATE — POST /books
@app.route("/books", methods=["POST"])
def create_book():
    body = request.get_json(silent=True) or {}
    t, a = body.get("title"), body.get("author")
    year = body.get("year")
    ok, err = validate_year(year)
    if not ok:
        return {"error": err}, 400
    if not t or not a:
        return {"error": "need title+author"}, 400

    db = get_db()
    cur = db.execute(
        "INSERT INTO books (title, author, year) VALUES (?, ?, ?)",
        (t, a, year)
    )
    db.commit()
    new_id = cur.lastrowid
    row = db.execute("SELECT * FROM books WHERE id = ?", (new_id,)).fetchone()
    return jsonify(dict(row)), 201, {"Location": f"/books/{new_id}"}


# UPDATE — PUT, DELETE — DELETE
@app.route("/books/<int:bid>", methods=["PUT", "DELETE"])
def modify_book(bid):
    db = get_db()
    row = db.execute("SELECT * FROM books WHERE id = ?", (bid,)).fetchone()
    if row is None:
        return {"error": "not found"}, 404

    if request.method == "PUT":
        body = request.get_json(silent=True) or {}
        if "year" in body:
            ok, err = validate_year(body["year"])
            if not ok:
                return {"error": err}, 400

        allowed_fields = {"title", "author", "year"}
        updates = {k: v for k, v in body.items() if k in allowed_fields}
        if updates:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            params = list(updates.values()) + [bid]
            db.execute(f"UPDATE books SET {set_clause} WHERE id = ?", params)
            db.commit()

        updated = db.execute("SELECT * FROM books WHERE id = ?", (bid,)).fetchone()
        return jsonify(dict(updated)), 200

    db.execute("DELETE FROM books WHERE id = ?", (bid,))
    db.commit()
    return "", 204


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)