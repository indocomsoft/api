from datetime import datetime

import requests
from passlib.hash import argon2
from sqlalchemy.sql import func

from src.database import BuyOrder, Round, Security, SellOrder, User, session_scope
from src.exceptions import (
    InvalidRequestException,
    NoActiveRoundException,
    UnauthorizedException,
)
from src.schemata import (
    CREATE_ORDER_SCHEMA,
    CREATE_USER_SCHEMA,
    DELETE_ORDER_SCHEMA,
    EDIT_ORDER_SCHEMA,
    EMAIL_RULE,
    INVITE_SCHEMA,
    LINKEDIN_BUYER_PRIVILEGES_SCHEMA,
    LINKEDIN_CODE_SCHEMA,
    LINKEDIN_TOKEN_SCHEMA,
    USER_AUTH_SCHEMA,
    UUID_RULE,
    validate_input,
)


class DefaultService:
    def __init__(self, config):
        self.config = config


class UserService(DefaultService):
    def __init__(self, config, User=User, hasher=argon2):
        super().__init__(config)
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
            session.commit()
            result = user.asdict()
        result.pop("hashed_password")
        return result

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

    @validate_input({"email": EMAIL_RULE})
    def get_user_by_email(self, email):
        with session_scope() as session:
            user = session.query(self.User).filter_by(email=email).one().asdict()
        user.pop("hashed_password")
        return user


