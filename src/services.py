from collections import defaultdict
from datetime import datetime, timezone

import requests
from passlib.hash import argon2
from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased
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
    Offer,
    UserRequest,
    session_scope,
)
from src.email_service import EmailService
from src.exceptions import (
    InvisibleUnauthorizedException,
    ResourceNotFoundException,
    ResourceNotOwnedException,
    UnauthorizedException,
    UserProfileNotFoundException,
)
from src.match import match_buyers_and_sellers
from src.schemata import (
    AUTHENTICATE_SCHEMA,
    CREATE_BUY_ORDER_SCHEMA,
    CREATE_SELL_ORDER_SCHEMA,
    DELETE_ORDER_SCHEMA,
    EDIT_MARKET_PRICE_SCHEMA,
    EDIT_ORDER_SCHEMA,
    GET_AUTH_URL_SHCMEA,
    UUID_RULE,
    validate_input,
)


class UserService:
    def __init__(self, config, hasher=argon2):
        self.config = config
        self.hasher = hasher

    def create_if_not_exists(
        self, email, display_image_url, full_name, user_id, is_buy
    ):
        with session_scope() as session:
            user = session.query(User).filter_by(user_id=user_id).one_or_none()
            if user is None:
                user = User(
                    email=email,
                    full_name=full_name,
                    display_image_url=display_image_url,
                    provider="linkedin",
                    can_buy=False,
                    can_sell=False,
                    user_id=user_id,
                )
                session.add(user)
                session.flush()

                req = UserRequest(user_id=str(user.id), is_buy=is_buy)
                session.add(req)
            else:
                user.email = email
                user.full_name = full_name
                user.display_image_url = display_image_url

            session.commit()
            return user.asdict()

    @validate_input({"id": UUID_RULE})
    def get_user(self, id):
        with session_scope() as session:
            user = session.query(User).get(id)
            if user is None:
                raise ResourceNotFoundException()
            user_dict = user.asdict()
        return user_dict

    def get_user_by_linkedin_id(self, user_id):
        with session_scope() as session:
            user = session.query(User).filter_by(user_id=user_id).one_or_none()
            if user is None:
                raise ResourceNotFoundException()
            user_dict = user.asdict()
        return user_dict


class SellOrderService:
    def __init__(self, config):
        self.config = config

    @validate_input(CREATE_SELL_ORDER_SCHEMA)
    def create_order(self, user_id, number_of_shares, price, security_id, scheduler):
        with session_scope() as session:
            user = session.query(User).get(user_id)
            if user is None:
                raise ResourceNotFoundException()

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
                    RoundService(self.config).create_new_round_and_set_orders(scheduler)
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

    @validate_input(CREATE_BUY_ORDER_SCHEMA)
    def create_order(self, user_id, number_of_shares, price, security_id):
        with session_scope() as session:
            user = session.query(User).get(user_id)
            if user is None:
                raise ResourceNotFoundException()

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

    @validate_input(EDIT_MARKET_PRICE_SCHEMA)
    def edit_market_price(self, id, subject_id, market_price):
        with session_scope() as session:
            security = session.query(Security).get(id)
            if security is None:
                raise ResourceNotFoundException()

            subject = session.query(User).get(subject_id)
            if not subject.is_committee:
                raise UnauthorizedException(
                    "You need to be a committee of this security."
                )

            security.market_price = market_price
            session.commit()
            return security.asdict()


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

    def create_new_round_and_set_orders(self, scheduler):
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
            EmailService(self.config).send_email(emails, template="round_opened")

        if scheduler is not None:
            scheduler.add_job(
                MatchService(self.config).run_matches, "date", run_date=end_time
            )

    @validate_input({"security_id": UUID_RULE})
    def get_previous_round_statistics(self, security_id):
        return None


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
                for b in session.query(BuyOrder)
                .join(User, User.id == BuyOrder.user_id)
                .filter(BuyOrder.round_id == round_id, User.can_buy)
                .all()
            ]
            sell_orders = [
                s.asdict()
                for s in session.query(SellOrder)
                .join(User, User.id == SellOrder.user_id)
                .filter(SellOrder.round_id == round_id, User.can_sell)
                .all()
            ]
            banned_pairs = [
                (bp.buyer_id, bp.seller_id) for bp in session.query(BannedPair).all()
            ]

        return buy_orders, self._double_sell_orders(sell_orders), banned_pairs

    def _double_sell_orders(self, sell_orders):
        seller_counts = defaultdict(lambda: 0)
        for sell_order in sell_orders:
            seller_counts[sell_order["user_id"]] += 1

        new_sell_orders = []
        for sell_order in sell_orders:
            new_sell_orders.append(sell_order)
            if seller_counts[sell_order["user_id"]] == 1:
                new_sell_orders.append(sell_order)

        return new_sell_orders

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


