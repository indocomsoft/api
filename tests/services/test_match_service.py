from datetime import datetime
from unittest.mock import patch

from src.config import APP_CONFIG
from src.database import (
    BuyOrder,
    Match,
    Round,
    Security,
    SellOrder,
    User,
    session_scope,
)
from src.services import MatchService

match_service = MatchService(
    config=APP_CONFIG, BuyOrder=BuyOrder, SellOrder=SellOrder, Match=Match
)


def test_run_matches():
    with session_scope() as session:
        user = User(
            can_sell=False,
            can_buy=True,
            email="a@a",
            hashed_password="123456",
            full_name="Ben",
        )
        security = Security(name="Grab")
        round = Round(end_time=datetime.now(), is_concluded=False)
        session.add_all([user, security, round])
        session.commit()

        user_id = str(user.id)
        security_id = str(security.id)
        round_id = str(round.id)

        buy_order = BuyOrder(
            user_id=user_id,
            number_of_shares=20,
            price=30,
            security_id=security_id,
            round_id=round_id,
        )
        buy_order_2 = BuyOrder(
            user_id=user_id,
            number_of_shares=40,
            price=50,
            security_id=security_id,
            round_id=round_id,
        )
        sell_order = SellOrder(
            user_id=user_id,
            number_of_shares=20,
            price=30,
            security_id=security_id,
            round_id=round_id,
        )
        sell_order_2 = SellOrder(
            user_id=user_id,
            number_of_shares=40,
            price=50,
            security_id=security_id,
            round_id=round_id,
        )

        session.add_all([buy_order, buy_order_2, sell_order, sell_order_2])
        session.commit()

        buy_order_id = str(buy_order.id)
        sell_order_id = str(sell_order.id)
        round_dict = round.asdict()

    with patch(
        "src.services.match_buyers_and_sellers",
        return_value=[(buy_order_id, sell_order_id)],
    ), patch("src.services.RoundService.get_active", return_value=round_dict):
        match_service.run_matches()

    with session_scope() as session:
        match = session.query(Match).one()
        assert match.buy_order_id == buy_order_id
        assert match.sell_order_id == sell_order_id

        assert session.query(Round).get(round_dict["id"]).is_concluded
