import logging

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
logger = logging.getLogger(__name__)

PROBLEM_JSON = "application/problem+json"


class ProblemError(Exception):
    """Lỗi nghiệp vụ, được chuyển thành problem+json."""

    def __init__(self, status, title, detail=None,
                 type_="about:blank", **extra):
        super().__init__(title)
        self.status = status
        self.title = title
        self.detail = detail
        self.type = type_
        self.extra = extra  # extension members (tuỳ chọn)


def problem_response(status, title, detail=None,
                     type_="about:blank", extra=None, headers=None):
    body = {
        "type": type_,
        "title": title,
        "detail": detail,
        "status": status,
        "instance": request.path,
    }
    if extra:
        body.update(extra)

    resp = jsonify(body)
    resp.status_code = status
    resp.mimetype = PROBLEM_JSON
    for key, value in (headers or []):
        if key.lower() not in ("content-type", "content-length"):
            resp.headers[key] = value  # giữ lại Allow, Retry-After, ...
    return resp


@app.errorhandler(ProblemError)
def handle_problem_error(err):
    return problem_response(err.status, err.title, err.detail,
                            err.type, err.extra)


@app.errorhandler(HTTPException)
def handle_http_exception(err):
    # Fallback cho 404 (route không tồn tại), 405, 400, ...
    return problem_response(
        err.code or 500,
        err.name,
        err.description,
        headers=err.get_headers(),
        )


@app.errorhandler(Exception)
def handle_unexpected(err):
    # Log chi tiết (kèm stack trace) phía server, KHÔNG trả ra client
    logger.exception("Unhandled exception at %s %s",
                     request.method, request.path)
    return problem_response(
        500,
        "Internal Server Error",
        "An unexpected error occurred. Please try again later.",
    )


RESOURCES = {1: {"id": 1, "name": "first"}}


@app.get("/resources/<int:resource_id>")
def get_resource(resource_id):
    resource = RESOURCES.get(resource_id)
    if resource is None:
        raise ProblemError(
            404,
            "Resource Not Found",
            f"Resource with id {resource_id} does not exist.",
            type_="https://example.com/problems/resource-not-found",
        )
    return jsonify(resource)


@app.get("/boom")
def boom():
    raise RuntimeError("secret internal detail")  #500


if __name__ == "__main__":
    app.run(debug=False)