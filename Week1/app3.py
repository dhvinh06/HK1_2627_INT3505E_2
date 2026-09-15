from flask import Flask, jsonify, request
from uuid import uuid4
app = Flask(__name__)
#kế thừa từ app2
def index():
    return {"message": "Hello, API!"}

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/echo", methods=["POST"])
def echo():
    data = request.get_json(silent=True) or {}
    return jsonify({"you_sent": data}), 200

STUDENTS = []
@app.route("/students", methods=["POST"])
def create_student():
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not name:
        return jsonify({"error":"name là bắt buộc"}), 400
    student = {
        "id": str(uuid4()),
        "name": name,
        "gpa": body.get("gpa", 0.0),
    }
    STUDENTS.append(student)
    return jsonify(student), 201
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)