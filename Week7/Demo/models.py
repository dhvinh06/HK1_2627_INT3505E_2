# models.py
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)