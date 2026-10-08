from __future__ import annotations

from datetime import datetime, timezone

from app.models import GovtNotification, Post, QualificationRule


def _strip_label(raw_line: str, label: str) -> str:
    value = raw_line
    if label in value:
        value = value.split(label, 1)[1]
    if value.startswith(":"):
        value = value[1:]
    return value.strip()


def extract_notification_from_text(raw_text: str) -> GovtNotification:
    """A deterministic parser for the officially published source text. This is intentionally forgiving and meant for fixtures and tests."""
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    advertisement_no = next((line for line in lines if "Advertisement No" in line), "Advert. 01/2026")
    title = next((line for line in lines if "Title" in line), "Junior Engineer")
    last_date = next((line for line in lines if "Last Date" in line), "2026-12-15")
    fee_ur = 200.0
    notification = GovtNotification(
        org="MPESB",
        advertisement_no=_strip_label(advertisement_no, "Advertisement No"),
        title=_strip_label(title, "Title"),
        posts=[
            Post(
                title="Junior Engineer (Civil)",
                vacancies=24,
                qualification_rules=[
                    QualificationRule(level="Diploma", stream="Civil"),
                ],
                age_min=18,
                age_max=40,
                domicile_required=True,
            )
        ],
        total_vacancies=24,
        category_vacancies={"UR": 12, "OBC": 6, "SC": 4, "ST": 2},
        fee_by_category={"UR": fee_ur, "OBC": fee_ur, "SC": 0.0, "ST": 0.0},
        portal_charges=25.0,
        age_limit={"min": 18, "max": 40, "as_on_date": 2026},
        age_relaxation_rules=["Age relaxation as notified in the official PDF; verify before applying."],
        source_urls=["https://esb.mp.gov.in/official-notification"],
        notification_pdf_url="https://esb.mp.gov.in/application/notification.pdf",
        verified_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        verified_by="auto",
        discrepancies=[],
        status="open",
        last_date=_strip_label(last_date, "Last Date"),
    )
    return notification


def get_sample_notifications() -> list[GovtNotification]:
    return [
        extract_notification_from_text(
            """
            Advertisement No: 01/2026
            Title: Junior Engineer (Civil)
            Last Date: 2026-12-15
            """
        ),
        GovtNotification(
            org="MPPSC",
            advertisement_no="02/2026",
            title="State Services Preliminary Exam",
            posts=[
                Post(
                    title="State Services",
                    vacancies=120,
                    qualification_rules=[QualificationRule(level="Graduate")],
                    age_min=21,
                    age_max=40,
                )
            ],
            total_vacancies=120,
            category_vacancies={"UR": 60, "OBC": 30, "SC": 20, "ST": 10},
            fee_by_category={"UR": 500.0, "OBC": 250.0, "SC": 0.0, "ST": 0.0},
            portal_charges=50.0,
            age_limit={"min": 21, "max": 40, "as_on_date": 2026},
            age_relaxation_rules=["As per official notification."],
            source_urls=["https://mppsc.mp.gov.in/advertisement/02-2026"],
            notification_pdf_url="https://mppsc.mp.gov.in/advertisement/02-2026.pdf",
            verified_at="2026-10-08T08:00:00Z",
            verified_by="curator",
            discrepancies=["Aggregator listed 2026-12-19, official value is 2026-12-15."],
            status="open",
            last_date="2026-12-15",
        ),
    ]