class OfferService:
    def __init__(self, config):
        self.config = config

    def _serialize_offer(self, offer, user_id):
        return {
            "id": offer.get("id"),
            "price": offer.get("price"),
            "number_of_shares": offer.get("number_of_shares"),
            "is_buyer_agreeable": offer.get("is_buyer_agreeable"),
            "is_seller_agreeable": offer.get("is_seller_agreeable"),
            "is_rejected": offer.get("is_rejected"),
            "updated_at": datetime.timestamp(offer.get("updated_at")) * 1000,
            "is_author": True if offer.get("author_id") == user_id else False,
            "type": "offer"
        }

    def _serialize_chat_offer(self, chat_room_id, offer, user_id):
        return {
            "chat_room_id": chat_room_id,
            "updated_at": datetime.timestamp(offer.get("updated_at")) * 1000,
            "new_chat": self._serialize_offer(offer=offer, user_id=user_id),
        } 
    
    def _get_current_offer(self, session, offer):
        session.add(offer)
        session.flush()
        session.refresh(offer)
        return offer.asdict()

    def _set_last_chat_date_time(self, session, chat_room_id, offer):
        chat_room = session.query(ChatRoom).filter_by(id=chat_room_id).one()
        chat_room.updated_at = offer.get("updated_at")
        session.commit()
    
    def set_new_offer(self, chat_room_id, author_id, price, number_of_shares):
        with session_scope() as session:
            offer = Offer(
                chat_room_id=str(chat_room_id),
                price=price,
                number_of_shares=number_of_shares,
                author_id=str(author_id),
            )
            offer = self._get_current_offer(session=session, offer=offer)
            self._set_last_chat_date_time(session=session, chat_room_id=chat_room_id, offer=offer)
            return self._serialize_chat_offer(
                chat_room_id=chat_room_id,
                offer=offer,
                user_id=author_id,
            )

    def set_accept_offer(self, chat_room_id, offer_id, user_id):
        with session_scope() as session:
            offer_chat_room = session.query(Offer, ChatRoom)\
                .filter_by(id=offer_id)\
                .outerjoin(ChatRoom, Offer.chat_room_id == ChatRoom.id)\
                .one()
            if offer_chat_room[1].seller_id == user_id:
                offer_chat_room[0].is_seller_agreeable = True
            elif offer_chat_room[1].buyer_id == user_id:
                offer_chat_room[0].is_buyer_agreeable = True
            else:
                raise ResourceNotOwnedException("Wrong user")
            offer = self._get_current_offer(session=session, offer=offer_chat_room[0])
            self._set_last_chat_date_time(session=session, chat_room_id=chat_room_id, offer=offer)
            return self._serialize_chat_offer(
                chat_room_id=chat_room_id,
                offer=offer,
                user_id=user_id,
            )

    def set_reject_offer(self, chat_room_id, offer_id, user_id):
        with session_scope() as session:
            offer = session.query(Offer).filter_by(id=offer_id).one()
            offer.is_rejected = True
            offer = self._get_current_offer(session=session, offer=offer)
            self._set_last_chat_date_time(session=session, chat_room_id=chat_room_id, offer=offer)
            return self._serialize_chat_offer(
                chat_room_id=chat_room_id,
                offer=offer,
                user_id=user_id,
            )

    def get_chat_offers(self, user_id, chat_room_id):
        with session_scope() as session:
            results = session.query(Offer)\
                .filter_by(chat_room_id=chat_room_id)\
                .all()
            data = []
            for result in results:
                data.append(self._serialize_offer(
                    offer=result.asdict(),
                    user_id=user_id,
                ))
            return data

