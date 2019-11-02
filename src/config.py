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
DATABASE_URL = getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

APP_CONFIG = {
    "DATABASE_URL": DATABASE_URL,
    "HOST": getenv("HOST"),
    "PORT": getenv("PORT", 8000),
    "CLIENT_ID": getenv("CLIENT_ID"),
    "CLIENT_SECRET": getenv("CLIENT_SECRET"),
    "ACQUITY_ROUND_START_NUMBER_OF_SELLERS_CUTOFF": 2,
    "ACQUITY_ROUND_START_TOTAL_SELL_SHARES_CUTOFF": 1000,
    "ACQUITY_ROUND_LENGTH": timedelta(weeks=1),
    "ACQUITY_SELL_ORDER_PER_ROUND_LIMIT": 2,
    "ACQUITY_BUY_ORDER_PER_ROUND_LIMIT": 1,
    "CORS_AUTOMATIC_OPTIONS": True,
    "CORS_SUPPORTS_CREDENTIALS": True,
    "MAILGUN_ENABLE": getenv("MAILGUN_ENABLE", ACQUITY_ENV == "PRODUCTION"),
    "MAILGUN_API_KEY": getenv("MAILGUN_API_KEY"),
    "MAILGUN_API_BASE_URL": getenv("MAILGUN_API_BASE_URL"),
    "SENTRY_ENABLE": getenv("SENTRY_ENABLE", ACQUITY_ENV == "PRODUCTION"),
    "apscheduler.jobstores.default": {"type": "sqlalchemy", "url": DATABASE_URL},
}