class LinkedinService(DefaultService):
    def __init__(self, config):
        super().__init__(config)

    @validate_input(LINKEDIN_BUYER_PRIVILEGES_SCHEMA)
    def activate_buyer_privileges(self, code, redirect_uri, user_email):
        linkedin_email = self._get_user_data(code=code, redirect_uri=redirect_uri)
        if linkedin_email == user_email:
            user = UserService(self.config).get_user_by_email(email=user_email)
            return UserService(self.config).activate_buy_privileges(
                user_id=user.get("id")
            )
        else:
            raise InvalidRequestException("Linkedin email does not match")

    @validate_input(LINKEDIN_CODE_SCHEMA)
    def _get_user_data(self, code, redirect_uri):
        token = self._get_token(code=code, redirect_uri=redirect_uri)
        return self._get_user_email(token=token)

    @validate_input(LINKEDIN_CODE_SCHEMA)
    def _get_token(self, code, redirect_uri):
        token = requests.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            headers={"Content-Type": "x-www-form-urlencoded"},
            params={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.config["CLIENT_ID"],
                "client_secret": self.config["CLIENT_SECRET"],
            },
        ).json()
        return token.get("access_token")

    @validate_input(LINKEDIN_TOKEN_SCHEMA)
    def _get_user_email(self, token):
        email = requests.get(
            "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        return email.get("elements")[0].get("handle~").get("emailAddress")


class SellOrderService(DefaultService):
    def __init__(self, config, SellOrder=SellOrder, User=User, Round=Round):
        super().__init__(config)
        self.SellOrder = SellOrder
        self.User = User
        self.Round = Round

    @validate_input(CREATE_ORDER_SCHEMA)
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

            active_round = RoundService(self.config).get_active()
            if active_round is None:
                session.add(sell_order)
                session.commit()
                if RoundService(self.config).should_round_start():
                    self._set_orders_to_new_round()
            else:
                sell_order.round_id = active_round["id"]
                session.add(sell_order)

            session.commit()
            return sell_order.asdict()

    @validate_input({"user_id": UUID_RULE})
    def get_orders_by_user(self, user_id):
        with session_scope() as session:
            sell_orders = session.query(self.SellOrder).filter_by(user_id=user_id).all()
            return [sell_order.asdict() for sell_order in sell_orders]

    @validate_input(EDIT_ORDER_SCHEMA)
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

    @validate_input(DELETE_ORDER_SCHEMA)
    def delete_order(self, id, subject_id):
        with session_scope() as session:
            sell_order = session.query(self.SellOrder).filter_by(id=id).one()
            if sell_order.user_id != subject_id:
                raise UnauthorizedException("You need to own this order.")

            session.delete(sell_order)
        return {}

    def _set_orders_to_new_round(self):
        with session_scope() as session:
            new_round = self.Round(
                end_time=datetime.now() + self.config["ACQUITY_ROUND_LENGTH"],
                is_concluded=False,
            )
            session.add(new_round)
            session.flush()

            for sell_order in session.query(self.SellOrder).filter_by(round_id=None):
                sell_order.round_id = str(new_round.id)


class BuyOrderService(DefaultService):
    def __init__(self, config, BuyOrder=BuyOrder, User=User):
        super().__init__(config)
        self.BuyOrder = BuyOrder
        self.User = User

    @validate_input(CREATE_ORDER_SCHEMA)
    def create_order(self, user_id, number_of_shares, price, security_id):
        with session_scope() as session:
            user = session.query(self.User).filter_by(id=user_id).one()
            if not user.can_buy:
                raise UnauthorizedException("This user cannot buy securities.")

            active_round = RoundService(self.config).get_active()
            if active_round is None:
                raise NoActiveRoundException(
                    "There is no active round to associate this buy order with."
                )

            buy_order = self.BuyOrder(
                user_id=user_id,
                number_of_shares=number_of_shares,
                price=price,
                security_id=security_id,
                round_id=active_round["id"],
            )

            session.add(buy_order)
            session.commit()
            return buy_order.asdict()

    @validate_input({"user_id": UUID_RULE})
    def get_orders_by_user(self, user_id):
        with session_scope() as session:
            buy_orders = session.query(self.BuyOrder).filter_by(user_id=user_id).all()
            return [buy_order.asdict() for buy_order in buy_orders]

    @validate_input(EDIT_ORDER_SCHEMA)
    def edit_order(self, id, subject_id, new_number_of_shares=None, new_price=None):
        with session_scope() as session:
            buy_order = session.query(self.BuyOrder).filter_by(id=id).one()
            if buy_order.user_id != subject_id:
                raise UnauthorizedException("You need to own this order.")

            if new_number_of_shares is not None:
                buy_order.number_of_shares = new_number_of_shares
            if new_price is not None:
                buy_order.price = new_price

            session.commit()
            return buy_order.asdict()

    @validate_input(DELETE_ORDER_SCHEMA)
    def delete_order(self, id, subject_id):
        with session_scope() as session:
            buy_order = session.query(self.BuyOrder).filter_by(id=id).one()
            if buy_order.user_id != subject_id:
                raise UnauthorizedException("You need to own this order.")

            session.delete(buy_order)
        return {}


class SecurityService(DefaultService):
    def __init__(self, config, Security=Security):
        super().__init__(config)
        self.Security = Security

    def get_all(self):
        with session_scope() as session:
            return [sec.asdict() for sec in session.query(self.Security).all()]


class RoundService(DefaultService):
    def __init__(self, config, Round=Round, SellOrder=SellOrder):
        super().__init__(config)
        self.Round = Round
        self.SellOrder = SellOrder

    def get_all(self):
        with session_scope() as session:
            return [r.asdict() for r in session.query(self.Round).all()]

    def get_active(self):
        with session_scope() as session:
            active_round = (
                session.query(self.Round)
                .filter(
                    self.Round.end_time >= datetime.now(),
                    self.Round.is_concluded == False,
                )
                .one_or_none()
            )
            return active_round and active_round.asdict()

    def should_round_start(self):
        with session_scope() as session:
            unique_sellers = (
                session.query(self.SellOrder.user_id)
                .filter_by(round_id=None)
                .distinct()
                .count()
            )
            if (
                unique_sellers
                >= self.config["ACQUITY_ROUND_START_NUMBER_OF_SELLERS_CUTOFF"]
            ):
                return True

            total_shares = (
                session.query(func.sum(self.SellOrder.number_of_shares))
                .filter_by(round_id=None)
                .scalar()
                or 0
            )
            return (
                total_shares
                >= self.config["ACQUITY_ROUND_START_TOTAL_SELL_SHARES_CUTOFF"]
            )
