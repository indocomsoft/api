import datetime

import requests
from passlib.hash import argon2

from src.config import APP_CONFIG
from src.database import BuyOrder, Security, SellOrder, User, session_scope
from src.exceptions import InvalidRequestException, UnauthorizedException
from src.schemata import (
    CREATE_ORDER_SCHEMA,
    CREATE_USER_SCHEMA,
    DELETE_ORDER_SCHEMA,
    EDIT_ORDER_SCHEMA,
    EMAIL_RULE,
    INVITE_SCHEMA,
    LINKEDIN_BUYER_PRIVILEGES_SCHEMA,
    LINKEDIN_CODE_SCHEMA,
    LINKEDIN_MATCH_EMAILS_SCHEMA,
    LINKEDIN_TOKEN_SCHEMA,
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


class LinkedinService:
    def __init__(self, User=User, UserService=UserService):
        self.User = User
        self.UserService = UserService

    @validate_input(LINKEDIN_BUYER_PRIVILEGES_SCHEMA)
    def activate_buyer_privileges(self, code, redirect_uri, user_email):
        linkedin_email = self.get_user_data(code=code, redirect_uri=redirect_uri)
        is_email = self.is_match(linkedin_email=linkedin_email, user_email=user_email)
        if is_email:
            user = self.UserService().get_user_by_email(email=user_email)
            return self.UserService().activate_buy_privileges(user_id=user.get("id"))
        else:
            raise InvalidRequestException("Linkedin email does not match")

    @validate_input(LINKEDIN_CODE_SCHEMA)
    def get_user_data(self, code, redirect_uri):
        token = self.get_token(code=code, redirect_uri=redirect_uri)
        return self.get_user_email(token=token)

    @validate_input(LINKEDIN_CODE_SCHEMA)
    def get_token(self, code, redirect_uri):
        token = requests.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            headers={"Content-Type": "x-www-form-urlencoded"},
            params={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": APP_CONFIG.get("CLIENT_ID"),
                "client_secret": APP_CONFIG.get("CLIENT_SECRET"),
            },
        ).json()
        return token.get("access_token")

    @validate_input(LINKEDIN_TOKEN_SCHEMA)
    def get_user_profile(self, token):
        user_profile = requests.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        first_name = user_profile.get("localizedFirstName")
        last_name = user_profile.get("localizedLastName")
        return {"full_name": f"{first_name} {last_name}"}

    @validate_input(LINKEDIN_TOKEN_SCHEMA)
    def get_user_email(self, token):
        email = requests.get(
            "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        return email.get("elements")[0].get("handle~").get("emailAddress")

    @validate_input(LINKEDIN_MATCH_EMAILS_SCHEMA)
    def is_match(self, user_email, linkedin_email):
        return True if user_email == linkedin_email else False


class SellOrderService:
    def __init__(self, SellOrder=SellOrder, User=User):
        self.SellOrder = SellOrder
        self.User = User

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


class BuyOrderService:
    def __init__(self, BuyOrder=BuyOrder, User=User):
        self.BuyOrder = BuyOrder
        self.User = User

    @validate_input(CREATE_ORDER_SCHEMA)
    def create_order(self, user_id, number_of_shares, price, security_id):
        with session_scope() as session:
            user = session.query(self.User).filter_by(id=user_id).one()
            if not user.can_buy:
                raise UnauthorizedException("This user cannot buy securities.")

            buy_order = self.BuyOrder(
                user_id=user_id,
                number_of_shares=number_of_shares,
                price=price,
                security_id=security_id,
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


class SecurityService:
    def __init__(self, Security=Security):
        self.Security = Security

    def get_all(self):
        with session_scope() as session:
            return [sec.asdict() for sec in session.query(self.Security).all()]
