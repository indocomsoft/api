from datetime import timedelta
from os import getenv

from dotenv import load_dotenv

load_dotenv()

ACQUITY_ENV = getenv("ACQUITY_ENV")
DEFAULT_DATABASE_URL = ""
if ACQUITY_ENV == "DEVELOPMENT":
    DEFAULT_DATABASE_URL = "postgresql://acquity:acquity@localhost/acquity"
elif ACQUITY_ENV == "TEST":
    DEFAULT_DATABASE_URL = "postgresql://acquity:acquity@localhost/acquity_test"

APP_CONFIG = {
    "DATABASE_URL": getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
    "CORS_AUTOMATIC_OPTIONS": True,
    "HOST": getenv("HOST"),
    "PORT": getenv("PORT", 8000),
    "SANIC_JWT_EXPIRATION_DELTA": 2 * 24 * 3600,  # 2 days
    "SANIC_JWT_USER_ID": "id",
    "SANIC_JWT_SECRET": getenv(
        "JWT_SECRET", "secret" if ACQUITY_ENV in ["DEVELOPMENT", "TEST"] else ""
    ),
    "CLIENT_ID": getenv("CLIENT_ID"),
    "CLIENT_SECRET": getenv("CLIENT_SECRET"),
    "ACQUITY_ROUND_START_NUMBER_OF_SELLERS_CUTOFF": 2,
    "ACQUITY_ROUND_START_TOTAL_SELL_SHARES_CUTOFF": 1000,
    "ACQUITY_ROUND_LENGTH": timedelta(weeks=1),
    "ACQUITY_SELL_ORDER_PER_ROUND_LIMIT": 2,
    "ACQUITY_BUY_ORDER_PER_ROUND_LIMIT": 1,
    "CORS_SUPPORTS_CREDENTIALS": True,
    "MAILGUN_API_KEY": getenv("MAILGUN_API_KEY"),
    "MAILGUN_API_BASE_URL": getenv("MAILGUN_API_BASE_URL"),
}
