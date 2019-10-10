import datetime

from passlib.hash import argon2

from src.database import Security, SellOrder, User, session_scope
from src.exceptions import UnauthorizedException
from src.schemata import (
    CREATE_SELL_ORDER_SCHEMA,
    CREATE_USER_SCHEMA,
    DELETE_SELL_ORDER_SCHEMA,
    EDIT_SELL_ORDER_SCHEMA,
    INVITE_SCHEMA,
    USER_AUTH_SCHEMA,
    UUID_RULE,
    validate_input,
)


class UserService:
    def __init__(self, User=User, hasher=argon2):
        self.User = User
        self.hasher = hasher

    @validate_input(CREATE_USER_SCHEMA)
    def create(self, email, password, full_name):
        with session_scope() as session:
            hashed_password = self.hasher.hash(password)
            user = self.User(
                email=email,
                full_name=full_name,
                hashed_password=hashed_password,
                can_buy=False,
                can_sell=False,
            )
            session.add(user)
            session.commit()

            result = user.asdict()
        result.pop("hashed_password")
        return result

    @validate_input({"user_id": UUID_RULE})
    def activate_buy_privileges(self, user_id):
        with session_scope() as session:
            user = session.query(self.User).filter_by(id=user_id).one()
            user.can_buy = True

        return user.asdict()

    @validate_input(INVITE_SCHEMA)
    def invite_to_be_seller(self, inviter_id, invited_id):
        with session_scope() as session:
            inviter = session.query(self.User).filter_by(id=inviter_id).one()
            if not inviter.can_sell:
                raise UnauthorizedException("Inviter is not a previous seller.")

            invited = session.query(self.User).filter_by(id=invited_id).one()
            invited.can_sell = True

            session.commit()

            result = invited.asdict()
        result.pop("hashed_password")
        return result

    @validate_input(USER_AUTH_SCHEMA)
    def authenticate(self, email, password):
        with session_scope() as session:
            user = session.query(self.User).filter_by(email=email).one()
            if self.hasher.verify(password, user.hashed_password):
                return user.asdict()
            else:
                return None

    @validate_input({"id": UUID_RULE})
    def get_user(self, id):
        with session_scope() as session:
            user = session.query(self.User).filter_by(id=id).one().asdict()
        user.pop("hashed_password")
        return user


class SellOrderService:
    def __init__(self, SellOrder=SellOrder, User=User):
        self.SellOrder = SellOrder
        self.User = User

    @validate_input(CREATE_SELL_ORDER_SCHEMA)
    def create_order(self, user_id, number_of_shares, price, security_id):
        with session_scope() as session:
            user = session.query(self.User).filter_by(id=user_id).one()
            if not user.can_sell:
                raise UnauthorizedException("This user cannot sell securities.")

            sell_order = self.SellOrder(
                user_id=user_id,
                number_of_shares=number_of_shares,
                price=price,
                security_id=security_id,
            )

            session.add(sell_order)
            session.commit()
            return sell_order.asdict()

    @validate_input({"user_id": UUID_RULE})
    def get_orders_by_user(self, user_id):
        with session_scope() as session:
            sell_orders = session.query(self.SellOrder).filter_by(user_id=user_id).all()
            return [sell_order.asdict() for sell_order in sell_orders]

    @validate_input(EDIT_SELL_ORDER_SCHEMA)
    def edit_order(self, id, subject_id, new_number_of_shares=None, new_price=None):
        with session_scope() as session:
            sell_order = session.query(self.SellOrder).filter_by(id=id).one()
            if sell_order.user_id != subject_id:
                raise UnauthorizedException("You need to own this order.")

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
            if sell_order.user_id != subject_id:
                raise UnauthorizedException("You need to own this order.")

            session.delete(sell_order)
        return {}


class SecurityService:
    def __init__(self, Security=Security):
        self.Security = Security

    def get_all(self):
        with session_scope() as session:
            return [sec.asdict() for sec in session.query(self.Security).all()]
