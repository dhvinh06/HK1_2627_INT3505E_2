from flask import Blueprint, jsonify
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..errors import NotFound
from ..extensions import db
from ..models import Order, OrderItem, Product
from ..schemas import OrderIn, OrderOut
from .utils import count, get_json_body, get_page_args

orders_bp = Blueprint("orders", __name__, url_prefix="/api/v1/orders")


def _eager():
    # selectinload: 3 query co dinh (orders, items, products) thay vi 1+N
    return selectinload(Order.items).selectinload(OrderItem.product)


# POST /api/v1/orders   body: {"items": [{"product_id": 1, "qty": 2}]}
@orders_bp.post("")
def create_order():
    body = OrderIn().load(get_json_body())
    ids = {i["product_id"] for i in body["items"]}

    products = {
        p.id: p for p in db.session.execute(
            select(Product).where(Product.id.in_(ids), Product.archived.is_(False))
        ).scalars()
    }
    missing = ids - products.keys()
    if missing:
        raise NotFound(f"products not found: {sorted(missing)}")

    order = Order(items=[
        OrderItem(product_id=i["product_id"], qty=i["qty"],
                  unit_price_cents=products[i["product_id"]].price_cents)
        for i in body["items"]
    ])
    db.session.add(order)
    db.session.commit()

    order = db.session.execute(
        select(Order).options(_eager()).where(Order.id == order.id)).scalar_one()
    return jsonify(OrderOut().dump(order)), 201


# GET /api/v1/orders?page=1&size=20
@orders_bp.get("")
def list_orders():
    page, size = get_page_args()
    rows = db.session.execute(
        select(Order).options(_eager())
        .order_by(Order.id).offset((page - 1) * size).limit(size)
    ).scalars().all()
    return jsonify({
        "items": OrderOut(many=True).dump(rows),
        "page": page, "size": size, "total": count(Order),
    }), 200


# GET /api/v1/orders/<id>
@orders_bp.get("/<int:id>")
def get_order(id):
    order = db.session.execute(
        select(Order).options(_eager()).where(Order.id == id)).scalar_one_or_none()
    if order is None:
        raise NotFound(f"order {id} not found")
    return jsonify(OrderOut().dump(order)), 200
