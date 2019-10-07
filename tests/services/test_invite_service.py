import datetime

import pytest

from src.database import Invite, Seller, session_scope
from src.exceptions import UnauthorizedException
from src.services import InviteService
from tests.utils import assert_dict_in

invite_service = InviteService()


def test_get_invites():
    with session_scope() as session:
        seller = Seller(email="a@a", hashed_password="123456", full_name="Ben")
        session.add(seller)
        session.commit()

        seller_id = str(seller.id)
        expiry_time = datetime.datetime.now(datetime.timezone.utc)

        invite_b_params = {
            "origin_seller_id": seller_id,
            "destination_email": "b@b",
            "valid": True,
            "expiry_time": expiry_time,
        }
        invite_c_params = {
            "origin_seller_id": seller_id,
            "destination_email": "c@c",
            "valid": False,
            "expiry_time": expiry_time,
        }

        invite = Invite(**invite_b_params)
        invite2 = Invite(**invite_c_params)
        session.add_all([invite, invite2])

    invites = invite_service.get_invites(origin_seller_id=seller_id)
    assert len(invites) == 2

    invite_b = invites[0] if invites[0]["destination_email"] == "b@b" else invites[1]
    assert_dict_in(invite_b_params, invite_b)

    invite_c = invites[1] if invites[0]["destination_email"] == "b@b" else invites[0]
    assert_dict_in(invite_c_params, invite_c)


def test_create_invite():
    with session_scope() as session:
        seller = Seller(email="a@a", hashed_password="123456", full_name="Ben")
        session.add(seller)
        session.commit()

        seller_id = str(seller.id)

    invite_id = invite_service.create_invite(
        origin_seller_id=seller_id, destination_email="b@b"
    )["id"]

    with session_scope() as session:
        invite = session.query(Invite).filter_by(id=invite_id).one().asdict()

    assert_dict_in(
        {"origin_seller_id": seller_id, "destination_email": "b@b", "valid": True},
        invite,
    )
