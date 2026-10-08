import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

APP_ENV = os.getenv("APP_ENV", "development")
APP_NAME = os.getenv("APP_NAME", "MP Job Saathi")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mp_job_saathi.db")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

__all__ = [
    "APP_ENV",
    "APP_NAME",
    "DATABASE_URL",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "ANTHROPIC_API_KEY",
    "BASE_DIR",
]
