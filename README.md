# MP Job Saathi

MP Job Saathi is a mobile-first job-discovery and eligibility assistant for Madhya Pradesh opportunities. This repo is intentionally being rebuilt and hardening from a verified baseline; the current state is not a full production system and these status labels reflect reality.

## Phase status

| Phase | Status | Notes |
| --- | --- | --- |
| Phase 1: Government core | Partial: models, early eligibility engine, fixtures | Real data model and tests exist, but this is still a fixture-driven implementation rather than a live official-source pipeline |
| Phase 2: Government apply assist | Scaffold only | Browser assist, validation, and pre-submit logic are not yet real or fully integrated |
| Phase 3: Private jobs + job fairs | Scaffold only | Company registry and job data exist as fixtures, not verified live sourcing |
| Phase 4: Polish and growth | Scaffold only | Reminder and growth flows are placeholders and not production-ready |

## Real vs stubbed

| Area | Status |
| --- | --- |
| Government notification models | Real, but fixture-backed |
| Eligibility engine | Real for the configured rules and tests |
| Notification extraction parser | Real, but fixture-driven and not live fetched |
| FastAPI API | Real |
| Frontend shell | Present, but not connected to a verified production API |
| MV3 extension | Present as scaffold only |
| Live crawlers / official verification | Not yet implemented |
| Private-job ATS and job-fair data | Fixture-only |
| Phase 3 and 4 features | Not production-ready; scaffold or fixture only |

## Docker / local setup note

The repository currently includes a `docker-compose.yml` that starts PostgreSQL while the backend is configured for SQLite. This mismatch is acknowledged and documented here for now. It is not yet fixed in this Work Package.

## Quick start

### Backend

```bash
cd backend
python -m pip install -r requirements.txt
python -m pytest tests -q
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm ci
npm run build
```

## Verification

Current measured backend proof command:

```bash
python -m pytest backend/tests -q
```

Current result from the repo at this revision:

```text
18 passed, 1 warning in 1.46s
```

This is a verified fixture-backed baseline, not a claim of full production deployment.
