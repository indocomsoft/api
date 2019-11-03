from src.database import Chat, ChatRoom, Security, User, session_scope


def seed_db():
    with session_scope() as session:

        # adding users
        user_seeds = [
            {
                "email": "admin@acquity.com",
                "provider": "linkedin",
                "full_name": "Acquity",
                "display_image_url": "https://loremflickr.com/320/240",
                "can_buy": True,
                "can_sell": True,
                "is_committe": True,
                "user_id": "1",
            },
            {
                "email": "a@a.com",
                "provider": "linkedin",
                "full_name": "Aaron",
                "display_image_url": "https://loremflickr.com/320/240",
                "can_buy": True,
                "can_sell": True,
                "is_committe": False,
                "user_id": "2",
            },
            {
                "email": "b@b.com",
                "provider": "linkedin",
                "full_name": "Ben",
                "display_image_url": "https://loremflickr.com/320/240",
                "can_buy": True,
                "can_sell": True,
                "is_committe": False,
                "user_id": "3",
            },
            {
                "email": "c@c.com",
                "provider": "linkedin",
                "full_name": "Colin",
                "display_image_url": "https://loremflickr.com/320/240",
                "can_buy": True,
                "can_sell": True,
                "is_committee": False,
                "user_id": "4",
            },
            {
                "email": "nwjbrandon@outlook.com",
                "provider": "linkedin",
                "full_name": "Brandon Ng",
                "display_image_url": "https://media.licdn.com/dms/image/C5103AQHrnOLE-_QFsg/profile-displayphoto-shrink_800_800/0?e=1577923200&v=beta&t=c1KiSHRhuvVYqwYvkBOEhzAMw0ykSbBNjRsGNta_oGQ",
                "can_buy": True,
                "can_sell": True,
                "is_committee": True,
                "user_id": "z_1i-r7yV2",
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

        # getting user ids
        admin_id = session.query(User).filter_by(email="admin@acquity.com").first().id
        aaron_id = session.query(User).filter_by(email="a@a.com").first().id
        ben_id = session.query(User).filter_by(email="b@b.com").first().id
        colin_id = session.query(User).filter_by(email="c@c.com").first().id
        brandon_id = (
            session.query(User).filter_by(email="nwjbrandon@outlook.com").first().id
        )

        # creating chatrooms
        if session.query(ChatRoom).filter_by(seller_id=str(aaron_id)).count() == 0:
            session.add(ChatRoom(seller_id=str(aaron_id), buyer_id=str(brandon_id)))
        if session.query(ChatRoom).filter_by(seller_id=str(brandon_id)).count() == 0:
            session.add(ChatRoom(seller_id=str(brandon_id), buyer_id=str(colin_id)))

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
