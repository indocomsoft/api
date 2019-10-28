import pytest
from passlib.hash import plaintext
from sqlalchemy.orm.exc import NoResultFound

from src.config import APP_CONFIG
from src.database import User, session_scope
from src.exceptions import ResourceNotFoundException, UnauthorizedException
from src.services import UserService
from tests.fixtures import attributes_for_user, create_user
from tests.utils import assert_dict_in

user_service = UserService(config=APP_CONFIG, hasher=plaintext)


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
    user_params = create_user()

    user = user_service.authenticate(
        email=user_params["email"], password=user_params["hashed_password"]
    )
    assert user_params == user


def test_invite_to_be_seller__unauthorized():
    inviter_id = create_user("1", is_committee=False)["id"]
    invited_id = create_user("2")["id"]

    with pytest.raises(UnauthorizedException):
        user_service.invite_to_be_seller(inviter_id=inviter_id, invited_id=invited_id)


def test_invite_to_be_seller__authorized():
    inviter_id = create_user("1", is_committee=True)["id"]
    invited_id = create_user("2")["id"]

    user_service.invite_to_be_seller(inviter_id=inviter_id, invited_id=invited_id)

    with session_scope() as session:
        assert session.query(User).get(invited_id).can_sell


def test_invite_to_be_buyer__unauthorized():
    inviter_id = create_user("1", is_committee=False)["id"]
    invited_id = create_user("2")["id"]

    with pytest.raises(UnauthorizedException):
        user_service.invite_to_be_buyer(inviter_id=inviter_id, invited_id=invited_id)


def test_invite_to_be_buyer__authorized():
    inviter_id = create_user("1", is_committee=True)["id"]
    invited_id = create_user("2")["id"]

    user_service.invite_to_be_buyer(inviter_id=inviter_id, invited_id=invited_id)

    with session_scope() as session:
        assert session.query(User).get(invited_id).can_buy


def test_get_user():
    user_params = create_user()

    user_id = user_service.authenticate(
        email=user_params["email"], password=user_params["hashed_password"]
    )["id"]

    user = user_service.get_user(id=user_id)

    user_params.pop("hashed_password")
    assert user_params == user

    with pytest.raises(ResourceNotFoundException):
        user_service.get_user(id="00000000-0000-0000-0000-000000000000")
