from sanic import Sanic
from sanic_cors.extension import CORS

from api import blueprint
from config import APP_CONFIG
from services import SellerService

app = Sanic(load_env=False)
app.config.update(APP_CONFIG)

app.blueprint(blueprint)
CORS(app)

app.seller_service = SellerService()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["PORT"])
