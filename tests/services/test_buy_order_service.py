from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from src.config import APP_CONFIG
from src.database import BuyOrder, Round, Security, User, session_scope
from src.exceptions import NoActiveRoundException, UnauthorizedException
from src.services import BuyOrderService
from tests.utils import assert_dict_in

buy_order_service = BuyOrderService(config=APP_CONFIG, BuyOrder=BuyOrder, User=User)


def test_get_orders_by_user():
    with session_scope() as session:
        user = User(
            can_sell=False,
            can_buy=True,
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
        )
        security = Security(name="Grab")
        round = Round(end_time=datetime.now(), is_concluded=False)
        session.add_all([user, security, round])
        session.commit()

        user_id = str(user.id)
        security_id = str(security.id)
        round_id = str(round.id)
        buy_order_params = {
            "user_id": user_id,
            "number_of_shares": 20,
            "price": 30,
            "security_id": security_id,
            "round_id": round_id,
        }
        buy_order_params_2 = {
            "user_id": user_id,
            "number_of_shares": 40,
            "price": 50,
            "security_id": security_id,
            "round_id": round_id,
        }

        buy_order = BuyOrder(**buy_order_params)
        buy_order_2 = BuyOrder(**buy_order_params_2)
        session.add_all([buy_order, buy_order_2])

    orders = buy_order_service.get_orders_by_user(user_id=user_id)
    assert len(orders) == 2

    buy_order_20 = orders[0] if orders[0]["number_of_shares"] == 20 else orders[1]
    assert_dict_in(buy_order_params, buy_order_20)

    buy_order_40 = orders[1] if orders[0]["number_of_shares"] == 20 else orders[0]
    assert_dict_in(buy_order_params_2, buy_order_40)


def test_create_order__authorized():
    with session_scope() as session:
        user = User(
            can_sell=False,
            can_buy=True,
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
        )
        security = Security(name="Grab")
        round = Round(end_time=datetime.now(), is_concluded=False)
        session.add_all([user, security, round])
        session.commit()

        round_dict = round.asdict()
        user_id = str(user.id)
        security_id = str(security.id)
        round_id = str(round.id)

    buy_order_params = {
        "user_id": user_id,
        "number_of_shares": 20,
        "price": 30,
        "security_id": security_id,
    }

    with patch("src.services.RoundService.get_active", return_value=round_dict):
        buy_order_id = buy_order_service.create_order(**buy_order_params)["id"]

    with session_scope() as session:
        buy_order = session.query(BuyOrder).get(buy_order_id).asdict()

    buy_order_params["round_id"] = round_id
    assert_dict_in(buy_order_params, buy_order)


def test_create_order__authorized_no_active_rounds():
    with session_scope() as session:
        user = User(
            can_sell=False,
            can_buy=True,
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
        )
        security = Security(name="Grab")
        session.add_all([user, security])
        session.commit()

        user_id = str(user.id)
        security_id = str(security.id)

    buy_order_params = {
        "user_id": user_id,
        "number_of_shares": 20,
        "price": 30,
        "security_id": security_id,
    }

    with patch(
        "src.services.RoundService.get_active", return_value=None
    ), pytest.raises(NoActiveRoundException):
        buy_order_id = buy_order_service.create_order(**buy_order_params)["id"]


def test_create_order__unauthorized():
    with session_scope() as session:
        user = User(
            can_sell=False,
            can_buy=False,
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
        )
        security = Security(name="Grab")
        round = Round(end_time=datetime.now() + timedelta(weeks=1), is_concluded=False)
        session.add_all([user, security, round])
        session.commit()

        user_id = str(user.id)
        security_id = str(security.id)

    with pytest.raises(UnauthorizedException):
        buy_order_service.create_order(
            user_id=user_id, number_of_shares=20, price=30, security_id=security_id
        )


def test_edit_order():
    with session_scope() as session:
        user = User(
            can_sell=False,
            can_buy=True,
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
        )
        security = Security(name="Grab")
        round = Round(end_time=datetime.now(), is_concluded=False)
        session.add_all([user, security, round])
        session.commit()

        user_id = str(user.id)
        security_id = str(security.id)
        round_id = str(round.id)
        buy_order_params = {
            "user_id": user_id,
            "number_of_shares": 20,
            "price": 30,
            "security_id": security_id,
            "round_id": round_id,
        }

        buy_order = BuyOrder(**buy_order_params)
        session.add(buy_order)
        session.commit()

        buy_order_id = str(buy_order.id)

    buy_order_service.edit_order(
        id=buy_order_id, subject_id=user_id, new_number_of_shares=50
    )

    with session_scope() as session:
        new_buy_order = session.query(BuyOrder).get(buy_order_id).asdict()

    assert_dict_in({**buy_order_params, "number_of_shares": 50}, new_buy_order)


def test_delete_order():
    with session_scope() as session:
        user = User(
            can_sell=False,
            can_buy=True,
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
        )
        security = Security(name="Grab")
        round = Round(end_time=datetime.now(), is_concluded=False)
        session.add_all([user, security, round])
        session.commit()

        user_id = str(user.id)
        security_id = str(security.id)
        round_id = str(round.id)
        buy_order_params = {
            "user_id": user_id,
            "number_of_shares": 20,
            "price": 30,
            "security_id": security_id,
            "round_id": round_id,
        }

        buy_order = BuyOrder(**buy_order_params)
        session.add(buy_order)
        session.commit()

        buy_order_id = str(buy_order.id)

    buy_order_service.delete_order(id=buy_order_id, subject_id=user_id)

    with session_scope() as session:
        assert session.query(BuyOrder).filter_by(id=buy_order_id).count() == 0
