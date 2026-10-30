from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.db.database import create_database_engine, get_session
from app.db.orm import AuditEventRecord, Base
from app.db.repositories import NotificationRepository
from app.eligibility.engine import compute_effective_status, evaluate_eligibility, get_for_you_feed
from app.main import app
from app.models import FieldProvenance, GovtNotification, Post, UserProfile


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_database_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        yield session
    engine.dispose()


def _sample_notification(
    title: str = "Assistant Engineer",
    review_required: bool = True,
    last_date: str | None = "2026-11-15",
    source_kind: str = "official",
    status: str | None = None,
) -> GovtNotification:
    return GovtNotification(
        title=title,
        org="MPPSC",
        advertisement_no="01/2026",
        total_vacancies=10,
        opens_date="2026-10-01",
        last_date=last_date,
        source_kind=source_kind,
        review_required=review_required,
        status=status,
        age_limit={"min": 21, "max": 40, "as_on": "2026-01-01"},
        fee_by_category={"UR": 500, "SC": 250},
        portal_charges=40,
        posts=[
            Post(
                title=f"{title} Civil",
                vacancies=10,
                qualification_rules=[
                    {
                        "level": "Graduate",
                        "stream": "Civil",
                        "mandatory": True,
                    }
                ],
            )
        ],
    )


def _sample_profile() -> UserProfile:
    return UserProfile(
        name="Candidate Name",
        date_of_birth="2000-05-15",
        gender="male",
        category="UR",
        mp_domicile=True,
        qualifications=[
            {
                "level": "Graduate",
                "stream": "Civil",
                "year": 2022,
                "percentage": 75.0,
            }
        ],
    )


def test_extracted_notice_reaches_eligible_after_verification(db_session: Session) -> None:
    repo = NotificationRepository(db_session)
    profile = _sample_profile()
    unverified_notice = _sample_notification(review_required=True)

    record = repo.add_extracted(unverified_notice, actor="extractor")
    loaded = repo.get(record.id)
    assert loaded is not None
    assert loaded.review_required is True

    # Pre-verification: eligibility must be capped to needs_check
    result_before = evaluate_eligibility(loaded, profile)
    assert result_before.status == "needs_check"
    assert any(r.check == "verification" for r in result_before.reasons)

    # Curator verifies the notice
    verified = repo.verify(record.id, actor="curator", source_url="https://mppsc.mp.gov.in/advt01.pdf")
    assert verified is not None
    assert verified.verified_by == "curator"
    assert verified.review_required is False

    # Check persistence: review_required must be False in both DB record data and loaded model
    reloaded = repo.get(record.id)
    assert reloaded is not None
    assert reloaded.review_required is False

    # Post-verification: fully matching profile reaches eligible
    result_after = evaluate_eligibility(reloaded, profile)
    assert result_after.status == "eligible"
    assert not any(r.check == "verification" for r in result_after.reasons)

    # In feed: verified item appears as eligible
    feed_items = get_for_you_feed(profile, [reloaded], notification_ids={id(reloaded): record.id}, today="2026-10-10")
    assert len(feed_items) == 1
    assert feed_items[0]["status"] == "eligible"
    assert feed_items[0]["verification_status"] == "verified"
    assert feed_items[0]["review_required"] is False


def test_feed_skips_past_deadline_notices_and_computes_effective_status() -> None:
    profile = _sample_profile()
    today = "2026-10-10"

    expired = _sample_notification(title="Expired Notice", last_date="2026-10-09", review_required=False)
    closing_soon = _sample_notification(title="Closing Soon Notice", last_date="2026-10-15", review_required=False)
    open_notice = _sample_notification(title="Open Notice", last_date="2026-11-15", review_required=False)
    closed_by_status = _sample_notification(title="Explicitly Closed", last_date="2026-11-15", status="closed", review_required=False)

    feed = get_for_you_feed(profile, [expired, closing_soon, open_notice, closed_by_status], today=today)

    titles = [item["notification"] for item in feed]
    assert "Expired Notice" not in titles, "Expired notice (last_date < today) must be excluded from feed"
    assert "Explicitly Closed" not in titles, "Notice with status='closed' must be excluded from feed"
    assert "Closing Soon Notice" in titles
    assert "Open Notice" in titles

    closing_item = next(item for item in feed if item["notification"] == "Closing Soon Notice")
    assert closing_item["days_left"] == 5
    assert closing_item.get("effective_status") == "closing_soon"

    open_item = next(item for item in feed if item["notification"] == "Open Notice")
    assert open_item["days_left"] == 36
    assert open_item.get("effective_status") == "open"


def test_compute_effective_status_helper() -> None:
    today = "2026-10-10"

    notice_closed = _sample_notification(status="closed", last_date="2026-11-01")
    assert compute_effective_status(notice_closed, today) == "closed"

    notice_past = _sample_notification(last_date="2026-10-08")
    assert compute_effective_status(notice_past, today) == "closed"

    notice_soon = _sample_notification(last_date="2026-10-17")
    assert compute_effective_status(notice_soon, today) == "closing_soon"

    notice_open = _sample_notification(last_date="2026-10-25")
    assert compute_effective_status(notice_open, today) == "open"

    notice_no_date = _sample_notification(last_date=None)
    assert compute_effective_status(notice_no_date, today) == "open"


def test_show_fixtures_filtering_in_repository(db_session: Session) -> None:
    repo = NotificationRepository(db_session)
    fixture_notice = _sample_notification(title="Fixture Job", source_kind="fixture")
    official_notice = _sample_notification(title="Official Job", source_kind="official")

    repo.create(fixture_notice)
    repo.create(official_notice)

    all_items = repo.list(include_fixtures=True)
    assert len(all_items) == 2

    prod_items = repo.list(include_fixtures=False)
    assert len(prod_items) == 1
    assert prod_items[0].title == "Official Job"
    assert prod_items[0].source_kind == "official"

    all_with_ids = repo.list_with_ids(include_fixtures=True)
    assert len(all_with_ids) == 2

    prod_with_ids = repo.list_with_ids(include_fixtures=False)
    assert len(prod_with_ids) == 1
    assert prod_with_ids[0][1].title == "Official Job"


def test_curator_edit_preserves_verified_status(db_session: Session) -> None:
    repo = NotificationRepository(db_session)
    notice = _sample_notification(title="Initial Title", review_required=True)
    record = repo.add_extracted(notice, actor="extractor")

    # Verify first
    verified = repo.verify(record.id, actor="curator", source_url="https://official.mp.gov.in/notice.pdf")
    assert verified is not None
    assert verified.verified_by == "curator"
    assert verified.review_required is False
    verified_at_1 = verified.verified_at

    # Edit title via curator_edit
    updated = repo.curator_edit(record.id, {"title": "Updated Official Title"}, actor="curator")
    assert updated is not None
    assert updated.title == "Updated Official Title"
    assert updated.verified_by == "curator"
    assert updated.review_required is False
    assert updated.source_kind == "official"
    assert updated.verified_at is not None
    assert updated.verified_at >= verified_at_1

    # Reload and assert DB record state
    reloaded = repo.get(record.id)
    assert reloaded is not None
    assert reloaded.title == "Updated Official Title"
    assert reloaded.verified_by == "curator"
    assert reloaded.review_required is False

