from datetime import datetime, timedelta

from src.config import APP_CONFIG
from src.database import Round, Security, SellOrder, User, session_scope
from src.services import RoundService

round_service = RoundService(config=APP_CONFIG, Round=Round, SellOrder=SellOrder)


def test_get_all():
    with session_scope() as session:
        round = Round(end_time=datetime.now(), is_concluded=True)
        round2 = Round(end_time=datetime.now(), is_concluded=False)
        session.add_all([round, round2])
        session.commit()

        round_id = str(round.id)
        round_id2 = str(round2.id)

    rounds = round_service.get_all()
    assert len(rounds) == 2
    assert frozenset([r["id"] for r in rounds]) == frozenset([round_id, round_id2])


def test_get_active():
    with session_scope() as session:
        round = Round(end_time=datetime.now() - timedelta(weeks=1), is_concluded=True)
        round2 = Round(end_time=datetime.now() + timedelta(weeks=1), is_concluded=False)
        session.add_all([round, round2])
        session.commit()

        active_id = str(round2.id)

    active_round = round_service.get_active()
    assert active_round["id"] == active_id


def test_get_active__all_in_the_past():
    with session_scope() as session:
        round = Round(end_time=datetime.now() - timedelta(weeks=1), is_concluded=True)
        round2 = Round(end_time=datetime.now() - timedelta(weeks=2), is_concluded=False)
        session.add_all([round, round2])
        session.commit()

    assert round_service.get_active() is None


def test_get_active__all_concluded():
    with session_scope() as session:
        round = Round(end_time=datetime.now() + timedelta(weeks=1), is_concluded=True)
        round2 = Round(end_time=datetime.now() + timedelta(weeks=2), is_concluded=True)
        session.add_all([round, round2])
        session.commit()

    assert round_service.get_active() is None


def test_should_round_start__unique_sellers():
    with session_scope() as session:
        user = User(
            can_buy=False,
            can_sell=True,
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
        )
        user2 = User(
            can_buy=False,
            can_sell=True,
            email="b@b",
            hashed_password="123456",
            full_name="Ben",
        )
        user3 = User(
            can_buy=False,
            can_sell=True,
            email="c@c",
            hashed_password="123456",
            full_name="Ben",
        )

        security = Security(name="Grab")
        session.add_all([user, user2, user3, security])
        session.flush()

        security_id = str(security.id)

        session.add(
            SellOrder(
                user_id=str(user.id),
                number_of_shares=20,
                price=30,
                security_id=security_id,
            )
        )
        session.commit()
        assert not round_service.should_round_start()

        session.add(
            SellOrder(
                user_id=str(user2.id),
                number_of_shares=20,
                price=30,
                security_id=security_id,
            )
        )
        session.commit()
        assert round_service.should_round_start()

        session.add(
            SellOrder(
                user_id=str(user3.id),
                number_of_shares=20,
                price=30,
                security_id=security_id,
            )
        )
        session.commit()
        assert round_service.should_round_start()


def test_should_round_start__total_shares():
    with session_scope() as session:
        user = User(
            can_buy=False,
            can_sell=True,
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
        )

        security = Security(name="Grab")
        session.add_all([user, security])
        session.flush()

        user_id = str(user.id)
        security_id = str(security.id)

        session.add(
            SellOrder(
                user_id=user_id, number_of_shares=500, price=30, security_id=security_id
            )
        )
        session.commit()
        assert not round_service.should_round_start()

        session.add(
            SellOrder(
                user_id=user_id, number_of_shares=500, price=40, security_id=security_id
            )
        )
        session.commit()
        assert round_service.should_round_start()

        session.add(
            SellOrder(
                user_id=user_id, number_of_shares=500, price=50, security_id=security_id
            )
        )
        session.commit()
        assert round_service.should_round_start()
