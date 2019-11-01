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
    user_service.create_if_not_exists(
        email="a@a.io", display_image_url=None, full_name="Ben", user_id="testing"
    )

    with session_scope() as session:
        user = session.query(User).one()
        user = user.asdict()
        user.pop("created_at")
        user.pop("updated_at")

    assert_dict_in(
        {
            "email": "a@a.io",
            "full_name": "Ben",
            "can_buy": "NO",
            "can_sell": "NO",
            "user_id": "testing",
            "provider": "linkedin",
            "display_image_url": None,
        },
        user,
    )


def test_create_if_user_exist():
    user_service.create_if_not_exists(
        email="a@a.io", display_image_url=None, full_name="Ben", user_id="testing"
    )

    user_service.create_if_not_exists(
        email="a@a.io",
        display_image_url="https://test.png",
        full_name="Ben",
        user_id="testing",
    )

    with session_scope() as session:
        user = session.query(User).one()
        user = user.asdict()
        user.pop("created_at")
        user.pop("updated_at")

    assert_dict_in(
        {
            "email": "a@a.io",
            "full_name": "Ben",
            "can_buy": "NO",
            "can_sell": "NO",
            "user_id": "testing",
            "provider": "linkedin",
            "display_image_url": "https://test.png",
        },
        user,
    )


def test_get_user_by_linkedin_id():
    user_params = create_user()

    user = user_service.get_user_by_linkedin_id(user_id="abcdef")
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

    user_id = user_service.get_user_by_linkedin_id(user_id="abcdef")["id"]

    user = user_service.get_user(id=user_id)

    assert user_params == user

    with pytest.raises(ResourceNotFoundException):
        user_service.get_user(id="00000000-0000-0000-0000-000000000000")
