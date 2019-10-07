from sanic import Blueprint
from sanic.response import json
from sanic_jwt.decorators import inject_user, protected
from sanic_jwt.exceptions import AuthenticationFailed

from services import SellerService
from utils import expects_json_object

blueprint = Blueprint("root", version="v1")


def auth_required(func):
    return (inject_user(blueprint))(protected(blueprint)(func))


@blueprint.get("/")
async def root(request):
    return json({"hello": "world"})


@blueprint.post("/seller/")
@expects_json_object
async def create_seller(request):
    request.app.seller_service.create_account(**request.json)
    return json({})


@expects_json_object
async def seller_login(request):
    seller = request.app.seller_service.authenticate(**request.json)
    if seller is None:
        raise AuthenticationFailed()
    return {"id": seller["id"], "email": seller["email"]}


@blueprint.get("/invite/")
@auth_required
async def get_invites(request, user):
    return json(request.app.invite_service.get_invites(origin_seller_id=user["id"]))


@blueprint.post("/invite/")
@auth_required
@expects_json_object
async def create_invite(request, user):
    return json(
        request.app.invite_service.create_invite(
            **request.json, origin_seller_id=user["id"]
        )
    )


@blueprint.get("/sell_orders/")
@auth_required
async def get_sell_orders_by_seller(request, user):
    return json(
        request.app.sell_order_service.get_order_by_seller(seller_id=user["id"])
    )


@blueprint.post("/sell_orders/")
@auth_required
@expects_json_object
async def create_sell_order(request, user):
    return json(
        request.app.sell_order_service.create_order(
            **request.json, seller_id=user["id"]
        )
    )


@blueprint.patch("/sell_orders/<id>")
@auth_required
@expects_json_object
async def edit_sell_order(request, user, id):
    return json(
        request.app.sell_order_service.edit_order(
            **request.json, id=id, subject_id=user["id"]
        )
    )


@blueprint.delete("/sell_orders/<id>")
@auth_required
async def delete_sell_order(request, user, id):
    return json(
        request.app.sell_order_service.edit_order(
            **request.json, id=id, subject_id=user["id"]
        )
    )
