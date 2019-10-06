import traceback

from sanic import Blueprint, Sanic
from sanic.exceptions import SanicException
from sanic.response import json
from sanic_cors.extension import CORS as initialize_cors
from sanic_jwt import Initialize as initialize_jwt
from sanic_jwt import Responses

from api import blueprint, seller_login
from config import APP_CONFIG
from services import SellerService

app = Sanic(load_env=False)
app.config.update(APP_CONFIG)

initialize_cors(app)


class AcquityJwtResponses(Responses):
    @staticmethod
    def exception_response(request, exception):
        reasons = (
            exception.args[0]
            if isinstance(exception.args[0], list)
            else [exception.args[0]]
        )
        return json({"error": reasons}, status=exception.status_code)


initialize_jwt(
    blueprint, app=app, authenticate=seller_login, responses_class=AcquityJwtResponses
)

app.blueprint(blueprint)

app.seller_service = SellerService()


async def error_handler(request, exception):
    if isinstance(exception, SanicException):
        return json({"error": exception.message}, status=exception.status_code)
    traceback.print_exc()
    return json({"error": "An internal error occured."}, status=500)


app.error_handler.add(Exception, error_handler)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["PORT"])
