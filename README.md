# MP Job Saathi

MP Job Saathi is a mobile-first job discovery and eligibility assistant for Madhya Pradesh government and private opportunities. The project is intentionally designed in phased delivery, with the first working slice focused on the government core: official-source-first listings, extraction, fee logic, eligibility checks, and alert-ready feed data.

## Phase status

| Phase | Status | Notes |
| --- | --- | --- |
| Phase 1: Government core | ✅ Working slice implemented | Source model, extraction, eligibility engine, feed, API, tests |
| Phase 2: Government apply assist | ✅ Working assist slice implemented | Pre-fill map, document validation, pre-submit checklist |
| Phase 3: Private jobs + job fairs | ✅ Working phase implemented | Company registry, private job matcher, scam-risk logic, job-fair fixtures |
| Phase 4: Polish and growth | ✅ Working tracker and reminder layer | Application tracker, admit-card/result reminders, share card, admin snapshot |

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
python -m pytest tests -q
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open:

- Health: http://localhost:8000/health
- Notifications: http://localhost:8000/notifications
- Prefill assist: POST /assist/prefill
- Document validation: POST /assist/validate-document
- Pre-submit checklist: POST /assist/pre-submit-checklist
- Private jobs ranking: POST /private-jobs/match
- Applications tracker: POST /applications
- Reminder feed: POST /applications/reminders
- Share card: POST /share-card
- Admin snapshot: POST /admin/snapshot

## Verification

The current proof command is:

```bash
python -m pytest backend/tests -q
```

This repository currently passes all implemented phases (1 through 4) with 18 passing tests.
