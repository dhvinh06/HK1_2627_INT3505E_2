import random

from app import create_app
from models import Author, Book, BookAuthor, Category, User, db

PRICES = [100000, 150000, 200000, 250000, 300000]  # it gia tri -> nhieu sach trung gia (test tie-break)


def main():
    random.seed(42)
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        cats = [Category(name=s.title(), slug=s) for s in ("tech", "novel", "science", "history", "business")]
        authors = [Author(name=f"Author {i}", bio=f"Bio of author {i}") for i in range(1, 16)]
        users = [User(email=f"user{i}@example.com", display_name=f"User {i}") for i in range(1, 6)]
        db.session.add_all(cats + authors + users)
        db.session.flush()

        for i in range(1, 201):
            book = Book(
                title=f"Title {random.randint(1, 40):02d}",  # title cung bi trung
                isbn=f"978{i:010d}",
                price_vnd=random.choice(PRICES),
                stock=random.choice([0, 0, 5, 10, 20]),
                category_id=random.choice(cats).id,
            )
            db.session.add(book)
            db.session.flush()
            for n, a in enumerate(random.sample(authors, random.choice([1, 2]))):
                db.session.add(BookAuthor(book_id=book.id, author_id=a.id, role="lead" if n == 0 else "co"))
        db.session.commit()
        print("Seeded 200 books, 15 authors, 5 categories, 5 users")


if __name__ == "__main__":
    main()
