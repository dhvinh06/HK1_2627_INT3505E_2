from flask import jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Base: moi loi nghiep vu ke thua class nay."""
    status_code = 500
    code = "internal_error"

    def __init__(self, message="", code=None, status=None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status:
            self.status_code = status


class NotFound(ApiError):
    status_code = 404
    code = "not_found"


class Conflict(ApiError):
    status_code = 409
    code = "conflict"


class OutOfStock(ApiError):
    status_code = 409
    code = "out_of_stock"


def _body(error, detail):
    # Dinh dang theo de bai: {"error": "...", "detail": "..."}
    return jsonify({"error": error, "detail": detail})


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def _on_api(err):
        return _body(err.code, err.message), err.status_code

    @app.errorhandler(ValidationError)
    def _on_validation(err):
        return _body("validation_error", err.messages), 422

    @app.errorhandler(HTTPException)
    def _on_http(err):
        return _body(err.name.lower().replace(" ", "_"), err.description), err.code

    @app.errorhandler(Exception)
    def _on_unhandled(err):
        app.logger.exception("unhandled")
        return _body("internal_error", "unexpected server error"), 500
