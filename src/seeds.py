from passlib.hash import argon2

from src.database import Security, User, session_scope


def seed_db():
    with session_scope() as session:
        if session.query(User).filter_by(email="a@a.com").count() == 0:
            session.add(
                User(
                    email="a@a.com",
                    hashed_password=argon2.hash("acquity"),
                    full_name="Ben",
                    can_buy=True,
                    can_sell=True,
                )
            )
        if session.query(Security).filter_by(name="Grab").count() == 0:
            session.add(Security(name="Grab"))


if __name__ == "__main__":
    seed_db()
