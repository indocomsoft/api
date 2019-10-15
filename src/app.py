import traceback

from sanic import Sanic
from sanic.exceptions import SanicException
from sanic.response import json
from sanic_cors.extension import CORS as initialize_cors
from sanic_jwt import Initialize as initialize_jwt
from sanic_jwt import Responses

from src.api import blueprint, user_login
from src.config import APP_CONFIG
from src.exceptions import AcquityException
from src.services import (
    BuyOrderService,
    LinkedinService,
    RoundService,
    SecurityService,
    SellOrderService,
    UserService,
)

app = Sanic(load_env=False)
app.config.update(APP_CONFIG)

app.user_service = UserService(app.config)
app.linkedin_service = LinkedinService(app.config)
app.sell_order_service = SellOrderService(app.config)
app.buy_order_service = BuyOrderService(app.config)
app.security_service = SecurityService(app.config)
app.round_service = RoundService(app.config)

initialize_cors(app)


class AcquityJwtResponses(Responses):
    @staticmethod
    def exception_response(request, exception):
        if exception.args[0] == "Auth required.":
            # Let's throw 404 Not Found instead
            return json(
                {"error": [f"Requested URL {request.path} not found"]}, status=404
            )

        reasons = (
            exception.args[0]
            if isinstance(exception.args[0], list)
            else [exception.args[0]]
        )
        return json({"error": reasons}, status=exception.status_code)


async def retrieve_user(request, payload, *args, **kwargs):
    if payload is not None:
        return request.app.user_service.get_user(id=payload.get("id"))
    else:
        return None


initialize_jwt(
    blueprint,
    app=app,
    authenticate=user_login,
    responses_class=AcquityJwtResponses,
    retrieve_user=retrieve_user,
)

app.blueprint(blueprint)


async def error_handler(request, exception):
    if isinstance(exception, AcquityException):
        return json({"error": exception.message}, status=exception.status_code)
    elif isinstance(exception, SanicException):
        return json({"error": exception.args}, status=exception.status_code)
    traceback.print_exc()
    return json({"error": "An internal error occured."}, status=500)


app.error_handler.add(Exception, error_handler)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["PORT"])
