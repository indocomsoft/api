from datetime import datetime, timezone
from operator import itemgetter
from urllib.parse import quote

import requests
from passlib.hash import argon2
from sqlalchemy import and_, asc, desc, funcfilter, or_
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func

from src.database import (
    BannedPair,
    BuyOrder,
    Chat,
    ChatRoom,
    Match,
    Round,
    Security,
    SellOrder,
    User,
    session_scope,
)
from src.email_service import EmailService
from src.exceptions import (
    ResourceNotFoundException,
    ResourceNotOwnedException,
    UnauthorizedException,
)
from src.match import match_buyers_and_sellers
from src.schemata import (
    CREATE_ORDER_SCHEMA,
    CREATE_USER_SCHEMA,
    DELETE_ORDER_SCHEMA,
    EDIT_ORDER_SCHEMA,
    INVITE_SCHEMA,
    USER_AUTH_SCHEMA,
    UUID_RULE,
    validate_input,
)


class UserService:
    def __init__(self, config, hasher=argon2):
        self.config = config
        self.hasher = hasher

    @validate_input(CREATE_USER_SCHEMA)
    def create(self, email, password, full_name):
        with session_scope() as session:
            hashed_password = self.hasher.hash(password)
            user = User(
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
            user = session.query(User).get(user_id)
            if user is None:
                raise ResourceNotFoundException()

            user.can_buy = True
            session.commit()
            result = user.asdict()
        result.pop("hashed_password")
        return result

    @validate_input(INVITE_SCHEMA)
    def invite_to_be_seller(self, inviter_id, invited_id):
        with session_scope() as session:
            inviter = session.query(User).get(inviter_id)
            if inviter is None:
                raise ResourceNotFoundException()
            if not inviter.is_committee:
                raise UnauthorizedException("Inviter is not a committee.")

            invited = session.query(User).get(invited_id)
            invited.can_sell = True

            session.commit()

            result = invited.asdict()
        result.pop("hashed_password")
        return result

    @validate_input(INVITE_SCHEMA)
    def invite_to_be_buyer(self, inviter_id, invited_id):
        with session_scope() as session:
            inviter = session.query(User).get(inviter_id)
            if inviter is None:
                raise ResourceNotFoundException()
            if not inviter.is_committee:
                raise UnauthorizedException("Inviter is not a committee.")

            invited = session.query(User).get(invited_id)
            invited.can_buy = True

            session.commit()

            result = invited.asdict()
        result.pop("hashed_password")
        return result

    @validate_input(USER_AUTH_SCHEMA)
    def authenticate(self, email, password):
        with session_scope() as session:
            user = session.query(User).filter_by(email=email).one_or_none()
            if user is None:
                raise ResourceNotFoundException()
            if self.hasher.verify(password, user.hashed_password):
                return user.asdict()
            else:
                return None

    @validate_input({"id": UUID_RULE})
    def get_user(self, id):
        with session_scope() as session:
            user = session.query(User).get(id)
            if user is None:
                raise ResourceNotFoundException()
            if user is None:
                raise NoResultFound
            user_dict = user.asdict()
        user_dict.pop("hashed_password")
        return user_dict

    def get_user_by_email(self, email):
        with session_scope() as session:
            user = session.query(User).filter_by(email=email).one_or_none()
            if user is None:
                raise InvalidRequestException("Linkedin email does not match")
            if user is None:
                raise NoResultFound
            user_dict = user.asdict()
        user_dict.pop("hashed_password")
        return user_dict


class SellOrderService:
    def __init__(self, config):
        self.config = config

    @validate_input(CREATE_ORDER_SCHEMA)
    def create_order(self, user_id, number_of_shares, price, security_id):
        with session_scope() as session:
            user = session.query(User).get(user_id)
            if user is None:
                raise ResourceNotFoundException()
            if not user.can_sell:
                raise UnauthorizedException("This user cannot sell securities.")

            sell_order_count = (
                session.query(SellOrder).filter_by(user_id=user_id).count()
            )
            if sell_order_count >= self.config["ACQUITY_SELL_ORDER_PER_ROUND_LIMIT"]:
                raise UnauthorizedException("Limit of sell orders reached.")

            sell_order = SellOrder(
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
                    RoundService(self.config).create_new_round_and_set_orders()
            else:
                sell_order.round_id = active_round["id"]
                session.add(sell_order)

            session.commit()
            return sell_order.asdict()

    @validate_input({"user_id": UUID_RULE})
    def get_orders_by_user(self, user_id):
        with session_scope() as session:
            sell_orders = session.query(SellOrder).filter_by(user_id=user_id).all()
            return [sell_order.asdict() for sell_order in sell_orders]

    @validate_input({"id": UUID_RULE, "user_id": UUID_RULE})
    def get_order_by_id(self, id, user_id):
        with session_scope() as session:
            order = session.query(SellOrder).get(id)
            if order is None:
                raise ResourceNotFoundException()
            if order.user_id != user_id:
                raise ResourceNotOwnedException()
            return order.asdict()

    @validate_input(EDIT_ORDER_SCHEMA)
    def edit_order(self, id, subject_id, new_number_of_shares=None, new_price=None):
        with session_scope() as session:
            sell_order = session.query(SellOrder).get(id)
            if sell_order is None:
                raise ResourceNotFoundException()
            if sell_order.user_id != subject_id:
                raise ResourceNotOwnedException("You need to own this order.")

            if new_number_of_shares is not None:
                sell_order.number_of_shares = new_number_of_shares
            if new_price is not None:
                sell_order.price = new_price

            session.commit()
            return sell_order.asdict()

    @validate_input(DELETE_ORDER_SCHEMA)
    def delete_order(self, id, subject_id):
        with session_scope() as session:
            sell_order = session.query(SellOrder).get(id)
            if sell_order is None:
                raise ResourceNotFoundException()
            if sell_order.user_id != subject_id:
                raise ResourceNotOwnedException("You need to own this order.")

            session.delete(sell_order)
        return {}


class BuyOrderService:
    def __init__(self, config):
        self.config = config

    @validate_input(CREATE_ORDER_SCHEMA)
    def create_order(self, user_id, number_of_shares, price, security_id):
        with session_scope() as session:
            user = session.query(User).get(user_id)
            if user is None:
                raise ResourceNotFoundException()
            if not user.can_buy:
                raise UnauthorizedException("This user cannot buy securities.")

            buy_order_count = session.query(BuyOrder).filter_by(user_id=user_id).count()
            if buy_order_count >= self.config["ACQUITY_BUY_ORDER_PER_ROUND_LIMIT"]:
                raise UnauthorizedException("Limit of buy orders reached.")

            active_round = RoundService(self.config).get_active()

            buy_order = BuyOrder(
                user_id=user_id,
                number_of_shares=number_of_shares,
                price=price,
                security_id=security_id,
                round_id=(active_round and active_round["id"]),
            )

            session.add(buy_order)
            session.commit()
            return buy_order.asdict()

    @validate_input({"user_id": UUID_RULE})
    def get_orders_by_user(self, user_id):
        with session_scope() as session:
            buy_orders = session.query(BuyOrder).filter_by(user_id=user_id).all()
            return [buy_order.asdict() for buy_order in buy_orders]

    @validate_input({"id": UUID_RULE, "user_id": UUID_RULE})
    def get_order_by_id(self, id, user_id):
        with session_scope() as session:
            order = session.query(BuyOrder).get(id)
            if order is None:
                raise ResourceNotFoundException()
            if order.user_id != user_id:
                raise ResourceNotOwnedException()
            return order.asdict()

    @validate_input(EDIT_ORDER_SCHEMA)
    def edit_order(self, id, subject_id, new_number_of_shares=None, new_price=None):
        with session_scope() as session:
            buy_order = session.query(BuyOrder).get(id)
            if buy_order is None:
                raise ResourceNotFoundException()
            if buy_order.user_id != subject_id:
                raise ResourceNotOwnedException("You need to own this order.")

            if new_number_of_shares is not None:
                buy_order.number_of_shares = new_number_of_shares
            if new_price is not None:
                buy_order.price = new_price

            session.commit()
            return buy_order.asdict()

    @validate_input(DELETE_ORDER_SCHEMA)
    def delete_order(self, id, subject_id):
        with session_scope() as session:
            buy_order = session.query(BuyOrder).get(id)
            if buy_order is None:
                raise ResourceNotFoundException()
            if buy_order.user_id != subject_id:
                raise ResourceNotOwnedException("You need to own this order.")

            session.delete(buy_order)
        return {}


class SecurityService:
    def __init__(self, config):
        self.config = config

    def get_all(self):
        with session_scope() as session:
            return [sec.asdict() for sec in session.query(Security).all()]


class RoundService:
    def __init__(self, config):
        self.config = config

    def get_all(self):
        with session_scope() as session:
            return [r.asdict() for r in session.query(Round).all()]

    def get_active(self):
        with session_scope() as session:
            active_round = (
                session.query(Round)
                .filter(Round.end_time >= datetime.now(), Round.is_concluded == False)
                .one_or_none()
            )
            return active_round and active_round.asdict()

    def should_round_start(self):
        with session_scope() as session:
            unique_sellers = (
                session.query(SellOrder.user_id)
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
                session.query(func.sum(SellOrder.number_of_shares))
                .filter_by(round_id=None)
                .scalar()
                or 0
            )
            return (
                total_shares
                >= self.config["ACQUITY_ROUND_START_TOTAL_SELL_SHARES_CUTOFF"]
            )

    def create_new_round_and_set_orders(self):
        with session_scope() as session:
            end_time = datetime.now(timezone.utc) + self.config["ACQUITY_ROUND_LENGTH"]
            new_round = Round(end_time=end_time, is_concluded=False)
            session.add(new_round)
            session.flush()

            for sell_order in session.query(SellOrder).filter_by(round_id=None):
                sell_order.round_id = str(new_round.id)
            for buy_order in session.query(BuyOrder).filter_by(round_id=None):
                buy_order.round_id = str(new_round.id)

            emails = [user.email for user in session.query(User).all()]
            EmailService(self.config).send_email(
                bcc_list=emails, template="round_opened"
            )


class MatchService:
    def __init__(self, config):
        self.config = config

    def run_matches(self):
        round_id = RoundService(self.config).get_active()["id"]
        buy_orders, sell_orders, banned_pairs = self._get_matching_params(round_id)

        match_results = match_buyers_and_sellers(buy_orders, sell_orders, banned_pairs)

        buy_order_to_buyer_dict = {
            order["id"]: order["user_id"] for order in buy_orders
        }
        sell_order_to_seller_dict = {
            order["id"]: order["user_id"] for order in sell_orders
        }

        self._add_db_objects(
            round_id, match_results, sell_order_to_seller_dict, buy_order_to_buyer_dict
        )
        self._send_emails(buy_orders, sell_orders, match_results)

    def _get_matching_params(self, round_id):
        with session_scope() as session:
            buy_orders = [
                b.asdict()
                for b in session.query(BuyOrder).filter_by(round_id=round_id).all()
            ]
            sell_orders = [
                s.asdict()
                for s in session.query(SellOrder).filter_by(round_id=round_id).all()
            ]
            banned_pairs = [
                (bp.buyer_id, bp.seller_id) for bp in session.query(BannedPair).all()
            ]

        return buy_orders, sell_orders, banned_pairs

    def _add_db_objects(
        self,
        round_id,
        match_results,
        sell_order_to_seller_dict,
        buy_order_to_buyer_dict,
    ):
        with session_scope() as session:
            for buy_order_id, sell_order_id in match_results:
                match = Match(buy_order_id=buy_order_id, sell_order_id=sell_order_id)
                chat_room = ChatRoom(
                    seller_id=sell_order_to_seller_dict[sell_order_id],
                    buyer_id=buy_order_to_buyer_dict[buy_order_id],
                )
                session.add_all([match, chat_room])

            session.query(Round).get(round_id).is_concluded = True

    def _send_emails(self, buy_orders, sell_orders, match_results):
        matched_uuids = set()
        for buy_order_uuid, sell_order_uuid in match_results:
            matched_uuids.add(buy_order_uuid)
            matched_uuids.add(sell_order_uuid)

        all_user_ids = set()
        matched_user_ids = set()
        for buy_order in buy_orders:
            all_user_ids.add(buy_order["user_id"])
            if buy_order["id"] in matched_uuids:
                matched_user_ids.add(buy_order["user_id"])
        for sell_order in sell_orders:
            all_user_ids.add(sell_order["user_id"])
            if sell_order["id"] in matched_uuids:
                matched_user_ids.add(sell_order["user_id"])

        with session_scope() as session:
            matched_emails = [
                user.email
                for user in session.query(User)
                .filter(User.id.in_(matched_user_ids))
                .all()
            ]
            EmailService(self.config).send_email(
                matched_emails, template="match_done_has_match"
            )

            unmatched_emails = [
                user.email
                for user in session.query(User)
                .filter(User.id.in_(all_user_ids - matched_user_ids))
                .all()
            ]
            EmailService(self.config).send_email(
                unmatched_emails, template="match_done_no_match"
            )


class BannedPairService:
    def __init__(self, config):
        self.config = config

    @validate_input({"my_user_id": UUID_RULE, "other_user_id": UUID_RULE})
    def ban_user(self, my_user_id, other_user_id):
        # Currently this bans the user two-way: both as buyer and as seller
        with session_scope() as session:
            session.add_all(
                [
                    BannedPair(buyer_id=my_user_id, seller_id=other_user_id),
                    BannedPair(buyer_id=other_user_id, seller_id=my_user_id),
                ]
            )


def serialize_chat(chat_room_result, chat_result, buyer, seller, user_id):
    (author, dealer) = (
        (seller, buyer) if seller.get("id") == user_id else (buyer, seller)
    )
    return {
        "dealer_id": dealer.get("id"),
        "created_at": datetime.timestamp(chat_result.get("created_at")),
        "updated_at": datetime.timestamp(chat_result.get("updated_at")),
        "author_name": author.get("full_name"),
        "author_id": author.get("id"),
        "message": chat_result.get("message"),
        "chatRoom_id": chat_room_result.get("id"),
    }


class ChatService:
    def __init__(self, config):
        self.config = config

    def add_message(self, chat_room_id, message, author_id):
        with session_scope() as session:
            chat = Chat(
                chat_room_id=str(chat_room_id),
                message=message,
                author_id=str(author_id),
            )
            session.add(chat)
            session.flush()
            session.refresh(chat)
            chat = chat.asdict()

            Buyer = aliased(User)
            Seller = aliased(User)

            result = (
                session.query(ChatRoom, Buyer, Seller)
                .filter_by(id=chat.get("chat_room_id"))
                .outerjoin(Buyer, Buyer.id == ChatRoom.buyer_id)
                .outerjoin(Seller, Seller.id == ChatRoom.seller_id)
                .one()
            )
            return serialize_chat(
                chat_room_result=result[0].asdict(),
                chat_result=chat,
                buyer=result[1].asdict(),
                seller=result[2].asdict(),
                user_id=author_id,
            )

    def get_conversation(self, user_id, chat_room_id):
        with session_scope() as session:
            Buyer = aliased(User)
            Seller = aliased(User)

            results = (
                session.query(ChatRoom, Chat, Buyer, Seller)
                .filter(ChatRoom.id == chat_room_id)
                .outerjoin(Chat, Chat.chat_room_id == ChatRoom.id)
                .outerjoin(Buyer, Buyer.id == ChatRoom.buyer_id)
                .outerjoin(Seller, Seller.id == ChatRoom.seller_id)
                .all()
            )

            data = []
            for result in results:
                data.append(
                    serialize_chat(
                        chat_room_result=result[0].asdict(),
                        chat_result=result[1].asdict(),
                        buyer=result[2].asdict(),
                        seller=result[3].asdict(),
                        user_id=user_id,
                    )
                )
            return sorted(data, key=lambda item: item["created_at"])


class ChatRoomService:
    def __init__(self, config):
        self.config = config

    def get_chat_rooms(self, user_id):
        data = []
        with session_scope() as session:
            subq = (
                session.query(
                    Chat.chat_room_id, func.max(Chat.created_at).label("maxdate")
                )
                .group_by(Chat.chat_room_id)
                .subquery()
            )

            Buyer = aliased(User)
            Seller = aliased(User)

            results = (
                (
                    session.query(Chat, ChatRoom, Buyer, Seller)
                    .join(
                        subq,
                        and_(
                            Chat.chat_room_id == subq.c.chat_room_id,
                            Chat.created_at == subq.c.maxdate,
                        ),
                    )
                    .outerjoin(ChatRoom, ChatRoom.id == Chat.chat_room_id)
                )
                .filter(
                    or_(ChatRoom.seller_id == user_id, ChatRoom.buyer_id == user_id)
                )
                .outerjoin(Buyer, Buyer.id == ChatRoom.buyer_id)
                .outerjoin(Seller, Seller.id == ChatRoom.seller_id)
                .all()
            )
            for result in results:
                data.append(
                    serialize_chat(
                        chat_room_result=result[1].asdict(),
                        chat_result=result[0].asdict(),
                        buyer=result[2].asdict(),
                        seller=result[3].asdict(),
                        user_id=user_id,
                    )
                )
        return sorted(data, key=lambda item: item["created_at"], reverse=True)

    def get_other_party_details(self, chat_room_id, user_id):
        with session_scope() as session:
            chat_room = session.query(ChatRoom).get(chat_room_id).asdict()

        if not chat_room["is_revealed"]:
            raise ResourceNotOwnedException("Other party has not revealed.")

        if chat_room["seller_id"] == user_id:
            other_party_user_id = chat_room["buyer_id"]
        elif chat_room["buyer_id"] == user_id:
            other_party_user_id = chat_room["seller_id"]
        else:
            raise ResourceNotOwnedException("Wrong user.")

        with session_scope() as session:
            user = session.query(User).get(other_party_user_id).asdict()
            return {k: user[k] for k in ["email", "full_name"]}


class SocialLogin:
    def __init__(self, config, sio):
        self.config = config
        self.sio = sio

    def get_auth_url(self, socket_id):
        self.join_room(socket_id)
        host = self.config.get("HOST")
        client_id = self.config.get("CLIENT_ID")
        response_type = "code"
        redirect_uri = f"{host}/v1/linkedin/auth/callback"
        scope = "r_liteprofile%20r_emailaddress%20w_member_social"
        url = f"https://www.linkedin.com/oauth/v2/authorization?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={socket_id}"
        return url

    def join_room(self, socket_id):
        self.sio.enter_room(socket_id, "linkedin")

    async def authenticate(self, code, socket_id):
        token = self.get_token(code=code)
        full_name = self.get_user_profile(token=token)
        email = self.get_user_email(token=token)
        user = UserService(self.config).get_user_by_email(email=email)
        user = UserService(self.config).activate_buy_privileges(user_id=user.get("id"))
        user["created_at"] = user.get("created_at").timestamp()
        user["updated_at"] = user.get("updated_at").timestamp()
        await self.sio.emit("provider", user, namespace="/v1/", room=socket_id)
        self.sio.leave_room(socket_id, "linkedin")

    def get_token(self, code):
        host = self.config.get("HOST")
        redirect_uri = f"{host}/v1/linkedin/auth/callback"
        token = requests.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            headers={"Content-Type": "x-www-form-urlencoded"},
            params={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.config.get("CLIENT_ID"),
                "client_secret": self.config.get("CLIENT_SECRET"),
            },
        ).json()
        return token.get("access_token")

    def get_user_profile(self, token):
        user_profile = requests.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        first_name = user_profile.get("localizedFirstName")
        last_name = user_profile.get("localizedLastName")
        return {"full_name": f"{first_name} {last_name}"}

    def get_user_email(self, token):
        email = requests.get(
            "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        return email.get("elements")[0].get("handle~").get("emailAddress")
