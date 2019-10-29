import pytest

from src.config import APP_CONFIG
from src.database import Security, session_scope
from src.exceptions import UnauthorizedException
from src.services import SecurityService
from tests.fixtures import create_security, create_user

security_service = SecurityService(config=APP_CONFIG)


def test_get_all():
    security = create_security("1")
    security2 = create_security("2")
    securities = security_service.get_all()
    assert len(securities) == 2
    assert frozenset([s["name"] for s in securities]) == frozenset(
        [security["name"], security2["name"]]
    )


def test_edit_market_price():
    security = create_security()
    committee = create_user(is_committee=True)

    security_service.edit_market_price(
        id=security["id"], subject_id=committee["id"], market_price=10
    )
    with session_scope() as session:
        assert session.query(Security).one().market_price == 10

    security_service.edit_market_price(
        id=security["id"], subject_id=committee["id"], market_price=None
    )
    with session_scope() as session:
        assert session.query(Security).one().market_price is None


def test_edit_market_price__unauthorized():
    security = create_security()
    committee = create_user(is_committee=False)

    with pytest.raises(UnauthorizedException):
        security_service.edit_market_price(
            id=security["id"], subject_id=committee["id"], market_price=10
        )
