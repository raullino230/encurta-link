import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    BASE_URL = os.environ.get("BASE_URL")
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    REDIS_URL = os.environ.get("REDIS_URL")
    CLICK_RETENTION_DAYS = int(os.getenv("CLICK_RETENTION_DAYS", 365))
    CRON_SECRET = os.getenv("CRON_SECRET")

    MAX_CONTENT_LENGTH = 7 * 1024
    LIMITE_TAMANHO_URL = 2000

    SESSION_COOKIE_SECURE = (os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true")

    PERMANENT_SESSION_LIFETIME = timedelta(days = 7)

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle" : 280,
    }