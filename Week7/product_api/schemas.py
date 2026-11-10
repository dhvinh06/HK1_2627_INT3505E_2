from marshmallow import EXCLUDE, Schema, fields, validate


# ---------- product ----------
class ProductOut(Schema):
    id = fields.Int()
    sku = fields.Str()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    price_cents = fields.Int()
    qty_in_stock = fields.Int()
    archived = fields.Bool()


class ProductIn(Schema):
    sku = fields.Str(required=True, validate=validate.Length(min=3, max=32))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(load_default=None, allow_none=True,
                             validate=validate.Length(max=2000))
    price_cents = fields.Int(required=True, validate=validate.Range(min=0))
    qty_in_stock = fields.Int(load_default=0, validate=validate.Range(min=0))


class ProductPatch(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    price_cents = fields.Int(validate=validate.Range(min=0))
    qty_in_stock = fields.Int(validate=validate.Range(min=0))


class ReserveIn(Schema):
    qty = fields.Int(required=True, validate=validate.Range(min=1))


# ---------- paging ----------
class PageQuery(Schema):
    class Meta:
        unknown = EXCLUDE

    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    size = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))


# ---------- order ----------
class OrderItemIn(Schema):
    product_id = fields.Int(required=True)
    qty = fields.Int(required=True, validate=validate.Range(min=1))


class OrderIn(Schema):
    items = fields.List(fields.Nested(OrderItemIn), required=True,
                        validate=validate.Length(min=1))


class OrderItemOut(Schema):
    id = fields.Int()
    product_id = fields.Int()
    # truy cap item.product.name -> can eager load de tranh N+1
    product_name = fields.Str(attribute="product.name")
    qty = fields.Int()
    unit_price_cents = fields.Int()


class OrderOut(Schema):
    id = fields.Int()
    items = fields.List(fields.Nested(OrderItemOut))
    total_cents = fields.Method("get_total")

    def get_total(self, order):
        return sum(i.qty * i.unit_price_cents for i in order.items)
