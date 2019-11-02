import pytest
from passlib.hash import plaintext

from src.config import APP_CONFIG
from src.database import User, UserRequest, session_scope
from src.exceptions import ResourceNotFoundException, UnauthorizedException
from src.services import UserService
from tests.fixtures import attributes_for_user, create_user
from tests.utils import assert_dict_in

user_service = UserService(config=APP_CONFIG, hasher=plaintext)


def test_create__is_buy():
    user_params = {
        "email": "a@a.io",
        "full_name": "Ben",
        "user_id": "testing",
        "display_image_url": "http://blah",
        "is_buy": True,
    }
    user_service.create_if_not_exists(**user_params)

    with session_scope() as session:
        user = session.query(User).one().asdict()
        req = session.query(UserRequest).one().asdict()

    user_expected = user_params
    user_expected.pop("is_buy")
    user_expected.update({"can_buy": "UNAPPROVED", "can_sell": "NO"})
    assert_dict_in(user_expected, user)

    assert_dict_in({"user_id": user["id"], "is_buy": True}, req)


def test_create__is_sell():
    user_params = {
        "email": "a@a.io",
        "full_name": "Ben",
        "user_id": "testing",
        "display_image_url": "http://blah",
        "is_buy": False,
    }
    user_service.create_if_not_exists(**user_params)

    with session_scope() as session:
        user = session.query(User).one().asdict()
        req = session.query(UserRequest).one().asdict()

    user_expected = user_params
    user_expected.pop("is_buy")
    user_expected.update({"can_buy": "NO", "can_sell": "UNAPPROVED"})
    assert_dict_in(user_expected, user)

    assert_dict_in({"user_id": user["id"], "is_buy": False}, req)


def test_create__user_exists():
    user_params = {
        "email": "a@a.io",
        "full_name": "Ben",
        "user_id": "testing",
        "display_image_url": "http://blah",
        "is_buy": True,
    }
    user_service.create_if_not_exists(
        **{
            **user_params,
            "email": "b@b.io",
            "full_name": "Boo",
            "display_image_url": "old",
        }
    )
    user_service.create_if_not_exists(**user_params)

    with session_scope() as session:
        user = session.query(User).one().asdict()

    user_expected = user_params
    user_expected.pop("is_buy")
    user_expected.update({"can_buy": "UNAPPROVED", "can_sell": "NO"})
    assert_dict_in(user_expected, user)


def test_get_user_by_linkedin_id():
    user_params = create_user(user_id="abcdef")

    user = user_service.get_user_by_linkedin_id(user_id="abcdef")
    assert user_params == user


def test_get_user():
    user_params = create_user()

    user_id = user_service.get_user_by_linkedin_id(user_id="abcdef")["id"]

    user = user_service.get_user(id=user_id)

    assert user_params == user

    with pytest.raises(ResourceNotFoundException):
        user_service.get_user(id="00000000-0000-0000-0000-000000000000")
