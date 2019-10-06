from os import getenv

APP_CONFIG = {
    "DATABASE_URL": getenv(
        "DATABASE_URL", "postgresql://acquity:acquity@localhost/acquity"
    ),
    "CORS_AUTOMATIC_OPTIONS": True,
    "PORT": getenv("PORT", 8000),
}