class ChatService:
    def __init__(self, config):
        self.config = config

    def _serialize_message(self, message, user_id):
        return {
            "id": message.get("id"),
            "message": message.get("message"),
            "updated_at": datetime.timestamp(message.get("updated_at")) * 1000,
            "is_author": True if message.get("author_id") == user_id else False,
            "type": "message",
        }

    def _serialize_chat_message(self, chat_room_id, message, user_id):
        return {
            "chat_room_id": chat_room_id,
            "updated_at": datetime.timestamp(message.get("updated_at")) * 1000,
            "new_chat": self._serialize_message(message=message, user_id=user_id),
        }

    def _get_current_message(self, session, message):
        session.add(message)
        session.flush()
        session.refresh(message)
        return message.asdict()

    def _set_last_chat_date_time(self, session, chat_room_id, message):
        chat_room = session.query(ChatRoom).filter_by(id=chat_room_id).one()
        chat_room.updated_at = message.get("updated_at")
        session.commit()

    def set_new_message(self, chat_room_id, message, author_id):
        with session_scope() as session:
            message = Chat(
                chat_room_id=str(chat_room_id),
                message=message,
                author_id=str(author_id),
            )
            message = self._get_current_message(session=session, message=message)
            self._set_last_chat_date_time(session=session, chat_room_id=chat_room_id, message=message)
            return self._serialize_chat_message(
                chat_room_id=chat_room_id,
                message=message,
                user_id=author_id,
            )

    def get_chat_messages(self, user_id, chat_room_id):
        with session_scope() as session:
            results = session.query(Chat)\
                .filter_by(chat_room_id=chat_room_id)\
                .all()
            data = []
            for result in results:
                data.append(self._serialize_message(
                    message=result.asdict(),
                    user_id=user_id,
                ))
            return data

    def get_conversation(self, user_id, chat_room_id):
        with session_scope() as session:
            results = session.query(ChatRoom, BuyOrder, SellOrder)\
                .filter(ChatRoom.id == chat_room_id)\
                .outerjoin(BuyOrder, ChatRoom.buyer_id == BuyOrder.user_id)\
                .outerjoin(SellOrder, ChatRoom.seller_id == SellOrder.user_id)\
                .one()

            chat_room = results[0].asdict()
            buy_order = results[1].asdict()
            sell_order = results[2].asdict()

            offers = OfferService(self.config)\
                .get_chat_offers(user_id=user_id, chat_room_id=chat_room_id)
            messages = self.get_chat_messages(user_id=user_id, chat_room_id=chat_room_id)
            
            return {
                "chat_room_id": chat_room_id,
                "seller_price": sell_order.get("price"),
                "seller_number_of_shares": sell_order.get("number_of_shares"),
                "buyer_price": buy_order.get("price"),
                "buyer_number_of_shares": buy_order.get("number_of_shares"),
                "updated_at": datetime.timestamp(chat_room.get("updated_at")) * 1000,
                "conversation": sorted(messages + offers, key=lambda item: item["updated_at"])
            }


class ChatRoomService:
    def __init__(self, config):
        self.config = config

    def _serialize_chat_room(self, chat_room, buyer, seller, buy_order, sell_order):
        return {
            "chat_room_id": chat_room.get("id"),
            "seller_price": sell_order.get("price"),
            "seller_number_of_shares": sell_order.get("number_of_shares"),
            "buyer_price": buy_order.get("price"),
            "buyer_number_of_shares": buy_order.get("number_of_shares"),
            "updated_at": datetime.timestamp(chat_room.get("updated_at")) * 1000,
        }

    def get_chat_rooms(self, user_id):
        data = []
        with session_scope() as session:
            Buyer = aliased(User)
            Seller = aliased(User)
            results = session.query(ChatRoom, Buyer, Seller, BuyOrder, SellOrder)\
                .filter(ChatRoom.seller_id == user_id)\
                .outerjoin(Buyer, Buyer.id == ChatRoom.buyer_id)\
                .outerjoin(Seller, Seller.id == ChatRoom.seller_id)\
                .outerjoin(BuyOrder, Seller.id == BuyOrder.user_id)\
                .outerjoin(SellOrder, Seller.id == SellOrder.user_id)\
                .all()
            for result in results:
                data.append(self._serialize_chat_room(
                    chat_room=result[0].asdict(),
                    buyer=result[1].asdict(),
                    seller=result[2].asdict(),
                    buy_order=result[3].asdict(),
                    sell_order=result[4].asdict(),
                ))

        return sorted(data, key=lambda item: item["updated_at"], reverse=True)

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


