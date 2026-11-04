from marshmallow import Schema, fields, validate


class ProductIn(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    price_cents = fields.Int(required=True, validate=validate.Range(min=0))


class ProductOut(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    price_cents = fields.Int()
