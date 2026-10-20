from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, relationship

db = SQLAlchemy()


class Category(db.Model):
    __tablename__ = "categories"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    slug = mapped_column(String(100), unique=True, nullable=False)


class Book(db.Model):
    __tablename__ = "books"

    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String(200), nullable=False)
    price_vnd = mapped_column(Integer, nullable=False)  # NOT NULL: so sanh tuple khong duoc co NULL
    category_id = mapped_column(ForeignKey("categories.id"))

    category = relationship("Category")

    def to_dict(self):
        return {
            "id": f"book_{self.id}",
            "title": self.title,
            "price": {"amount": self.price_vnd, "currency": "VND"},
            "category": {"id": self.category.id, "slug": self.category.slug}
            if self.category
            else None,
        }
