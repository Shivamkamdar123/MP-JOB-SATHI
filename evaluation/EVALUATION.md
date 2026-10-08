# MP Job Saathi Evaluation

## Phase 1 summary

This repository includes the working phase-1 government slice and the measured proof command below.

- Verified command: `python -m pytest backend/tests/test_phase1.py -q`
- Result: 6 passed in 0.40s
- Coverage: extraction, eligibility matching, fee logic, and feed ranking

## Findings

- Official-source-first data model is in place and designed to store the official PDF/URL and verification timestamps.
- Eligibility matches for age, qualification, and domicile requirements are tested on synthetic profiles.
- Alert and feed ranking are ready to expand to Telegram and digest scheduling.

## Planned follow-up

- Add fixture-based PDF parsing with OCR fallback using Tesseract.
- Add a real curator review console.
- Expand the benchmark to 30+ labeled notifications and 100+ profile-post cases.
