from flask import Flask, jsonify, request, url_for
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

posts, next_id = {}, 1

MSG = "title and content must be non-empty strings"


class ProblemError(Exception):
    def __init__(self, title, detail, status):
        self.title = title
        self.detail = detail
        self.status = status
        super().__init__(detail)


@app.errorhandler(ProblemError)
def handle_problem_error(e):
    response = jsonify(
        type="about:blank",
        title=e.title,
        detail=e.detail,
        status=e.status
    )
    response.status_code = e.status
    response.content_type = "application/problem+json"
    return response


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    response = jsonify(
        type="about:blank",
        title=e.name,
        detail=e.description,
        status=e.code
    )
    response.status_code = e.code
    response.content_type = "application/problem+json"
    return response


@app.errorhandler(Exception)
def handle_exception(e):
    # Chi tiết exception chỉ log ở server
    app.logger.exception("Unhandled exception")

    response = jsonify(
        type="about:blank",
        title="Internal Server Error",
        detail="An unexpected error occurred",
        status=500
    )
    response.status_code = 500
    response.content_type = "application/problem+json"
    return response


def read_body():
    d = request.get_json(silent=True)

    if not isinstance(d, dict):
        return None

    t, c = d.get("title"), d.get("content")

    if all(isinstance(x, str) and x.strip() for x in (t, c)):
        return {
            "title": t.strip(),
            "content": c.strip()
        }

    return None

@app.get("/api/v1/posts")
def list_posts():
    return jsonify(list(posts.values()))


@app.post("/api/v1/posts")
def create_post():
    global next_id

    body = read_body()

    if not body:
        raise ProblemError(
            "Invalid request",
            MSG,
            422
        )

    post = posts[next_id] = {
        "id": next_id,
        **body
    }

    next_id += 1

    return jsonify(post), 201, {
        "Location": url_for(
            "get_post",
            post_id=post["id"]
        )
    }

@app.get("/api/v1/posts/<int:post_id>")
def get_post(post_id):
    if post_id not in posts:
        raise ProblemError(
            "Post not found",
            "The requested post does not exist",
            404
        )

    return jsonify(posts[post_id])


@app.put("/api/v1/posts/<int:post_id>")
def update_post(post_id):
    if post_id not in posts:
        raise ProblemError(
            "Post not found",
            "The requested post does not exist",
            404
        )

    body = read_body()

    if not body:
        raise ProblemError(
            "Invalid request",
            MSG,
            422
        )

    posts[post_id].update(body)

    return jsonify(posts[post_id])


@app.delete("/api/v1/posts/<int:post_id>")
def delete_post(post_id):
    if posts.pop(post_id, None) is None:
        raise ProblemError(
            "Post not found",
            "The requested post does not exist",
            404
        )

    return "", 204


if __name__ == "__main__":
    app.run(debug=True)