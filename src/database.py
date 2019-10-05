from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

_base = declarative_base()


class Base(_base):
    __abstract__ = True

    id = Column(UUID, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), on_update=func.now())


class Seller(Base):
    __tablename__ = "sellers"

    email = Column(String)
    password = Column(String)


class Buyer(Base):
    __tablename__ = "buyers"

    email = Column(String)


class Invite(Base):
    __tablename__ = "invites"

    origin_seller_id = Column(UUID, ForeignKey("sellers.id"))
    destination_email = Column(String)
    valid = Column(Boolean)
    expiry_time = Column(DateTime)

    origin_seller = relationship("Seller", back_populates="invites")


class SellOrder(Base):
    __tablename__ = "sell_orders"

    seller_id = Column(UUID, ForeignKey("sellers.id"))
    number_of_shares = Column(Float)
    price = Column(Float)

    sellers = relationship("Seller", back_populates="orders")


class BuyOrder(Base):
    __tablename__ = "buy_orders"

    buyer_id = Column(UUID, ForeignKey("buyers.id"))
    number_of_shares = Column(Float)
    price = Column(Float)

    buyers = relationship("Buyer", back_populates="orders")


class Match(Base):
    __tablename__ = "matches"

    buy_order_id = Column(UUID, ForeignKey("buy_orders.id"))
    sell_order_id = Column(UUID, ForeignKey("sell_orders.id"))
    number_of_shares = Column(Float)
    price = Column(Float)

    buy_order = relationship("BuyOrder", back_populates="matches")
    sell_order = relationship("SellOrder", back_populates="matches")
