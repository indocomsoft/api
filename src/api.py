from operator import itemgetter

from sanic import Blueprint
from sanic.response import json

from services import SellerService

blueprint = Blueprint("root")


@blueprint.get("/")
async def root(request):
    return json({"hello": "world"})


@blueprint.post("/seller/")
async def create_seller(request):
    email, password = itemgetter("email", "password")(request.json)
    request.app.seller_service.create_account(email, password)
    return json("")


@blueprint.post("/login/seller")
async def seller_login(request):
    email, password = itemgetter("email", "password")(request.json)
    password_is_correct = request.app.seller_service.authenticate(email, password)
    return json(password_is_correct)
