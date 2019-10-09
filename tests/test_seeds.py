from src.database import Base, engine
from src.seeds import seed_db


def test_seed_db__idempotent():
    Base.metadata.create_all(engine)

    try:
        seed_db()
        seed_db()
    finally:
        Base.metadata.drop_all(engine)
