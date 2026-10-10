from __future__ import annotations

import hashlib
import json
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.database import create_database_engine, get_session
from app.db.orm import Base, CuratorQueueRecord, FieldProvenanceRecord
from app.assist.form_assist import build_pre_submit_checklist
from app.ingestion import notification_ingest
from app.ingestion.mp_sources import compare_sources, extract_notification_from_text
from app.ingestion.pdf_extract import ExtractedPDF
from app.ingestion.source_policy import SourcePolicy
from app.ingestion import structured_extract
from app.main import app
from app.models import GovtNotification


def test_source_policy_checks_robots_allowlist_and_host_delay() -> None:
    current = [0.0]
    sleeps: list[float] = []

    def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        current[0] += seconds

    policy = SourcePolicy(
        allowlist={"esb.mp.gov.in"},
        min_delay_seconds=3,
        robots_fetcher=lambda _: "User-agent: *\nAllow: /",
        clock=lambda: current[0],
        sleeper=sleep,
    )
    calls: list[str] = []
    fetcher = lambda url: calls.append(url) or b"content"

    assert policy.fetch("https://esb.mp.gov.in/notices", fetcher) == b"content"
    assert policy.fetch("https://esb.mp.gov.in/notices/2", fetcher) == b"content"
    assert sleeps == [3]
    assert len(calls) == 2
    with pytest.raises(PermissionError):
        policy.fetch("https://mppsc.mp.gov.in/notice.pdf", fetcher)


def test_source_policy_fails_closed_for_robots_disallow_or_unknown() -> None:
    disallowed = SourcePolicy(robots_fetcher=lambda _: "User-agent: *\nDisallow: /")
    unknown = SourcePolicy(robots_fetcher=lambda _: None)
    with pytest.raises(PermissionError, match="robots.txt"):
        disallowed.check("https://esb.mp.gov.in/notice.pdf")
    with pytest.raises(PermissionError, match="robots.txt"):
        unknown.check("https://esb.mp.gov.in/notice.pdf")


def test_compare_sources_records_lead_date_and_fee_conflicts() -> None:
    official = GovtNotification(
        org="Board",
        title="Notice",
        last_date="2026-10-20",
        fee_by_category={"UR": 200.0},
        source_kind="official",
    )
    lead = GovtNotification(
        org="Board",
        title="Notice",
        last_date="2026-10-22",
        fee_by_category={"UR": 250.0},
        source_kind="lead",
    )

    compared = compare_sources(official, lead)

    assert any("last_date differs" in item for item in compared.discrepancies)
    assert any("fee_by_category differs" in item for item in compared.discrepancies)
    with pytest.raises(ValueError, match="source_kind='lead'"):
        compare_sources(official, official)


def test_checklist_handles_missing_fee_without_inventing_a_total() -> None:
    notification = GovtNotification(title="Notice", source_kind="official")
    profile = {
        "name": "Candidate",
        "date_of_birth": "2000-01-01",
        "gender": "female",
    }
    from app.models import UserProfile

    items = build_pre_submit_checklist(UserProfile.model_validate(profile), notification)
    assert items[0]["status"] == "pending"
    assert "verify the fee table" in items[0]["message"]


