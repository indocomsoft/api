import pytest

from src.database import Base, engine


@pytest.fixture(autouse=True)
def db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
