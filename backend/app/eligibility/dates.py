from __future__ import annotations

import re
from datetime import date, datetime


DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d")


def parse_date(value: str | int | date | datetime | None) -> tuple[date | None, bool]:
    if value is None:
        return None, False
    if isinstance(value, datetime):
        return value.date(), False
    if isinstance(value, date):
        return value, False
    if isinstance(value, int):
        text = str(value)
        if re.fullmatch(r"\d{4}", text):
            return None, True
        return None, False

    text = str(value).strip()
    if not text:
        return None, False
    if re.fullmatch(r"\d{4}", text):
        return None, True

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date(), False
        except ValueError:
            continue
    return None, False


def age_on_date(date_of_birth: str, as_on_date: str | int | None) -> int:
    dob, _ = parse_date(date_of_birth)
    if dob is None:
        raise ValueError("Date of birth is invalid or missing.")

    ref_date, is_year_only = parse_date(as_on_date)
    if ref_date is None:
        if is_year_only:
            raise ValueError("Age limit as-on date is ambiguous because only a year was provided; verify the official notification.")
        raise ValueError("Age limit as-on date is invalid or missing.")

    age = ref_date.year - dob.year - ((ref_date.month, ref_date.day) < (dob.month, dob.day))
    return age


def format_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%d/%m/%Y")


def days_left(notification: object, today: str | date | None) -> int | None:
    if getattr(notification, "last_date", None) in (None, ""):
        return None
    ref_date, is_year_only = parse_date(getattr(notification, "last_date"))
    if ref_date is None:
        return None
    parsed_today, _ = parse_date(today if today is not None else date.today())
    if parsed_today is None:
        parsed_today = date.today()
    return (ref_date - parsed_today).days


def is_closing_soon(notification: object, today: str | date | None = None) -> bool:
    delta = days_left(notification, today)
    return delta is not None and delta <= 7