def test_stubbed_pdf_ingest_persists_hash_then_returns_notification_to_feed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_database_engine(f"sqlite:///{(tmp_path / 'pipeline.db').as_posix()}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session() -> Generator[Session, None, None]:
        with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    extraction_calls: list[bytes] = []
    monkeypatch.setattr(
        notification_ingest,
        "extract_pdf",
        lambda content: extraction_calls.append(content) or ExtractedPDF(
            pages=["Title: Test notice"],
            tables=[],
            ocr_skipped_pages=[],
        ),
    )
    policy = SourcePolicy(
        allowlist={"esb.mp.gov.in"},
        min_delay_seconds=0,
        robots_fetcher=lambda _: "User-agent: *\nAllow: /",
    )
    responses = {
        "https://esb.mp.gov.in/list": b"listing-v1",
        "https://esb.mp.gov.in/notice.pdf": b"pdf-bytes-v1",
    }
    fetcher = lambda url: responses[url]

    try:
        with factory() as session:
            notification_id, notification, changed = notification_ingest.ingest_pdf_url(
                session,
                "https://esb.mp.gov.in/notice.pdf",
                "https://esb.mp.gov.in/list",
                policy,
                fetcher,
            )
            assert changed is True
            assert notification.title == "Test notice"
            assert notification.org is None
            title_provenance = session.scalar(select(FieldProvenanceRecord).where(
                FieldProvenanceRecord.notification_id == notification_id,
                FieldProvenanceRecord.field_name == "title",
            ))
            assert title_provenance is not None
            assert title_provenance.source_page == 1
            assert title_provenance.confidence == 0.9
            assert title_provenance.method == "regex"
            assert session.scalar(select(CuratorQueueRecord).where(
                CuratorQueueRecord.notification_id == notification_id,
            )) is not None

        with factory() as session:
            cached_id, _, changed = notification_ingest.ingest_pdf_url(
                session,
                "https://esb.mp.gov.in/notice.pdf",
                "https://esb.mp.gov.in/list",
                policy,
                fetcher,
            )
            assert cached_id == notification_id
            assert changed is False
        assert len(extraction_calls) == 1

        with TestClient(app) as client:
            response = client.post("/feed", json={
                "profile": {
                    "name": "Test Candidate",
                    "date_of_birth": "2000-01-01",
                    "gender": "female",
                }
            })
        assert response.status_code == 200
        item = response.json()["items"][0]
        assert item["id"] == notification_id
        assert item["notification"] == "Test notice"
        assert item["review_required"] is True
        assert item["verification_notice"] == "Auto-extracted, verify before applying."
        assert item["verification_status"] == "auto"
        with TestClient(app) as client:
            detail = client.get(f"/notifications/{notification_id}")
            stats = client.get("/stats")
        assert detail.status_code == 200
        assert detail.json()["notification"]["title"] == "Test notice"
        assert stats.status_code == 200
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_text_extraction_has_zero_confidence_for_absent_fields() -> None:
    notification = extract_notification_from_text("Title: Test notice")
    assert notification.field_provenance["org"].confidence == 0
    assert notification.field_provenance["org"].source_page is None
    assert notification.field_provenance["title"].confidence > 0


def test_regex_and_table_fallback_extract_only_evidenced_values() -> None:
    from app.ingestion.mp_sources import extract_notification_from_text

    labeled = extract_notification_from_text(
        "[PAGE 2]\nTotal vacancies: 42\nPortal fee: Rs. 25\nLast Date: 2026-12-20"
    )
    assert labeled.total_vacancies == 42
    assert labeled.portal_charges == 25
    assert labeled.field_provenance["total_vacancies"].source_page == 2

    table = [
        ["Post Name", "Vacancies", "UR", "OBC"],
        ["Assistant Clerk", "12", "6", "4"],
    ]
    fee_table = [["Category", "Application Fee"], ["UR", "200"], ["OBC", "100"]]
    from app.ingestion.structured_extract import extract_structured

    notification = extract_structured([], [(3, table), (4, fee_table)])
    assert len(notification.posts) == 1
    assert notification.posts[0].title == "Assistant Clerk"
    assert notification.posts[0].vacancies == 12
    assert notification.posts[0].field_provenance["title"].source_page == 3
    assert notification.total_vacancies == 12
    assert notification.fee_by_category == {"UR": 200.0, "OBC": 100.0}
    assert notification.field_provenance["fee_by_category"].method == "table"


def test_anthropic_json_response_retries_once_and_marks_llm_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("CI", raising=False)
    responses = iter([
        "not json",
        '{"title":"LLM notice","field_provenance":{"title":{"source_page":1,"snippet":"Title: LLM notice","confidence":0.95,"method":"regex"}}}',
    ])
    calls: list[int] = []

    def fake_api_response(*args: object) -> str:
        calls.append(1)
        return next(responses)

    monkeypatch.setattr(structured_extract, "_api_response", fake_api_response)
    notification = structured_extract.extract_structured(["Title: LLM notice"])

    assert len(calls) == 2
    assert notification.title == "LLM notice"
    assert notification.field_provenance["title"].method == "llm"


def test_ci_uses_only_recorded_model_responses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("CI", "true")
    monkeypatch.setattr(
        structured_extract,
        "_api_response",
        lambda *_: pytest.fail("CI must not make a live Anthropic API call"),
    )
    notification = structured_extract.extract_structured(["Title: CI fallback"])
    assert notification.title == "CI fallback"


def test_ci_replays_recorded_model_response(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("CI", "true")
    input_text = "[PAGE 1]\nTitle: Recorded notice\n\n"
    digest = hashlib.sha256(input_text.encode("utf-8")).hexdigest()
    fixture_path = tmp_path / "model-responses.json"
    fixture_path.write_text(json.dumps({digest: json.dumps({
        "title": "Recorded notice",
        "field_provenance": {
            "title": {
                "source_page": 1,
                "snippet": "Title: Recorded notice",
                "confidence": 0.95,
                "method": "llm",
            }
        },
    })}), encoding="utf-8")
    monkeypatch.setenv("MODEL_RESPONSE_FIXTURES", str(fixture_path))
    monkeypatch.setattr(
        structured_extract,
        "_api_response",
        lambda *_: pytest.fail("CI must not make a live Anthropic API call"),
    )

    notification = structured_extract.extract_structured(["Title: Recorded notice"])
    assert notification.title == "Recorded notice"
    assert notification.field_provenance["title"].method == "llm"


def test_llm_value_without_verifiable_snippet_is_discarded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr(
        structured_extract,
        "_api_response",
        lambda *_: '{"title":"Invented","field_provenance":{"title":{"source_page":1,"snippet":"Not in the notice","confidence":1,"method":"llm"}}}',
    )
    notification = structured_extract.extract_structured(["Title: Supported notice"])
    assert notification.title is None