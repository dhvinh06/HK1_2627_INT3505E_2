import random

from app import create_app
from models import Book, Category, db

PRICES = [100000, 150000, 200000, 250000, 300000]  # it gia tri -> nhieu sach trung gia


def main():
    random.seed(42)
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        cats = [Category(name=s.title(), slug=s) for s in ("tech", "novel", "science")]
        db.session.add_all(cats)
        db.session.flush()
        for i in range(1, 121):
            db.session.add(
                Book(
                    title=f"Book {i:03d}",
                    price_vnd=random.choice(PRICES),
                    category_id=random.choice(cats).id,
                )
            )
        db.session.commit()
        print("Seeded 120 books, 3 categories")


if __name__ == "__main__":
    main()
