from sanic import Blueprint, Sanic
from sanic_cors.extension import CORS as initialize_cors
from sanic_jwt import Initialize as initialize_jwt

from api import blueprint, seller_login
from config import APP_CONFIG
from services import SellerService

app = Sanic(load_env=False)
app.config.update(APP_CONFIG)

initialize_cors(app)
initialize_jwt(blueprint, app=app, authenticate=seller_login)

app.blueprint(blueprint)
app.seller_service = SellerService()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["PORT"])
