# MP Job Saathi

MP Job Saathi is a mobile-first job-discovery and eligibility assistant for Madhya Pradesh opportunities. This repo is intentionally being rebuilt and hardening from a verified baseline; the current state is not a full production system and these status labels reflect reality.

## Phase status

| Phase | Status | Notes |
| --- | --- | --- |
| Phase 1: Government core | Partial, fixture-backed | Eligibility rules pass 122 agent-authored rule cases, not independently reviewed; official-source data and real notice accuracy are not established |
| Phase 2: Government apply assist | Scaffold only | Existing API and checklist surfaces are incomplete and not production-ready |
| Phase 3: Private jobs + job fairs | Scaffold only | Existing catalog data is fixture-only and not verified live sourcing |
| Phase 4: Polish and growth | Scaffold only | Frontend and reminder surfaces are work-package implementation, not a completed product phase |

WP1 is the active eligibility-engine rewrite gate. Its 122-case benchmark passes status and reason-code checks; later WP work remains frozen for review.

## Eligibility diagnostics

VS Code has reported six unresolved-import diagnostics in `backend/tests/test_persistence.py` (`pytest`, Alembic, FastAPI test client, and SQLAlchemy imports) when the selected analysis interpreter does not have the backend dependencies. The backend test run uses the configured Python 3.12 environment and passes; these editor diagnostics are an interpreter/environment mismatch, not six failing tests.

## Real vs stubbed

| Area | Status |
| --- | --- |
| Government notification models | Real, persisted through SQLAlchemy; default data remains fixture-backed |
| Eligibility engine | Real for the configured rules and tests |
| Notification extraction parser | Present, but fixture-driven; no official PDFs downloaded |
| FastAPI API | Real, typed request/response contracts backed by repositories |
| Persistence | SQLAlchemy 2.0 + Alembic; SQLite locally and PostgreSQL in Docker |
| Frontend shell | Present, but not connected to a verified production API; frozen until later WP approval |
| MV3 extension | Present as scaffold only |
| Live crawlers / official verification | Not yet implemented |
| Private-job ATS and job-fair data | Fixture-only |
| Later workflow features | Not production-ready; scaffold or fixture only |

## Quick start

### Docker

```bash
docker compose up --build
```

The backend waits for PostgreSQL, applies migrations, and then starts the API at `http://localhost:8000`. PostgreSQL data is stored in the `postgres_data` volume. Fixture data is not loaded automatically; load it explicitly with `docker compose exec backend python -m app.db.seed`.

### Backend without Docker

Use Python 3.12 for the pinned backend dependencies.

```bash
cd backend
python -m pip install -r requirements.txt
alembic upgrade head
python -m app.db.seed
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Without `DATABASE_URL`, the backend uses `backend/mp_job_saathi.db` (SQLite). To use another database, set `DATABASE_URL` before running Alembic and the app. Set `CORS_ALLOWED_ORIGINS` to a comma-separated list of frontend origins; the default permits local Next.js development origins.

The seed command is explicit and idempotent. Seeded records retain `is_fixture=true` and notifications use `source_kind="fixture"`.

### Frontend

```bash
cd frontend
npm ci
npm run build
```

## Verification

Backend proof command:

```bash
python -m pytest backend/tests -q
```

The suite includes repository tests on in-memory SQLite, API tests on temporary SQLite databases, and an Alembic migration test against an empty database. The application remains fixture-backed unless real source records are added through curated workflows.
