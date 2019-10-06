from os import getenv

APP_CONFIG = {
    "DATABASE_URL": getenv(
        "DATABASE_URL", "postgresql://acquity:acquity@localhost/acquity"
    ),
    "CORS_AUTOMATIC_OPTIONS": True,
    "PORT": getenv("PORT", 8000),
    "SANIC_JWT_URL_PREFIX": "/auth/seller",
    "SANIC_JWT_EXPIRATION_DELTA": 2 * 24 * 3600,  # 2 days
    "SANIC_JWT_USER_ID": "id",
    "SANIC_JWT_SECRET": getenv(
        "JWT_SECRET", "secret" if getenv("ACQUITY_ENV") == "DEVELOPMENT" else ""
    ),
}
