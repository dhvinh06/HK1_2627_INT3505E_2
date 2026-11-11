"""LAB 1 — add your five tests here. Do not delete the smoke tests.

A. GET /books, empty database -> HTTP 200 and []
B. GET /books/9999 -> HTTP 404, JSON code == NOT_FOUND
C. POST /books with only author -> HTTP 400, errors contains title
D. POST valid book, DELETE it, GET same id -> HTTP 404
BONUS. Validate a Book response using JSON Schema; add an unknown
       field to a *copy* of the response and assert ValidationError.

Useful imports:

Do not depend on test execution order. Fixtures: client, app, sample_book.
"""
from jsonschema import validate, ValidationError
import pytest
from tools import get_book_schema


def test_get_books_empty(client):
    r = client.get("/books")
    assert r.status_code == 200
    assert r.get_json() == []

def test_get_books_not_found(client):
    r = client.get("/books/9999")
    assert r.status_code == 404
    assert r.get_json()["code"] == "NOT_FOUND"

def test_post_book(client):
    r = client.post("/books",json ={"author":"abc"})
    assert r.status_code == 400
    body = r.get_json()
    fields = {e["field"] for e in body["errors"]}
    assert "title" in fields


def test_delete_then_get_returns_404(client, sample_book):
    r = client.delete(f"/books/{sample_book}")
    assert r.status_code == 204

    r = client.get(f"/books/{sample_book}")
    assert r.status_code == 404
