from datetime import datetime, timedelta

from src.config import APP_CONFIG
from src.services import RoundService
from tests.fixtures import create_round, create_sell_order

round_service = RoundService(config=APP_CONFIG)


def test_get_all():
    round_id = create_round("1")["id"]
    round_id2 = create_round("2")["id"]
    rounds = round_service.get_all()
    assert len(rounds) == 2
    assert frozenset([r["id"] for r in rounds]) == frozenset([round_id, round_id2])


def test_get_active():
    active_id = create_round(
        end_time=datetime.now() + timedelta(weeks=1), is_concluded=False
    )["id"]

    active_round = round_service.get_active()
    assert active_round["id"] == active_id


def test_get_active__all_in_the_past():
    create_round(end_time=datetime.now() - timedelta(weeks=1), is_concluded=True)
    create_round(end_time=datetime.now() - timedelta(weeks=2), is_concluded=False)
    assert round_service.get_active() is None


def test_get_active__all_concluded():
    create_round(end_time=datetime.now() + timedelta(weeks=1), is_concluded=True)
    create_round(end_time=datetime.now() + timedelta(weeks=2), is_concluded=True)
    assert round_service.get_active() is None


def test_should_round_start__unique_sellers():
    create_sell_order("1", number_of_shares=5, round_id=None)
    assert not round_service.should_round_start()
    create_sell_order("2", number_of_shares=5, round_id=None)
    assert round_service.should_round_start()
    create_sell_order("3", number_of_shares=5, round_id=None)
    assert round_service.should_round_start()


def test_should_round_start__big_shares_amount():
    create_sell_order("1", number_of_shares=1000, round_id=None)
    assert round_service.should_round_start()
