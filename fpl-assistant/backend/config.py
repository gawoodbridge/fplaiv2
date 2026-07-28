import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Central application configuration.

    All values can be overridden with environment variables so the same
    codebase works locally and in a hosted environment.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET = os.environ.get("JWT_SECRET", "dev-jwt-secret-change-me")
    JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "72"))

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'fpl_assistant.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # How long (seconds) FPL API responses are cached in memory before
    # being re-fetched. The official API updates infrequently, so this
    # keeps the app fast and avoids hammering the upstream service.
    FPL_CACHE_TTL = int(os.environ.get("FPL_CACHE_TTL", "300"))

    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
