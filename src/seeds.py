import uuid

from passlib.hash import argon2

from src.database import Chat, ChatRoom, Security, User, session_scope


def seed_db():
    with session_scope() as session:

        # adding users
        user_seeds = [
            {
                "email": "admin@acquity.com",
                "password": "acquity",
                "full_name": "Acquity",
                "can_buy": True,
                "can_sell": True,
                "is_committe": True,
            },
            {
                "email": "a@a.com",
                "password": "acquity",
                "full_name": "Aaron",
                "can_buy": True,
                "can_sell": True,
                "is_committe": False,
            },
            {
                "email": "b@b.com",
                "password": "acquity",
                "full_name": "Ben",
                "can_buy": True,
                "can_sell": True,
                "is_committe": False,
            },
            {
                "email": "c@c.com",
                "password": "acquity",
                "full_name": "Colin",
                "can_buy": True,
                "can_sell": True,
                "is_committee": False,
            },
        ]
        for user in user_seeds:
            if session.query(User).filter_by(email=user.get("email")).count() == 0:
                session.add(
                    User(
                        email=user.get("email"),
                        hashed_password=argon2.hash(user.get("password")),
                        full_name=user.get("full_name"),
                        can_buy=user.get("can_buy"),
                        can_sell=user.get("can_sell"),
                        is_committee=user.get("is_committee"),
                    )
                )

        # getting user ids
        admin_id = session.query(User).filter_by(email="admin@acquity.com").first().id
        aaron_id = session.query(User).filter_by(email="a@a.com").first().id
        ben_id = session.query(User).filter_by(email="b@b.com").first().id
        colin_id = session.query(User).filter_by(email="c@c.com").first().id

        # creating chatrooms
        if session.query(ChatRoom).filter_by(seller_id=str(aaron_id)).count() == 0:
            session.add(ChatRoom(seller_id=str(aaron_id), buyer_id=str(ben_id)))
        if session.query(ChatRoom).filter_by(seller_id=str(ben_id)).count() == 0:
            session.add(ChatRoom(seller_id=str(ben_id), buyer_id=str(colin_id)))

        # creating chats
        chat_room_id = (
            session.query(ChatRoom).filter_by(seller_id=str(aaron_id)).first().id
        )
        if session.query(Chat).filter_by(chat_room_id=str(chat_room_id)).count() == 0:
            session.add(
                Chat(
                    chat_room_id=str(chat_room_id),
                    message="Start your deal now!",
                    author_id=str(aaron_id),
                )
            )
        chat_room_id = (
            session.query(ChatRoom).filter_by(buyer_id=str(colin_id)).first().id
        )
        if session.query(Chat).filter_by(chat_room_id=str(chat_room_id)).count() == 0:
            session.add(
                Chat(
                    chat_room_id=str(chat_room_id),
                    message="Start your deal now!",
                    author_id=str(colin_id),
                )
            )

        # adding securities
        if session.query(Security).filter_by(name="Grab").count() == 0:
            session.add(Security(name="Grab"))


if __name__ == "__main__":
    seed_db()
