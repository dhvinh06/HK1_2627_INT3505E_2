import os

from flask import Flask

from .api.health import health_bp
from .api.orders import orders_bp
from .api.products import products_bp
from .config import DefaultConfig
from .errors import register_error_handlers
from .extensions import db, migrate


def create_app(config=None):
    app = Flask(__name__)
    cfg = config or os.environ.get("APP_CONFIG") or DefaultConfig
    app.config.from_object(cfg)  # nhan class hoac chuoi "module.Class"

    db.init_app(app)
    migrate.init_app(app, db)

    from . import models  # noqa: F401  (dang ky model voi db.metadata)

    register_error_handlers(app)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(health_bp)

    @app.cli.command("init-db")
    def init_db():
        """Tao bang neu chua co."""
        db.create_all()
        print("tables ready")

    return app
