import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

APP_ENV = os.getenv("APP_ENV", "development")
APP_NAME = os.getenv("APP_NAME", "MP Job Saathi")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mp_job_saathi.db")
CORS_ALLOWED_ORIGINS = tuple(
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
EXTRACTION_CONFIDENCE_THRESHOLD = float(os.getenv("EXTRACTION_CONFIDENCE_THRESHOLD", "0.7"))

__all__ = [
    "APP_ENV",
    "APP_NAME",
    "DATABASE_URL",
    "CORS_ALLOWED_ORIGINS",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL",
    "EXTRACTION_CONFIDENCE_THRESHOLD",
    "BASE_DIR",
]
