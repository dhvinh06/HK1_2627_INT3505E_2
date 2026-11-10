from sqlalchemy import event

from product_api.extensions import db

OK = {"sku": "ABC-1", "name": "Phone", "price_cents": 1000, "qty_in_stock": 5}


def make(client, sku="ABC-1", **kw):
    return client.post("/api/v1/products", json={**OK, "sku": sku, **kw})


# ---------- POST ----------
def test_create_201(client):
    r = make(client)
    assert r.status_code == 201
    assert r.json["sku"] == "ABC-1" and r.json["archived"] is False


def test_create_duplicate_sku_409(client):
    make(client)
    r = make(client)
    assert r.status_code == 409
    assert r.json["error"] == "conflict"


def test_create_invalid_422(client):
    r = client.post("/api/v1/products", json={"sku": "AB", "price_cents": -5})
    assert r.status_code == 422
    assert r.json["error"] == "validation_error"


# ---------- GET / list / paging ----------
def test_get_404(client):
    r = client.get("/api/v1/products/9999")
    assert r.status_code == 404 and r.json["error"] == "not_found"


def test_list_paging_and_total(client):
    for i in range(5):
        make(client, sku=f"SKU-{i}")
    r = client.get("/api/v1/products?page=2&size=2")
    assert r.status_code == 200
    assert r.json["page"] == 2 and r.json["size"] == 2 and r.json["total"] == 5
    assert len(r.json["items"]) == 2


# ---------- PATCH / DELETE ----------
def test_patch_only_changes_given_fields(client):
    pid = make(client).json["id"]
    r = client.patch(f"/api/v1/products/{pid}", json={"name": "New"})
    assert r.status_code == 200
    assert r.json["name"] == "New" and r.json["price_cents"] == 1000


def test_soft_delete_hides_product(client):
    pid = make(client).json["id"]
    assert client.delete(f"/api/v1/products/{pid}").status_code == 204
    assert client.get(f"/api/v1/products/{pid}").status_code == 404
    assert client.get("/api/v1/products").json["total"] == 0


# ---------- reserve ----------
def test_reserve_decreases_stock(client):
    pid = make(client).json["id"]
    r = client.post(f"/api/v1/products/{pid}/reserve", json={"qty": 2})
    assert r.status_code == 200 and r.json["qty_in_stock"] == 3


def test_reserve_out_of_stock_409(client):
    pid = make(client).json["id"]
    r = client.post(f"/api/v1/products/{pid}/reserve", json={"qty": 99})
    assert r.status_code == 409 and r.json["error"] == "out_of_stock"
    assert client.get(f"/api/v1/products/{pid}").json["qty_in_stock"] == 5


# ---------- health ----------
def test_health_endpoints(client):
    assert client.get("/healthz").status_code == 200
    r = client.get("/ready")
    assert r.status_code == 200 and r.json["checks"]["db"] == "ok"


# ---------- orders + eager loading (khong N+1) ----------
def test_orders_list_has_constant_query_count(client):
    ids = [make(client, sku=f"P-{i}").json["id"] for i in range(3)]
    for _ in range(4):  # 4 order, moi order 3 item
        r = client.post("/api/v1/orders",
                        json={"items": [{"product_id": i, "qty": 1} for i in ids]})
        assert r.status_code == 201

    queries = []

    def on_exec(conn, cursor, statement, *a):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    engine = db.engine
    event.listen(engine, "before_cursor_execute", on_exec)
    try:
        r = client.get("/api/v1/orders")
    finally:
        event.remove(engine, "before_cursor_execute", on_exec)

    assert r.status_code == 200 and r.json["total"] == 4
    assert r.json["items"][0]["items"][0]["product_name"] == "Phone"
    # orders + items + products + count = 4, KHONG phu thuoc so order
    assert len(queries) <= 4, f"N+1 detected: {len(queries)} queries"


def test_order_with_missing_product_404(client):
    r = client.post("/api/v1/orders", json={"items": [{"product_id": 999, "qty": 1}]})
    assert r.status_code == 404