class LinkedInLogin:
    def __init__(self, config):
        self.config = config

    @validate_input(GET_AUTH_URL_SHCMEA)
    def get_auth_url(self, redirect_uri):
        client_id = self.config.get("CLIENT_ID")
        response_type = "code"

        scope = "r_liteprofile%20r_emailaddress%20w_member_social%20r_basicprofile"
        # TODO add state
        url = f"https://www.linkedin.com/oauth/v2/authorization?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}"

        return url

    @validate_input(AUTHENTICATE_SCHEMA)
    def authenticate(self, code, redirect_uri, is_buy):
        token = self._get_token(code=code, redirect_uri=redirect_uri)
        user = self._get_linkedin_user(token)
        UserService(self.config).create_if_not_exists(**user, is_buy=is_buy)
        return {"access_token": token}

    def _get_linkedin_user(self, token):
        user_profile = self._get_user_profile(token=token)
        email = self._get_user_email(token=token)
        return {**user_profile, "email": email}

    def _get_token(self, code, redirect_uri):
        return requests.post(
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

    @staticmethod
    def _get_user_profile(token):
        user_profile_request = requests.get(
            "https://api.linkedin.com/v2/me?projection=(id,firstName,lastName,profilePicture(displayImage~:playableStreams))",
            headers={"Authorization": f"Bearer {token}"},
        )
        if user_profile_request.status_code == 401:
            raise UserProfileNotFoundException("User profile not found")
        user_profile_data = user_profile_request.json()
        user_id = user_profile_data.get("id")
        first_name = user_profile_data.get("firstName").get("localized").get("en_US")
        last_name = user_profile_data.get("lastName").get("localized").get("en_US")
        try:
            display_image_url = (
                user_profile_data.get("profilePicture")
                .get("displayImage~")
                .get("elements")[-1]
                .get("identifiers")[0]
                .get("identifier")
            )
        except AttributeError:
            display_image_url = None

        return {
            "full_name": f"{first_name} {last_name}",
            "display_image_url": display_image_url,
            "user_id": user_id,
        }

    @staticmethod
    def _get_user_email(token):
        email_request = requests.get(
            "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
            headers={"Authorization": f"Bearer {token}"},
        )
        if email_request.status_code == 401:
            raise UserProfileNotFoundException("User email not found")
        email_data = email_request.json()
        return email_data.get("elements")[0].get("handle~").get("emailAddress")


class UserRequestService:
    def __init__(self, config):
        self.config = config

    @validate_input({"subject_id": UUID_RULE})
    def get_buy_requests(self, subject_id):
        with session_scope() as session:
            if not session.query(User).get(subject_id).is_committee:
                raise InvisibleUnauthorizedException("Not committee")

            buy_requests = session.query(UserRequest).filter_by(is_buy=True).all()
            return [buy_request.asdict() for buy_request in buy_requests]

    @validate_input({"subject_id": UUID_RULE})
    def get_sell_requests(self, subject_id):
        with session_scope() as session:
            if not session.query(User).get(subject_id).is_committee:
                raise InvisibleUnauthorizedException("Not committee")

            sell_requests = session.query(BuyOrder).filter_by(is_buy=False).all()
            return [sell_request.asdict() for sell_request in sell_requests]

    @validate_input({"request_id": UUID_RULE, "subject_id": UUID_RULE})
    def approve_request(self, request_id, subject_id):
        with session_scope() as session:
            if not session.query(User).get(subject_id).is_committee:
                raise InvisibleUnauthorizedException("Not committee")

            request = session.query(UserRequest).get(request_id)
            user = session.query(User).get(request.user_id)

            if request.is_buy:
                user.can_buy = True
            else:
                user.can_sell = False

            request.delete()

    @validate_input({"request_id": UUID_RULE, "subject_id": UUID_RULE})
    def reject_request(self, request_id, subject_id):
        with session_scope() as session:
            if not session.query(User).get(subject_id).is_committee:
                raise InvisibleUnauthorizedException("Not committee")

            session.query(UserRequest).get(request_id).delete()
