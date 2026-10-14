
import os
import re
from datetime import datetime

import yaml
from flask import Blueprint, Flask, Response, jsonify, request
from werkzeug.exceptions import HTTPException

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPEC_PATH = os.path.join(BASE_DIR, "openapi.yaml")
API_PREFIX = "/api/v1"

STATUSES = ("open", "done")
PRIORITIES = ("low", "normal", "high")
EDITABLE_FIELDS = ("title", "status", "priority", "dueDate", "assigneeId")

tasks = {}
next_id = 1


def error(status, code, message):
    return jsonify({"error": code, "message": message}), status


# RFC 3339 date-time: needs 'T' and a timezone (Z or +hh:mm).
DATE_TIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:\d{2})$"
)


def is_rfc3339(value):
    if not isinstance(value, str) or not DATE_TIME_RE.match(value):
        return False
    # fromisoformat only accepts 'Z' from Python 3.11, so normalise it first.
    normalized = value[:-1] + "+00:00" if value[-1] in "Zz" else value
    try:
        datetime.fromisoformat(normalized)
    except ValueError:  # e.g. month 13, hour 25
        return False
    return True


def validate_fields(data, partial):
    """Return an error message, or None if valid.

    partial=False -> POST (required fields must be present)
    partial=True  -> PATCH (only validate the fields that were sent)
    """
    if not partial:
        missing = [f for f in ("title", "dueDate", "assigneeId") if f not in data]
        if missing:
            return "Missing required field(s): " + ", ".join(missing) + "."

    if "title" in data:
        if not isinstance(data["title"], str) or not data["title"].strip():
            return "title must be a non-empty string."
    if "status" in data and data["status"] not in STATUSES:
        return "status must be one of: open, done."
    if "priority" in data and data["priority"] not in PRIORITIES:
        return "priority must be one of: low, normal, high."
    if "dueDate" in data and not is_rfc3339(data["dueDate"]):
        return "dueDate must be a valid RFC 3339 date-time format."
    if "assigneeId" in data:
        value = data["assigneeId"]
        if not isinstance(value, int) or isinstance(value, bool):
            return "assigneeId must be an integer."
    return None


def read_json_object():
    """Return the body as a dict, or None if it is not a valid JSON object."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


api = Blueprint("tasks", __name__, url_prefix=API_PREFIX)


@api.before_request
def require_bearer_token():
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return error(401, "UNAUTHORIZED", "Missing or invalid authentication token.")


@api.post("/tasks")
def create_task():
    global next_id
    data = read_json_object()
    if data is None:
        return error(400, "BAD_REQUEST", "Request body must be a valid JSON object.")
    problem = validate_fields(data, partial=False)
    if problem:
        return error(422, "VALIDATION_ERROR", problem)

    task = {
        "id": next_id,
        "title": data["title"],
        "status": data.get("status", "open"),
        "priority": data.get("priority", "normal"),
        "dueDate": data["dueDate"],
        "assigneeId": data["assigneeId"],
    }
    tasks[next_id] = task
    next_id += 1

    response = jsonify(task)
    response.status_code = 201
    response.headers["Location"] = f"{API_PREFIX}/tasks/{task['id']}"
    return response


@api.get("/tasks")
def list_tasks():
    status = request.args.get("status")
    if status is not None and status not in STATUSES:
        return error(400, "BAD_REQUEST", "status must be one of: open, done.")

    try:
        limit = int(request.args.get("limit", "10"))
    except ValueError:
        return error(400, "BAD_REQUEST", "limit must be an integer.")
    if limit < 1:
        return error(400, "BAD_REQUEST", "limit must be at least 1.")

    items = [t for t in tasks.values() if status is None or t["status"] == status]
    return jsonify(items[:limit])


@api.get("/tasks/<int:task_id>")
def get_task(task_id):
    task = tasks.get(task_id)
    if task is None:
        return error(404, "NOT_FOUND", f"Task not found with id {task_id}.")
    return jsonify(task)


@api.patch("/tasks/<int:task_id>")
def patch_task(task_id):
    task = tasks.get(task_id)
    if task is None:
        return error(404, "NOT_FOUND", f"Task not found with id {task_id}.")

    data = read_json_object()
    if data is None:
        return error(400, "BAD_REQUEST", "Request body must be a valid JSON object.")

    # Unknown fields (including "id") are ignored.
    updates = {k: data[k] for k in EDITABLE_FIELDS if k in data}
    if not updates:
        return error(422, "VALIDATION_ERROR", "No updatable fields provided.")
    problem = validate_fields(updates, partial=True)
    if problem:
        return error(422, "VALIDATION_ERROR", problem)

    task.update(updates)
    return jsonify(task)


@api.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    if tasks.pop(task_id, None) is None:
        return error(404, "NOT_FOUND", f"Task not found with id {task_id}.")
    return "", 204



app = Flask(__name__)
app.json.sort_keys = False
app.register_blueprint(api)


@app.errorhandler(Exception)
def handle_any_error(exc):
    if isinstance(exc, HTTPException):  # 404 unknown route, 405, ...
        code = exc.name.upper().replace(" ", "_")
        return error(exc.code, code, exc.description)
    app.logger.exception(exc)
    return error(500, "INTERNAL_SERVER_ERROR", "An unexpected error occurred on the server.")


@app.get("/openapi.json")
def openapi_json():
    with open(SPEC_PATH, encoding="utf-8") as f:
        return jsonify(yaml.safe_load(f))


DOCS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tasks API - Swagger UI (Flask)</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  <style>
    body { margin: 0; background: #fafafa; }
    .swagger-ui .topbar { display: none; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = function () {
      SwaggerUIBundle({
        url: "/openapi.json",
        dom_id: "#swagger-ui",
        deepLinking: true,
        presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
        layout: "BaseLayout"
      });
    };
  </script>
</body>
</html>
"""


@app.get("/docs")
def docs():
    return Response(DOCS_HTML, mimetype="text/html")


if __name__ == "__main__":
    app.run(port=8080, debug=True)