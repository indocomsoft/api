import uuid
from datetime import datetime

from src.database import (
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


def seed_db():
    with session_scope() as session:

        # add users
        user_seeds = [
            {
                "email": "nwjbrandon.lexonous@gmail.com",
                "provider": "linkedin",
                "full_name": "Brandon Ng",
                "display_image_url": None,
                "can_buy": True,
                "can_sell": True,
                "is_committee": True,
                "user_id": "UiYX0uP7Cf",
            },
            {
                "email": "brandon.ng10@yahoo.com.sg",
                "provider": "linkedin",
                "full_name": "Brandon Ng",
                "display_image_url": None,
                "can_buy": True,
                "can_sell": True,
                "is_committee": True,
                "user_id": "8tJpx5jWUx",
            },
        ]
        for user in user_seeds:
            if session.query(User).filter_by(email=user.get("email")).count() == 0:
                session.add(
                    User(
                        email=user.get("email"),
                        provider=user.get("provider"),
                        display_image_url=user.get("display_image_url"),
                        full_name=user.get("full_name"),
                        can_buy=user.get("can_buy"),
                        can_sell=user.get("can_sell"),
                        is_committee=user.get("is_committee"),
                        user_id=user.get("user_id"),
                    )
                )
        brandon_gmail_id = (
            session.query(User)
            .filter_by(email="nwjbrandon.lexonous@gmail.com")
            .first()
            .id
        )
        brandon_yahoo_id = (
            session.query(User).filter_by(email="brandon.ng10@yahoo.com.sg").first().id
        )

        # create chatrooms
        if (
            session.query(ChatRoom).filter_by(seller_id=str(brandon_gmail_id)).count()
            == 0
        ):
            session.add(
                ChatRoom(
                    buyer_id=str(brandon_yahoo_id),
                    seller_id=str(brandon_gmail_id),
                    buyer_hidden_id=str(uuid.uuid4()),
                    seller_hidden_id=str(uuid.uuid4())
                )
            )
        if (
            session.query(ChatRoom).filter_by(seller_id=str(brandon_yahoo_id)).count()
            == 0
        ):
            session.add(
                ChatRoom(
                    buyer_id=str(brandon_gmail_id), 
                    seller_id=str(brandon_yahoo_id),
                    buyer_hidden_id=str(uuid.uuid4()),
                    seller_hidden_id=str(uuid.uuid4())
                )
            )

        # adds security
        if session.query(Security).filter_by(name="Grab").count() == 0:
            session.add(Security(name="Grab"))
        grab_security_id = session.query(Security).filter_by(name="Grab").first().id

        # creates round
        current_round_end_time = datetime.now()
        if session.query(Round).filter_by(end_time=current_round_end_time).count() == 0:
            session.add(Round(end_time=current_round_end_time, is_concluded=True))
        current_round_id = session.query(Round).first().id

        # create buy orders
        if (
            session.query(BuyOrder).filter_by(user_id=str(brandon_gmail_id)).count()
            == 0
        ):
            session.add(
                BuyOrder(
                    user_id=str(brandon_gmail_id),
                    security_id=str(grab_security_id),
                    number_of_shares=100,
                    price=10,
                    round_id=str(current_round_id),
                )
            )
        if (
            session.query(BuyOrder).filter_by(user_id=str(brandon_yahoo_id)).count()
            == 0
        ):
            session.add(
                BuyOrder(
                    user_id=str(brandon_yahoo_id),
                    security_id=str(grab_security_id),
                    number_of_shares=200,
                    price=10,
                    round_id=str(current_round_id),
                )
            )
        brandon_yahoo_buy_order = (
            session.query(BuyOrder).filter_by(user_id=str(brandon_yahoo_id)).first().id
        )
        brandon_gmail_buy_order = (
            session.query(BuyOrder).filter_by(user_id=str(brandon_gmail_id)).first().id
        )

        # create sell orders
        if (
            session.query(SellOrder).filter_by(user_id=str(brandon_gmail_id)).count()
            == 0
        ):
            session.add(
                SellOrder(
                    user_id=str(brandon_gmail_id),
                    security_id=str(grab_security_id),
                    number_of_shares=300,
                    price=10,
                    round_id=str(current_round_id),
                )
            )
        if (
            session.query(SellOrder).filter_by(user_id=str(brandon_yahoo_id)).count()
            == 0
        ):
            session.add(
                SellOrder(
                    user_id=str(brandon_yahoo_id),
                    security_id=str(grab_security_id),
                    number_of_shares=400,
                    price=10,
                    round_id=str(current_round_id),
                )
            )
        brandon_yahoo_sell_order = (
            session.query(SellOrder).filter_by(user_id=str(brandon_yahoo_id)).first().id
        )
        brandon_gmail_sell_order = (
            session.query(SellOrder).filter_by(user_id=str(brandon_gmail_id)).first().id
        )


if __name__ == "__main__":
    seed_db()
