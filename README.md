# MP Job Saathi

MP Job Saathi is a mobile-first job discovery and eligibility assistant for Madhya Pradesh government and private opportunities. The project is intentionally designed in phased delivery, with the first working slice focused on the government core: official-source-first listings, extraction, fee logic, eligibility checks, and alert-ready feed data.

## Phase status

| Phase | Status | Notes |
| --- | --- | --- |
| Phase 1: Government core | ✅ Working slice implemented | Source model, extraction, eligibility engine, feed, API, tests |
| Phase 2: Government apply assist | 🚧 Planned | Browser extension and MPOnline field-mapping workflow |
| Phase 3: Private jobs + job fairs | 🚧 Planned | ATS matching, scam scoring, job-fair registry |
| Phase 4: Polish and growth | 🚧 Planned | Tracker, reminders, share cards, WhatsApp growth |

## What is real vs stubbed

| Area | Status |
| --- | --- |
| Official-source data model | Real |
| Notification extraction logic | Real (fixture-driven parser) |
| Eligibility engine | Real |
| FastAPI API | Real |
| Frontend PWA shell | Scaffolded |
| Chrome extension | Scaffolded |
| Live crawlers | Not yet enabled; fixtures only |

## Quick start

### Backend

```bash
cd backend
python -m pip install -r requirements.txt
python -m pytest tests/test_phase1.py -q
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open:

- Health: http://localhost:8000/health
- Notifications: http://localhost:8000/notifications

## Verification

The phase-1 proof command is:

```bash
python -m pytest backend/tests/test_phase1.py -q
```

It currently passes with 6 tests in the repository.
