import pytest

from src.database import Security, session_scope
from src.services import SecurityService
from tests.utils import assert_dict_in

security_service = SecurityService(Security=Security)


def test_get_all():
    with session_scope() as session:
        security = Security(name="Grab")
        security2 = Security(name="Barg")
        session.add_all([security, security2])
        session.commit()

    securities = security_service.get_all()
    assert len(securities) == 2
    assert frozenset([s["name"] for s in securities]) == frozenset(["Grab", "Barg"])
