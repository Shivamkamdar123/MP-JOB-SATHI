from __future__ import annotations

from app.core.config import DATABASE_URL


def get_database_url() -> str:
    return DATABASE_URL
