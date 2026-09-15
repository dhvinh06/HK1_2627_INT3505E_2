from flask import Flask, jsonify, request
app = Flask(__name__)
_next = 2
BOOKS = [{"id":1,"title":"Clean Code","author":"R. Martin"}]
def find(bid):
    return next((b for b in BOOKS if b["id"]==bid), None)
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
    items = BOOKS
    q = request.args.get("q", "").strip().lower()
    if q:
        items = [b for b in items if q in b["title"].lower()]

    sort = request.args.get("sort", "").strip()
    if sort:
        reverse = sort.startswith("-")
        field = sort[1:] if reverse else sort
        items = sorted(items, key=lambda b: b.get(field), reverse=reverse)
    n = int(request.args.get("limit", 100))
    return jsonify(items[:n]), 200

# DETAIL — GET /books/<int:id>
@app.route("/books/<int:bid>", methods=["GET"])
def get_book(bid):
        book = find(bid)
        if not book: return {"error":"not found"}, 404
        return jsonify(book), 200
# CREATE — POST /books
@app.route("/books", methods=["POST"])
def create_book():
    global _next
    body = request.get_json(silent=True) or {}
    t, a = body.get("title"), body.get("author")
    year = body.get("year")
    ok, err = validate_year(year)
    if not ok:
        return {"error": err}, 400
    if not t or not a:
        return {"error":"need title+author"}, 400
    book = {"id":_next, "title":t, "author":a,"year":year}
    _next += 1; BOOKS.append(book)
    return jsonify(book), 201, {"Location":f"/books/{book['id']}"}
# UPDATE — PUT, DELETE — DELETE (xem bên phải)
@app.route("/books/<int:bid>", methods=["PUT", "DELETE"])
def modify_book(bid):
    book = find(bid)
    if not book: return {"error":"not found"}, 404
    if request.method == "PUT":
        body = request.get_json(silent=True) or {}
        if "year" in body:
            ok, err = validate_year(body["year"])
            if not ok:
                return {"error": err}, 400
        book.update(body)
        return jsonify(book), 200
    BOOKS.remove(book)
    return"", 204


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)