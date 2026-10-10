from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.database import create_database_engine, get_session
from app.db.orm import AuditEventRecord, Base, FieldProvenanceRecord
from app.db.repositories import NotificationRepository
from app.ingestion.mp_sources import get_sample_notifications
from app.main import app


@pytest.fixture
def database_session() -> Generator[Session, None, None]:
    test_engine = create_database_engine("sqlite:///:memory:")
    Base.metadata.create_all(test_engine)
    factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    with factory() as session:
        yield session
    test_engine.dispose()


def test_notification_repository_persists_posts_provenance_and_audit(database_session: Session) -> None:
    notification = get_sample_notifications()[0]
    repository = NotificationRepository(database_session)
    record = repository.add_extracted(notification, actor="test-extractor")

    loaded = repository.get(record.id)
    assert loaded is not None
    assert loaded.title == notification.title
    assert loaded.source_kind == "fixture"
    assert loaded.verified_by == "auto"
    assert loaded.verified_at is None
    assert len(loaded.posts) == len(notification.posts)
    assert database_session.scalar(select(AuditEventRecord).where(AuditEventRecord.event_type == "extraction")) is not None
    assert database_session.scalar(select(FieldProvenanceRecord).where(FieldProvenanceRecord.notification_id == record.id)) is not None

    verified_before = datetime.now(timezone.utc)
    verified = repository.verify(record.id, actor="reviewer", source_url="https://example.gov/notification")
    verified_after = datetime.now(timezone.utc)
    assert verified is not None
    assert verified.source_kind == "official"
    assert verified.verified_by == "curator"
    assert verified.verified_at is not None
    verified_at = datetime.fromisoformat(verified.verified_at)
    assert verified_before <= verified_at <= verified_after
    updated = repository.curator_edit(record.id, {"title": "Curated title"}, actor="curator-1")
    assert updated is not None
    assert updated.title == "Curated title"
    assert [event.event_type for event in database_session.scalars(select(AuditEventRecord).order_by(AuditEventRecord.id))] == [
        "extraction",
        "verification",
        "curator_edit",
    ]


def test_api_uses_temp_database_and_returns_typed_errors(tmp_path: Path) -> None:
    test_engine = create_database_engine(f"sqlite:///{(tmp_path / 'api.db').as_posix()}")
    Base.metadata.create_all(test_engine)
    factory = sessionmaker(bind=test_engine, expire_on_commit=False)

    def override_session() -> Generator[Session, None, None]:
        with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        with factory() as session:
            notification = get_sample_notifications()[0]
            record = NotificationRepository(session).create(notification)
            session.commit()
            notification_id = record.id

        client = TestClient(app)
        listing = client.get("/notifications")
        assert listing.status_code == 200
        assert listing.json()["items"][0]["title"] == notification.title

        profile = {
            "name": "Amit Verma",
            "date_of_birth": "2001-08-12",
            "gender": "male",
            "category": "OBC",
            "mp_domicile": True,
            "qualifications": [{"level": "Diploma", "stream": "Civil", "percentage": 82.5}],
        }
        check = client.post("/eligibility/check", json={"notification_id": notification_id, "profile": profile})
        assert check.status_code == 200
        assert check.json()["status"] == "eligible"

        missing = client.post("/eligibility/check", json={"notification_id": 9999, "profile": profile})
        assert missing.status_code == 404
        invalid = client.post("/eligibility/check", json={"notification_id": "bad", "profile": profile})
        assert invalid.status_code == 422

        saved_profile = client.post("/profiles", json={"profile": profile, "email": "candidate@example.test"})
        assert saved_profile.status_code == 201
        user_id = saved_profile.json()["user_id"]

        created = client.post("/applications", json={
            "job_title": "Junior Engineer",
            "organization": "MPESB",
            "stage": "saved",
            "user_id": user_id,
            "notification_id": notification_id,
        })
        assert created.status_code == 201
        application_id = created.json()["id"]
        reloaded = client.get("/applications")
        assert reloaded.status_code == 200
        assert reloaded.json()["items"][0]["id"] == application_id

        reminders = client.post("/applications/reminders", json={
            "deadline": "2026-12-15",
            "user_id": user_id,
            "application_id": application_id,
        })
        assert reminders.status_code == 201
        assert reminders.json()["items"][0]["date"] == "2026-12-15"

        extracted = client.post("/notifications/extract", json={
            "raw_text": "Advertisement No: 14/2026\nTitle: Extracted Post\nLast Date: 2026-12-15",
            "actor": "api-test",
        })
        assert extracted.status_code == 201
        extracted_id = extracted.json()["id"]
        verified = client.post(f"/notifications/{extracted_id}/verify", json={"actor": "reviewer"})
        assert verified.status_code == 200
        edited = client.patch(f"/notifications/{extracted_id}", json={
            "actor": "curator",
            "changes": {"title": "Updated extracted post"},
        })
        assert edited.status_code == 200
        assert edited.json()["notification"]["title"] == "Updated extracted post"
        events = client.get("/audit-events")
        assert [item["event_type"] for item in events.json()["items"]] == ["extraction", "verification", "curator_edit"]
    finally:
        app.dependency_overrides.clear()
        test_engine.dispose()


def test_initial_migration_applies_to_empty_sqlite_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database_file = tmp_path / "empty.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_file.as_posix()}")
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))

    command.upgrade(config, "head")

    migrated_engine = create_database_engine(f"sqlite:///{database_file.as_posix()}")
    try:
        table_names = set(inspect(migrated_engine).get_table_names())
    finally:
        migrated_engine.dispose()
    assert {
        "notifications",
        "posts",
        "field_provenance",
        "users",
        "profiles",
        "applications",
        "reminders",
        "audit_events",
        "company_sources",
        "private_jobs",
        "job_fairs",
        "source_policies",
        "curator_queue",
    } <= table_names


def test_sqlite_records_survive_engine_recreation(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'restart.db').as_posix()}"
    first_engine = create_database_engine(database_url)
    Base.metadata.create_all(first_engine)
    first_factory = sessionmaker(bind=first_engine, expire_on_commit=False)
    with first_factory() as session:
        record = NotificationRepository(session).create(get_sample_notifications()[0])
        session.commit()
        notification_id = record.id
    first_engine.dispose()

    second_engine = create_database_engine(database_url)
    second_factory = sessionmaker(bind=second_engine, expire_on_commit=False)
    with second_factory() as session:
        loaded = NotificationRepository(session).get(notification_id)
        assert loaded is not None
        assert loaded.title == "Junior Engineer (Civil)"
    second_engine.dispose()
