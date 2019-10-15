import pytest
from passlib.hash import plaintext
from sqlalchemy.orm.exc import NoResultFound

from src.config import APP_CONFIG
from src.database import User, session_scope
from src.exceptions import UnauthorizedException
from src.services import UserService
from tests.utils import assert_dict_in

user_service = UserService(config=APP_CONFIG, User=User, hasher=plaintext)


def test_create():
    user_service.create(email="a@a", password="123456", full_name="Ben")

    with session_scope() as session:
        users = [u.asdict() for u in session.query(User).all()]

    assert len(users) == 1
    assert_dict_in(
        {
            "email": "a@a",
            "hashed_password": "123456",
            "full_name": "Ben",
            "can_buy": False,
            "can_sell": False,
        },
        users[0],
    )


def test_authenticate():
    user_params = {
        "email": "a@a",
        "hashed_password": "123456",
        "full_name": "Ben",
        "can_buy": False,
        "can_sell": False,
    }
    with session_scope() as session:
        user = User(**user_params)
        session.add(user)

    user = user_service.authenticate(email="a@a", password="123456")
    assert_dict_in(user_params, user)


def test_invite_to_be_seller__unauthorized():
    with session_scope() as session:
        inviter = User(
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
            can_buy=False,
            can_sell=False,
        )
        invited = User(
            email="b@b",
            hashed_password="123456",
            full_name="Ben",
            can_buy=False,
            can_sell=False,
        )
        session.add_all([inviter, invited])
        session.commit()

        inviter_id = str(inviter.id)
        invited_id = str(invited.id)

    with pytest.raises(UnauthorizedException):
        user_service.invite_to_be_seller(inviter_id=inviter_id, invited_id=invited_id)


def test_invite_to_be_seller__authorized():
    with session_scope() as session:
        inviter = User(
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
            can_buy=False,
            can_sell=True,
        )
        invited = User(
            email="b@b",
            hashed_password="123456",
            full_name="Ben",
            can_buy=False,
            can_sell=False,
        )
        session.add_all([inviter, invited])
        session.commit()

        inviter_id = str(inviter.id)
        invited_id = str(invited.id)

    user_service.invite_to_be_seller(inviter_id=inviter_id, invited_id=invited_id)

    with session_scope() as session:
        assert session.query(User).filter_by(id=invited_id).one().can_sell


def test_get_user():
    with session_scope() as session:
        user = User(
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
            can_buy=False,
            can_sell=False,
        )
        session.add(user)

    user_id = user_service.authenticate(email="a@a", password="123456")["id"]

    user = user_service.get_user(id=user_id)
    assert_dict_in(
        {"email": "a@a", "full_name": "Ben", "can_buy": False, "can_sell": False}, user
    )

    with pytest.raises(NoResultFound):
        user_service.get_user(id="00000000-0000-0000-0000-000000000000")
