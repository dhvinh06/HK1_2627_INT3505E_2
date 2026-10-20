from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import mapped_column, relationship

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


class Category(db.Model):
    __tablename__ = "categories"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    slug = mapped_column(String(100), unique=True, nullable=False)

    books = relationship("Book", back_populates="category")


class Author(db.Model):
    __tablename__ = "authors"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    bio = mapped_column(Text)

    book_links = relationship("BookAuthor", back_populates="author")


class User(db.Model):
    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True)
    email = mapped_column(String(255), unique=True, nullable=False)  
    display_name = mapped_column(String(100), nullable=False)


class BookAuthor(db.Model):
    """Junction N:M co metadata (role)."""

    __tablename__ = "book_authors"

    book_id = mapped_column(ForeignKey("books.id"), primary_key=True)
    author_id = mapped_column(ForeignKey("authors.id"), primary_key=True)
    role = mapped_column(String(10), nullable=False, default="co")  # lead | co | ed

    book = relationship("Book", back_populates="author_links")
    author = relationship("Author", back_populates="book_links")


class Book(db.Model):
    __tablename__ = "books"

    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String(200), nullable=False)
    isbn = mapped_column(String(13), unique=True)
    price_vnd = mapped_column(Integer, nullable=False)  # NOT NULL: cursor so sanh tuple se hong neu co NULL
    stock = mapped_column(Integer, nullable=False, default=0)
    category_id = mapped_column(ForeignKey("categories.id"))
    created_at = mapped_column(DateTime, nullable=False, default=utcnow)

    category = relationship("Category", back_populates="books")
    author_links = relationship(
        "BookAuthor", back_populates="book", cascade="all, delete-orphan"
    )
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")

    def to_dict(self):
        c = self.category
        return {
            "id": f"book_{self.id}",
            "title": self.title,
            "isbn": self.isbn,
            "category": {"id": c.id, "slug": c.slug} if c else None,
            "authors": [
                {"id": l.author.id, "name": l.author.name, "role": l.role}
                for l in self.author_links
            ],
            "price": {"amount": self.price_vnd, "currency": "VND"},
            "inStock": self.stock > 0,
            "createdAt": iso(self.created_at),
        }


class Review(db.Model):
    __tablename__ = "reviews"

    id = mapped_column(Integer, primary_key=True)
    rating = mapped_column(Integer, nullable=False)  # 1..5
    comment = mapped_column(Text)
    book_id = mapped_column(ForeignKey("books.id"), nullable=False)
    user_id = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at = mapped_column(DateTime, nullable=False, default=utcnow)

    book = relationship("Book", back_populates="reviews")
    user = relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "rating": self.rating,
            "comment": self.comment,
            "user": {"id": self.user.id, "displayName": self.user.display_name},
            "createdAt": iso(self.created_at),
        }
