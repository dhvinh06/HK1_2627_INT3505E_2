from flask import Blueprint, jsonify
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from ..errors import Conflict, NotFound, OutOfStock
from ..extensions import db
from ..models import Product
from ..schemas import ProductIn, ProductOut, ProductPatch, ReserveIn
from .utils import count, get_json_body, get_page_args

products_bp = Blueprint("products", __name__, url_prefix="/api/v1/products")


def _get_active(id):
    """Lay product chua archived, khong co thi 404."""
    p = db.session.scalar(
        select(Product).where(Product.id == id, Product.archived.is_(False)))
    if p is None:
        raise NotFound(f"product {id} not found")
    return p


# GET /api/v1/products?page=1&size=20
@products_bp.get("")
def list_products():
    page, size = get_page_args()
    rows = db.session.execute(
        select(Product)
        .where(Product.archived.is_(False))
        .order_by(Product.id)
        .offset((page - 1) * size)
        .limit(size)
    ).scalars().all()
    total = count(Product, Product.archived.is_(False))
    return jsonify({
        "items": ProductOut(many=True).dump(rows),
        "page": page, "size": size, "total": total,
    }), 200


# GET /api/v1/products/<id>
@products_bp.get("/<int:id>")
def get_product(id):
    return jsonify(ProductOut().dump(_get_active(id))), 200


# POST /api/v1/products
@products_bp.post("")
def create_product():
    body = ProductIn().load(get_json_body())
    p = Product(**body)
    db.session.add(p)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Conflict("sku already exists")
    return jsonify(ProductOut().dump(p)), 201


# PATCH /api/v1/products/<id>  (chi field co trong body moi doi)
@products_bp.patch("/<int:id>")
def patch_product(id):
    body = ProductPatch().load(get_json_body(), partial=True)
    p = _get_active(id)
    for k, v in body.items():
        setattr(p, k, v)
    db.session.commit()
    return jsonify(ProductOut().dump(p)), 200


# DELETE /api/v1/products/<id>  (soft delete)
@products_bp.delete("/<int:id>")
def delete_product(id):
    p = _get_active(id)
    p.archived = True
    db.session.commit()
    return "", 204


# POST /api/v1/products/<id>/reserve   body: {"qty": 1}
@products_bp.post("/<int:id>/reserve")
def reserve_product(id):
    body = ReserveIn().load(get_json_body())
    qty = body["qty"]
    _get_active(id)  # 404 neu khong ton tai / da archived

    # UPDATE co dieu kien: DB tru kho nguyen tu, khong bi race khi 2 request cung luc
    result = db.session.execute(
        update(Product)
        .where(Product.id == id, Product.qty_in_stock >= qty)
        .values(qty_in_stock=Product.qty_in_stock - qty)
    )
    if result.rowcount == 0:
        db.session.rollback()
        raise OutOfStock("not enough stock")
    db.session.commit()
    return jsonify(ProductOut().dump(db.session.get(Product, id))), 200
