from flask import Flask, jsonify, request, url_for

app = Flask(__name__)

posts = {}
next_id = 1


def bad(msg, code):
    return jsonify(error=msg), code


def read_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    title, content = data.get("title"), data.get("content")
    if not isinstance(title, str) or not title.strip():
        return None
    if not isinstance(content, str) or not content.strip():
        return None
    return {"title": title.strip(), "content": content.strip()}


@app.get("/api/v1/posts")
def list_posts():
    return jsonify(list(posts.values())), 200


@app.post("/api/v1/posts")
def create_post():
    global next_id
    body = read_body()
    if body is None:
        return bad("title and content must be non-empty strings", 422)
    post = {"id": next_id, **body}
    posts[next_id] = post
    next_id += 1
    return jsonify(post), 201, {"Location": url_for("get_post", post_id=post["id"])}


@app.get("/api/v1/posts/<int:post_id>")
def get_post(post_id):
    post = posts.get(post_id)
    if post is None:
        return bad("post not found", 404)
    return jsonify(post), 200

@app.put("/api/v1/posts/<int:post_id>")
def update_post(post_id):
    if post_id not in posts:
        return bad("post not found", 404)
    body = read_body()
    if body is None:
        return bad("title and content must be non-empty strings", 422)
    posts[post_id].update(body)
    return jsonify(posts[post_id]), 200


@app.delete("/api/v1/posts/<int:post_id>")
def delete_post(post_id):
    if posts.pop(post_id, None) is None:
        return bad("post not found", 404)
    return "", 204


if __name__ == "__main__":
    app.run(debug=True)