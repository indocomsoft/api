import datetime

from passlib.hash import argon2

from database import Invite, Seller, session_scope
from schemata import (
    CREATE_INVITE_SCHEMA,
    SELLER_AUTH_SCHEMA,
    generate_id_schema,
    validate_input,
)


class SellerService:
    def __init__(self, Seller=Seller, hasher=argon2):
        self.Seller = Seller
        self.hasher = hasher

    @validate_input(SELLER_AUTH_SCHEMA)
    def create_account(self, email, password):
        with session_scope() as session:
            hashed_password = self.hasher.hash(password)
            seller = self.Seller(email=email, hashed_password=hashed_password)
            session.add(seller)

    @validate_input(SELLER_AUTH_SCHEMA)
    def authenticate(self, email, password):
        with session_scope() as session:
            seller = session.query(self.Seller).filter_by(email=email).one()
            if self.hasher.verify(password, seller.hashed_password):
                return seller.asdict()
            else:
                return None

    @validate_input(generate_id_schema("id"))
    def get_seller(self, id):
        with session_scope() as session:
            return session.query(self.Seller).filter_by(id=id).one().asdict()


class InviteService:
    def __init__(self, Invite=Invite):
        self.Invite = Invite

    @validate_input(generate_id_schema("origin_seller_id"))
    def get_invites(self, origin_seller_id):
        with session_scope() as session:
            invites = (
                session.query(self.Invite)
                .filter_by(origin_seller_id=origin_seller_id)
                .all()
            )
            return [invite.asdict() for invite in invites]

    @validate_input(CREATE_INVITE_SCHEMA)
    def create_invite(self, origin_seller_id, destination_email):
        with session_scope() as session:
            invite = self.Invite(
                origin_seller_id=origin_seller_id,
                destination_email=destination_email,
                valid=True,
                expiry_time=datetime.datetime.now() + datetime.timedelta(weeks=1),
            )
            session.add(invite)
            session.commit()
            return invite.asdict()
