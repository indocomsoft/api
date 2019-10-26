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
            user = session.query(self.User).get(user_id)
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
            inviter = session.query(self.User).get(inviter_id)
            if inviter is None:
                raise ResourceNotFoundException()
            if not inviter.is_committee:
                raise UnauthorizedException("Inviter is not a committee.")

            invited = session.query(self.User).get(invited_id)
            invited.can_sell = True

            session.commit()

            result = invited.asdict()
        result.pop("hashed_password")
        return result

    @validate_input(INVITE_SCHEMA)
    def invite_to_be_buyer(self, inviter_id, invited_id):
        with session_scope() as session:
            inviter = session.query(self.User).get(inviter_id)
            if inviter is None:
                raise ResourceNotFoundException()
            if not inviter.is_committee:
                raise UnauthorizedException("Inviter is not a committee.")

            invited = session.query(self.User).get(invited_id)
            invited.can_buy = True

            session.commit()

            result = invited.asdict()
        result.pop("hashed_password")
        return result

    @validate_input(USER_AUTH_SCHEMA)
    def authenticate(self, email, password):
        with session_scope() as session:
            user = session.query(self.User).filter_by(email=email).one_or_none()
            if user is None:
                raise ResourceNotFoundException()
            if self.hasher.verify(password, user.hashed_password):
                return user.asdict()
            else:
                return None

    @validate_input({"id": UUID_RULE})
    def get_user(self, id):
        with session_scope() as session:
            user = session.query(self.User).get(id)
            if user is None:
                raise ResourceNotFoundException()
            if user is None:
                raise NoResultFound
            user_dict = user.asdict()
        user_dict.pop("hashed_password")
        return user_dict


class SellOrderService(DefaultService):
    def __init__(self, config, SellOrder=SellOrder, User=User, Round=Round):
        super().__init__(config)
        self.SellOrder = SellOrder
        self.User = User
        self.Round = Round

    @validate_input(CREATE_ORDER_SCHEMA)
    def create_order(self, user_id, number_of_shares, price, security_id):
        with session_scope() as session:
            user = session.query(self.User).get(user_id)
            if user is None:
                raise ResourceNotFoundException()
            if not user.can_sell:
                raise UnauthorizedException("This user cannot sell securities.")

            sell_order_count = (
                session.query(self.SellOrder).filter_by(user_id=user_id).count()
            )
            if sell_order_count >= self.config["ACQUITY_SELL_ORDER_PER_ROUND_LIMIT"]:
                raise UnauthorizedException("Limit of sell orders reached.")

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
                    RoundService(self.config).set_orders_to_new_round()
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

    @validate_input({"id": UUID_RULE, "user_id": UUID_RULE})
    def get_order_by_id(self, id, user_id):
        with session_scope() as session:
            order = session.query(self.SellOrder).get(id)
            if order is None:
                raise ResourceNotFoundException()
            if order.user_id != user_id:
                raise ResourceNotOwnedException()
            return order.asdict()

    @validate_input(EDIT_ORDER_SCHEMA)
    def edit_order(self, id, subject_id, new_number_of_shares=None, new_price=None):
        with session_scope() as session:
            sell_order = session.query(self.SellOrder).get(id)
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
            sell_order = session.query(self.SellOrder).get(id)
            if sell_order is None:
                raise ResourceNotFoundException()
            if sell_order.user_id != subject_id:
                raise ResourceNotOwnedException("You need to own this order.")

            session.delete(sell_order)
        return {}


