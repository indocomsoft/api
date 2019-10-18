from src.database import Base
from tests.utils import assert_dict_in


class DummyClass(Base):
    __tablename__ = "x"

    @property
    def additional_things_to_dict(self):
        return {"a": 2}


def test_asdict():
    assert_dict_in({"a": 2}, DummyClass().asdict())
