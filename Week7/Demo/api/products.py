from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Product
from schemas import ProductIn, ProductOut

blp = Blueprint("products", __name__, url_prefix="/products",
                description="Product operations")


@blp.route("")
class ProductList(MethodView):

    @blp.response(200, ProductOut(many=True))
    def get(self):
        return db.session.execute(db.select(Product)).scalars().all()

    @blp.arguments(ProductIn)             # validate body, sai thì tự trả 422
    @blp.response(201, ProductOut)        # serialize + set status 201
    def post(self, data):
        p = Product(**data)
        db.session.add(p)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(409, message="sku already exists")
        return p