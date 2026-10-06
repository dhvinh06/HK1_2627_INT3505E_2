import logging

import pytest

from app import app


@pytest.fixture
def client():
    return app.test_client()


FIELDS = {"type", "title", "detail", "status", "instance"}


def test_resource_not_found(client):
    r = client.get("/resources/999")
    assert r.status_code == 404
    assert r.mimetype == "application/problem+json"
    body = r.get_json()
    assert FIELDS <= body.keys()
    assert body["status"] == 404
    assert body["instance"] == "/resources/999"
    assert "Traceback" not in r.get_data(as_text=True)


def test_missing_accept_header(client):
    r = client.get("/resources/999", headers={"Accept": ""})
    assert r.status_code == 404
    assert r.mimetype == "application/problem+json"


def test_accept_json(client):
    r = client.get("/resources/999", headers={"Accept": "application/json"})
    assert r.status_code == 404
    assert r.mimetype == "application/problem+json"


def test_http_exception_fallback(client):
    r = client.get("/no-such-route")
    assert r.status_code == 404
    assert r.mimetype == "application/problem+json"
    assert FIELDS <= r.get_json().keys()


def test_unhandled_exception_returns_500(client, caplog):
    with caplog.at_level(logging.ERROR):
        r = client.get("/boom")
    assert r.status_code == 500
    assert r.mimetype == "application/problem+json"
    text = r.get_data(as_text=True)
    assert "secret internal detail" not in text  # không lộ ra client
    assert "Traceback" not in text
    assert "secret internal detail" in caplog.text  # nhưng có trong log server