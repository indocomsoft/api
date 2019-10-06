from passlib.hash import argon2

from database import Seller, session_scope


class SellerService:
    def __init__(self, Seller=Seller, hasher=argon2):
        self.Seller = Seller
        self.hasher = hasher

    def create_account(self, email, password):
        with session_scope() as session:
            hashed_password = self.hasher.hash(password)
            seller = self.Seller(email=email, hashed_password=hashed_password)
            session.add(seller)

    def authenticate(self, email, password):
        with session_scope() as session:
            seller = session.query(self.Seller).filter_by(email=email).one()
            if self.hasher.verify(password, seller.hashed_password):
                return seller.asdict()
            else:
                return None
