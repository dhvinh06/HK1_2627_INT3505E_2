from flask import Flask

from models import db
from routes.books import bp as books_bp


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lab2.db"
    db.init_app(app)
    app.register_blueprint(books_bp, url_prefix="/api/v1/books")
    with app.app_context():
        db.create_all()
    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
