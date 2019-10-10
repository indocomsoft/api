import datetime

import pytest

from src.database import Security, SellOrder, User, session_scope
from src.exceptions import UnauthorizedException
from src.services import SellOrderService
from tests.utils import assert_dict_in

sell_order_service = SellOrderService(SellOrder=SellOrder)


def test_get_orders_by_user():
    with session_scope() as session:
        user = User(
            can_buy=False,
            can_sell=True,
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
        )
        security = Security(name="Grab")
        session.add_all([user, security])
        session.commit()

        user_id = str(user.id)
        security_id = str(security.id)
        sell_order_params = {
            "user_id": user_id,
            "number_of_shares": 20,
            "price": 30,
            "security_id": security_id,
        }
        sell_order_params_2 = {
            "user_id": user_id,
            "number_of_shares": 40,
            "price": 50,
            "security_id": security_id,
        }

        sell_order = SellOrder(**sell_order_params)
        sell_order_2 = SellOrder(**sell_order_params_2)
        session.add_all([sell_order, sell_order_2])

    orders = sell_order_service.get_orders_by_user(user_id=user_id)
    assert len(orders) == 2

    sell_order_20 = orders[0] if orders[0]["number_of_shares"] == 20 else orders[1]
    assert_dict_in(sell_order_params, sell_order_20)

    sell_order_40 = orders[1] if orders[0]["number_of_shares"] == 20 else orders[0]
    assert_dict_in(sell_order_params_2, sell_order_40)


def test_create_order__authorized():
    with session_scope() as session:
        user = User(
            can_buy=False,
            can_sell=True,
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
        )
        security = Security(name="Grab")
        session.add_all([user, security])
        session.commit()

        user_id = str(user.id)
        security_id = str(security.id)

    sell_order_params = {
        "user_id": user_id,
        "number_of_shares": 20,
        "price": 30,
        "security_id": security_id,
    }
    sell_order_id = sell_order_service.create_order(**sell_order_params)["id"]

    with session_scope() as session:
        sell_order = session.query(SellOrder).filter_by(id=sell_order_id).one().asdict()
    assert_dict_in(sell_order_params, sell_order)


def test_create_order__unauthorized():
    with session_scope() as session:
        user = User(
            can_buy=False,
            can_sell=False,
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
        )
        security = Security(name="Grab")
        session.add_all([user, security])
        session.commit()

        user_id = str(user.id)
        security_id = str(security.id)

    with pytest.raises(UnauthorizedException):
        sell_order_service.create_order(
            user_id=user_id, number_of_shares=20, price=30, security_id=security_id
        )


def test_edit_order():
    with session_scope() as session:
        user = User(
            can_buy=False,
            can_sell=True,
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
        )
        security = Security(name="Grab")
        session.add_all([user, security])
        session.commit()

        user_id = str(user.id)
        security_id = str(security.id)
        sell_order_params = {
            "user_id": user_id,
            "number_of_shares": 20,
            "price": 30,
            "security_id": security_id,
        }

        sell_order = SellOrder(**sell_order_params)
        session.add(sell_order)
        session.commit()

        sell_order_id = str(sell_order.id)

    sell_order_service.edit_order(
        id=sell_order_id, subject_id=user_id, new_number_of_shares=50
    )

    with session_scope() as session:
        new_sell_order = (
            session.query(SellOrder).filter_by(id=sell_order_id).one().asdict()
        )

    new_sell_order_params = sell_order_params
    new_sell_order_params["number_of_shares"] = 50
    assert_dict_in(new_sell_order_params, new_sell_order)


def test_delete_order():
    with session_scope() as session:
        user = User(
            can_buy=False,
            can_sell=True,
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
        )
        security = Security(name="Grab")
        session.add_all([user, security])
        session.commit()

        user_id = str(user.id)
        security_id = str(security.id)
        sell_order_params = {
            "user_id": user_id,
            "number_of_shares": 20,
            "price": 30,
            "security_id": security_id,
        }

        sell_order = SellOrder(**sell_order_params)
        session.add(sell_order)
        session.commit()

        sell_order_id = str(sell_order.id)

    sell_order_service.delete_order(id=sell_order_id, subject_id=user_id)

    with session_scope() as session:
        assert session.query(SellOrder).filter_by(id=sell_order_id).count() == 0
