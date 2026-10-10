from __future__ import annotations

from sqlalchemy import func, select

from app.db.database import SessionLocal
from app.db.orm import NotificationRecord
from app.db.repositories import CatalogRepository, NotificationRepository
from app.ingestion.mp_sources import get_sample_notifications
from app.ingestion.private_jobs import get_company_registry, get_job_fair_calendar, get_private_job_fixtures
from app.models import GovtNotification


def seed() -> int:
    with SessionLocal() as session:
        existing = session.scalar(select(func.count()).select_from(NotificationRecord)) or 0
        if existing:
            print(f"Database already has {existing} notifications; seed skipped.")
            return 0

        notifications = [
            notification.model_copy(update={"source_kind": "fixture", "verified_at": None, "verified_by": "auto"})
            for notification in get_sample_notifications()
        ]
        notification_repository = NotificationRepository(session)
        for notification in notifications:
            notification_repository.create(notification)

        catalog = CatalogRepository(session)
        for company in get_company_registry():
            catalog.add_company(company.model_copy(update={"is_fixture": True}))
        for job in get_private_job_fixtures():
            catalog.add_private_job(job.model_copy(update={"is_fixture": True}))
        for fair in get_job_fair_calendar():
            catalog.add_job_fair(fair.model_copy(update={"is_fixture": True}))
        catalog.add_source_policy("fixture", {"allow_network_fetch": False, "label": "Local fixture data only"})
        session.commit()

        print(
            f"Seeded {len(notifications)} fixture notifications, "
            f"{len(get_company_registry())} companies, "
            f"{len(get_private_job_fixtures())} private jobs, and "
            f"{len(get_job_fair_calendar())} job fairs."
        )
        return len(notifications)


if __name__ == "__main__":
    seed()
