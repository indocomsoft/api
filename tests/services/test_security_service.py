from src.config import APP_CONFIG
from src.database import Security, session_scope
from src.services import SecurityService
from tests.fixtures import create_security

security_service = SecurityService(config=APP_CONFIG)


def test_get_all():
    security = create_security("1")
    security2 = create_security("2")
    securities = security_service.get_all()
    assert len(securities) == 2
    assert frozenset([s["name"] for s in securities]) == frozenset(
        [security["name"], security2["name"]]
    )
