import uuid
from contextlib import contextmanager

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    create_engine,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from src.config import APP_CONFIG

_base = declarative_base()


class Base(_base):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), on_update=func.now()
    )

    def asdict(self):
        d = {}
        columns = self.__table__.columns.keys()

        for col in columns:
            item = getattr(self, col)

            if isinstance(item, uuid.UUID):
                d[col] = str(item)
            else:
                d[col] = item
        return d


class Seller(Base):
    __tablename__ = "sellers"

    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)

    invites = relationship("Invite", back_populates="origin_seller")
    orders = relationship("SellOrder", back_populates="seller")


class Buyer(Base):
    __tablename__ = "buyers"

    email = Column(String, nullable=False, unique=True)

    orders = relationship("BuyOrder", back_populates="buyer")


class Invite(Base):
    __tablename__ = "invites"

    origin_seller_id = Column(UUID, ForeignKey("sellers.id"), nullable=False)
    destination_email = Column(String, nullable=False)
    valid = Column(Boolean, nullable=False)
    expiry_time = Column(DateTime(timezone=True), nullable=False)

    origin_seller = relationship("Seller", back_populates="invites")


class SellOrder(Base):
    __tablename__ = "sell_orders"

    seller_id = Column(UUID, ForeignKey("sellers.id"), nullable=False)
    number_of_shares = Column(Float, nullable=False)
    price = Column(Float, nullable=False)

    seller = relationship("Seller", back_populates="orders")
    matches = relationship("Match", back_populates="sell_order")


class BuyOrder(Base):
    __tablename__ = "buy_orders"

    buyer_id = Column(UUID, ForeignKey("buyers.id"), nullable=False)
    number_of_shares = Column(Float, nullable=False)
    price = Column(Float, nullable=False)

    buyer = relationship("Buyer", back_populates="orders")
    matches = relationship("Match", back_populates="buy_order")


class Match(Base):
    __tablename__ = "matches"

    buy_order_id = Column(UUID, ForeignKey("buy_orders.id"), nullable=False)
    sell_order_id = Column(UUID, ForeignKey("sell_orders.id"), nullable=False)
    number_of_shares = Column(Float, nullable=False)
    price = Column(Float, nullable=False)

    buy_order = relationship("BuyOrder", back_populates="matches")
    sell_order = relationship("SellOrder", back_populates="matches")


engine = create_engine(APP_CONFIG["DATABASE_URL"])


Session = sessionmaker(bind=engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
