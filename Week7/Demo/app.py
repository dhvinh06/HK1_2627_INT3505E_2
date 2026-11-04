from flask import Flask
from flask_smorest import Api

from extensions import db
from api.products import blp

app = Flask(__name__)

app.config["API_TITLE"] = "Product API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev_cf.db"
db.init_app(app)

api = Api(app)
api.register_blueprint(blp)

with app.app_context():
    import models
    db.create_all()

if __name__ == "__main__":
    app.run(port=5001, debug=True)