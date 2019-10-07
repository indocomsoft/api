import datetime
from exceptions import UninvitedSellerException

from passlib.hash import argon2

from database import Invite, Seller, SellOrder, session_scope
from schemata import (
    CREATE_INVITE_SCHEMA,
    CREATE_SELL_ORDER_SCHEMA,
    DELETE_SELL_ORDER_SCHEMA,
    EDIT_SELL_ORDER_SCHEMA,
    SELLER_AUTH_SCHEMA,
    UUID_RULE,
    validate_input,
)


class SellerService:
    def __init__(self, Seller=Seller, Invite=Invite, hasher=argon2):
        self.Seller = Seller
        self.Invite = Invite
        self.hasher = hasher

    @validate_input(SELLER_AUTH_SCHEMA)
    def create_account(self, email, password):
        with session_scope() as session:
            if not self.can_create_account(email, session):
                raise UninvitedSellerException(f"Email {email} is uninvited.")

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

    @validate_input({"id": UUID_RULE})
    def get_seller(self, id):
        with session_scope() as session:
            return session.query(self.Seller).filter_by(id=id).one().asdict()

    def can_create_account(self, email, session):
        return (
            session.query(self.Invite)
            .filter(
                self.Invite.destination_email == email,
                self.Invite.valid == True,
                self.Invite.expiry_time >= datetime.datetime.now(),
            )
            .count()
            > 0
        )


class InviteService:
    def __init__(self, Invite=Invite):
        self.Invite = Invite

    @validate_input({"origin_seller_id": UUID_RULE})
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


class SellOrderService:
    def __init__(self, SellOrder=SellOrder):
        self.SellOrder = SellOrder

    @validate_input(CREATE_SELL_ORDER_SCHEMA)
    def create_order(self, seller_id, number_of_shares, price):
        with session_scope() as session:
            sell_order = SellOrder(
                seller_id=seller_id, number_of_shares=number_of_shares, price=price
            )

            session.add(sell_order)
            session.commit()
            return sell_order.asdict()

    @validate_input({"seller_id": UUID_RULE})
    def get_order_by_seller(self, seller_id):
        with session_scope() as session:
            sell_orders = (
                session.query(self.SellOrder).filter_by(seller_id=seller_id).all()
            )
            return [sell_order.asdict() for sell_order in sell_orders]

    @validate_input(EDIT_SELL_ORDER_SCHEMA)
    def edit_order(self, id, subject_id, new_number_of_shares, new_price):
        with session_scope() as session:
            sell_order = session.query(self.SellOrder).filter_by(id=id).one()
            if sell_order.seller_id != subject_id:
                raise UnauthorizedError("You need to own this order.")

            if new_number_of_shares is not None:
                sell_order.number_of_shares = new_number_of_shares
            if new_price is not None:
                sell_order.price = new_price

            session.commit()
            return sell_order.asdict()

    @validate_input(DELETE_SELL_ORDER_SCHEMA)
    def delete_order(self, id, subject_id):
        with session_scope() as session:
            sell_order = session.query(self.SellOrder).filter_by(id=id).one()
            if sell_order.seller_id != subject_id:
                raise UnauthorizedError("You need to own this order.")

            session.delete(sell_order)
        return {}
