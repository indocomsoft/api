from passlib.hash import argon2

from src.database import Security, Seller, session_scope
from src.services import SecurityService, SellerService


def seed_db():
    with session_scope() as session:
        if session.query(Seller).filter_by(email="a@a.com").count() == 0:
            session.add(
                Seller(
                    email="a@a.com",
                    hashed_password=argon2.hash("acquity"),
                    full_name="Ben",
                )
            )
        if session.query(Security).filter_by(name="Grab").count() == 0:
            session.add(Security(name="Grab"))


if __name__ == "__main__":
    seed_db()