class BuyOrderService(DefaultService):
    def __init__(self, config, BuyOrder=BuyOrder, User=User):
        super().__init__(config)
        self.BuyOrder = BuyOrder
        self.User = User

    @validate_input(CREATE_ORDER_SCHEMA)
    def create_order(self, user_id, number_of_shares, price, security_id):
        with session_scope() as session:
            user = session.query(self.User).get(user_id)
            if user is None:
                raise ResourceNotFoundException()
            if not user.can_buy:
                raise UnauthorizedException("This user cannot buy securities.")

            buy_order_count = (
                session.query(self.BuyOrder).filter_by(user_id=user_id).count()
            )
            if buy_order_count >= self.config["ACQUITY_BUY_ORDER_PER_ROUND_LIMIT"]:
                raise UnauthorizedException("Limit of buy orders reached.")

            active_round = RoundService(self.config).get_active()

            buy_order = self.BuyOrder(
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
            buy_orders = session.query(self.BuyOrder).filter_by(user_id=user_id).all()
            return [buy_order.asdict() for buy_order in buy_orders]

    @validate_input({"id": UUID_RULE, "user_id": UUID_RULE})
    def get_order_by_id(self, id, user_id):
        with session_scope() as session:
            order = session.query(self.BuyOrder).get(id)
            if order is None:
                raise ResourceNotFoundException()
            if order.user_id != user_id:
                raise ResourceNotOwnedException()
            return order.asdict()

    @validate_input(EDIT_ORDER_SCHEMA)
    def edit_order(self, id, subject_id, new_number_of_shares=None, new_price=None):
        with session_scope() as session:
            buy_order = session.query(self.BuyOrder).get(id)
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
            buy_order = session.query(self.BuyOrder).get(id)
            if buy_order is None:
                raise ResourceNotFoundException()
            if buy_order.user_id != subject_id:
                raise ResourceNotOwnedException("You need to own this order.")

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
    def __init__(self, config, Round=Round, SellOrder=SellOrder, BuyOrder=BuyOrder):
        super().__init__(config)
        self.Round = Round
        self.SellOrder = SellOrder
        self.BuyOrder = BuyOrder

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

    def set_orders_to_new_round(self):
        with session_scope() as session:
            end_time = datetime.now(timezone.utc) + self.config["ACQUITY_ROUND_LENGTH"]
            new_round = self.Round(end_time=end_time, is_concluded=False)
            session.add(new_round)
            session.flush()

            self._schedule_event(end_time)

            for sell_order in session.query(self.SellOrder).filter_by(round_id=None):
                sell_order.round_id = str(new_round.id)
            for buy_order in session.query(self.BuyOrder).filter_by(round_id=None):
                buy_order.round_id = str(new_round.id)

    def _schedule_event(self, end_time):
        temporize_url = self.config["TEMPORIZE_URL"]
        end_time_encoded = end_time.strftime("%Y%m%dT%H%M%SZ")

        host = self.config["HOST"]
        temporize_token = self.config["TEMPORIZE_TOKEN"]
        callback_url = quote(f"{host}/v1/match/{temporize_token}", safe="")

        requests.post(f"{temporize_url}/v1/events/{end_time_encoded}/{callback_url}")


class MatchService(DefaultService):
    def __init__(
        self,
        config,
        BuyOrder=BuyOrder,
        SellOrder=SellOrder,
        Match=Match,
        BannedPair=BannedPair,
    ):
        super().__init__(config)
        self.BuyOrder = BuyOrder
        self.SellOrder = SellOrder
        self.Match = Match
        self.BannedPair = BannedPair

    def run_matches(self):
        round_id = RoundService(self.config).get_active()["id"]

        with session_scope() as session:
            buy_orders = [
                b.asdict()
                for b in session.query(self.BuyOrder).filter_by(round_id=round_id).all()
            ]
            sell_orders = [
                s.asdict()
                for s in session.query(self.SellOrder)
                .filter_by(round_id=round_id)
                .all()
            ]
            banned_pairs = [
                (bp.buyer_id, bp.seller_id)
                for bp in session.query(self.BannedPair).all()
            ]

        match_results = match_buyers_and_sellers(buy_orders, sell_orders, banned_pairs)

        with session_scope() as session:
            for buy_order_id, sell_order_id in match_results:
                match = self.Match(
                    buy_order_id=buy_order_id, sell_order_id=sell_order_id
                )
                session.add(match)

            session.query(Round).get(round_id).is_concluded = True


class BannedPairService(DefaultService):
    def __init__(self, config, BannedPair=BannedPair):
        super().__init__(config)
        self.BannedPair = BannedPair

    @validate_input({"my_user_id": UUID_RULE, "other_user_id": UUID_RULE})
    def ban_user(self, my_user_id, other_user_id):
        # Currently this bans the user two-way: both as buyer and as seller
        with session_scope() as session:
            session.add_all(
                [
                    self.BannedPair(buyer_id=my_user_id, seller_id=other_user_id),
                    self.BannedPair(buyer_id=other_user_id, seller_id=my_user_id),
                ]
            )


def serialize_chat(chat_room_result, chat_result, buyer, seller, user_id):
    (author, dealer) = (
        (seller, buyer) if seller.get("id") == user_id else (buyer, seller)
    )
    return {
        "dealer_name": dealer.get("full_name"),
        "dealer_id": dealer.get("id"),
        "created_at": datetime.timestamp(chat_result.get("created_at")),
        "updated_at": datetime.timestamp(chat_result.get("updated_at")),
        "author_name": author.get("full_name"),
        "author_id": author.get("id"),
        "message": chat_result.get("message"),
        "chatRoom_id": chat_room_result.get("id"),
    }


class ChatService(DefaultService):
    def __init__(
        self, config, User=User, UserService=UserService, Chat=Chat, ChatRoom=ChatRoom
    ):
        self.Buyer = aliased(User)
        self.Seller = aliased(User)
        self.User = User
        self.Chat = Chat
        self.UserService = UserService
        self.ChatRoom = ChatRoom
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

            result = (
                session.query(self.ChatRoom, self.Buyer, self.Seller)
                .filter_by(id=chat.get("chat_room_id"))
                .outerjoin(self.Buyer, self.Buyer.id == self.ChatRoom.buyer_id)
                .outerjoin(self.Seller, self.Seller.id == self.ChatRoom.seller_id)
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
            results = (
                session.query(self.ChatRoom, self.Chat, self.Buyer, self.Seller)
                .filter(self.ChatRoom.id == chat_room_id)
                .outerjoin(self.Chat, self.Chat.chat_room_id == self.ChatRoom.id)
                .outerjoin(self.Buyer, self.Buyer.id == self.ChatRoom.buyer_id)
                .outerjoin(self.Seller, self.Seller.id == self.ChatRoom.seller_id)
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


class ChatRoomService(DefaultService):
    def __init__(
        self,
        config,
        User=User,
        Chat=Chat,
        UserService=UserService,
        ChatRoom=ChatRoom,
        ChatService=ChatService,
    ):
        self.Buyer = aliased(User)
        self.Seller = aliased(User)
        self.User = User
        self.Chat = Chat
        self.UserService = UserService
        self.ChatRoom = ChatRoom
        self.ChatService = ChatService
        self.config = config

    def get_chat_rooms(self, user_id):
        data = []
        with session_scope() as session:

            subq = (
                session.query(
                    self.Chat.chat_room_id,
                    func.max(self.Chat.created_at).label("maxdate"),
                )
                .group_by(self.Chat.chat_room_id)
                .subquery()
            )

            results = (
                (
                    session.query(self.Chat, self.ChatRoom, self.Buyer, self.Seller)
                    .join(
                        subq,
                        and_(
                            self.Chat.chat_room_id == subq.c.chat_room_id,
                            self.Chat.created_at == subq.c.maxdate,
                        ),
                    )
                    .outerjoin(
                        self.ChatRoom, self.ChatRoom.id == self.Chat.chat_room_id
                    )
                )
                .filter(
                    or_(
                        self.ChatRoom.seller_id == user_id,
                        self.ChatRoom.buyer_id == user_id,
                    )
                )
                .outerjoin(self.Buyer, self.Buyer.id == self.ChatRoom.buyer_id)
                .outerjoin(self.Seller, self.Seller.id == self.ChatRoom.seller_id)
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
