from unittest.mock import patch

import pytest

from src.config import APP_CONFIG
from src.database import Security, SellOrder, User, session_scope
from src.exceptions import UnauthorizedException
from src.services import SellOrderService
from tests.fixtures import create_security, create_sell_order, create_user
from tests.utils import assert_dict_in

sell_order_service = SellOrderService(config=APP_CONFIG, SellOrder=SellOrder)


def test_get_orders_by_user():
    user_id = create_user()["id"]
    sell_order = create_sell_order("1", user_id=user_id)
    sell_order2 = create_sell_order("2", user_id=user_id)

    orders = sell_order_service.get_orders_by_user(user_id=user_id)
    assert len(orders) == 2

    assert (
        sell_order == orders[0]
        if orders[0]["number_of_shares"] == sell_order["number_of_shares"]
        else orders[1]
    )

    assert (
        sell_order2 == orders[1]
        if orders[0]["number_of_shares"] == sell_order["number_of_shares"]
        else orders[0]
    )


def test_create_order__authorized():
    user_id = create_user()["id"]
    security_id = create_security()["id"]

    sell_order_params = {
        "user_id": user_id,
        "number_of_shares": 20,
        "price": 30,
        "security_id": security_id,
    }

    with patch("src.services.RoundService.get_active", return_value=None), patch(
        "src.services.RoundService.should_round_start", return_value=False
    ):
        sell_order_id = sell_order_service.create_order(**sell_order_params)["id"]

    with session_scope() as session:
        sell_order = session.query(SellOrder).get(sell_order_id).asdict()

    assert_dict_in({**sell_order_params, "round_id": None}, sell_order)


def test_create_order__add_new_round():
    user_id = create_user()["id"]
    security_id = create_security()["id"]

    sell_order_params = {
        "user_id": user_id,
        "number_of_shares": 20,
        "price": 30,
        "security_id": security_id,
    }

    with patch("src.services.RoundService.get_active", return_value=None), patch(
        "src.services.RoundService.should_round_start", return_value=False
    ):
        sell_order_id = sell_order_service.create_order(**sell_order_params)["id"]
    with patch("src.services.RoundService.get_active", return_value=None), patch(
        "src.services.RoundService.should_round_start", return_value=True
    ):
        sell_order_id2 = sell_order_service.create_order(**sell_order_params)["id"]

    with session_scope() as session:
        sell_order = session.query(SellOrder).get(sell_order_id).asdict()
        sell_order2 = session.query(SellOrder).get(sell_order_id2).asdict()

    assert_dict_in(sell_order_params, sell_order)
    assert sell_order["round_id"] is not None
    assert_dict_in(sell_order_params, sell_order2)
    assert sell_order["round_id"] is not None


def test_create_order__unauthorized():
    user_id = create_user(can_sell=False)["id"]
    security_id = create_security()["id"]

    with pytest.raises(UnauthorizedException):
        sell_order_service.create_order(
            user_id=user_id, number_of_shares=20, price=30, security_id=security_id
        )


def test_edit_order():
    user_id = create_user()["id"]
    sell_order = create_sell_order(user_id=user_id)

    sell_order_service.edit_order(
        id=sell_order["id"], subject_id=user_id, new_number_of_shares=50
    )

    with session_scope() as session:
        new_sell_order = session.query(SellOrder).get(sell_order["id"]).asdict()

    test_dict = {**sell_order, "number_of_shares": 50}
    del test_dict["updated_at"]
    assert_dict_in(test_dict, new_sell_order)


def test_delete_order():
    user_id = create_user()["id"]
    sell_order_id = create_sell_order(user_id=user_id)["id"]

    sell_order_service.delete_order(id=sell_order_id, subject_id=user_id)

    with session_scope() as session:
        assert session.query(SellOrder).filter_by(id=sell_order_id).count() == 0
