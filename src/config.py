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
    "PORT": getenv("PORT", 8000),
    "SANIC_JWT_EXPIRATION_DELTA": 2 * 24 * 3600,  # 2 days
    "SANIC_JWT_USER_ID": "id",
    "SANIC_JWT_SECRET": getenv(
        "JWT_SECRET",
        "secret" if getenv("ACQUITY_ENV") in ["DEVELOPMENT", "TEST"] else "",
    ),
    "CLIENT_ID": getenv("CLIENT_ID"),
    "CLIENT_SECRET": getenv("CLIENT_SECRET"),
}
