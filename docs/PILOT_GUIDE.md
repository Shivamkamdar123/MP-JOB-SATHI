# MP Job Saathi: Pilot Delivery Guide

* For the Antigravity agent and the project owner. Based on a read-through of the repository as uploaded; nothing was executed, so every 'verify' step below is a real step, not a formality.*

---

## 1. Mission and definition of done

**Goal:** a small-scale live pilot (up to about 100 users) that shows Madhya Pradesh government recruitment notices (MPPSC and MPESB only) truthfully, with eligibility, fee and deadline guidance a user can rely on.

**Pilot model:** software extracts, the owner verifies, users see 'Eligible' only on verified notices. This is a human-in-the-loop pipeline, not full automation.

**In scope for the pilot**

- Govt feed, job detail, eligibility, fee, pre-submit checklist, English and Hindi UI, offline saved jobs.
- Admin/curator tooling to turn a PDF into a verified notice.
- Authenticated admin routes, server-side consent, deletion, deployment, backups.

**Out of scope (explicitly deferred)**

- Private jobs and job fairs (fixtures only, no ingestion).
- Browser extension (cannot work as designed, see D5).
- Tracker, admin dashboards, share cards, native apps, payments.

**The pilot is done when every Gate in section 4 is ticked and the Go/No-Go list in section 9 passes.**

---

## 2. Operating contract for the agent

Copy this section into `AGENTS.md` at the repo root (or your Antigravity workspace rules, if your version supports them).

1. **Checklist first, code second.** Before each work package (WP), write a plan listing files to touch and tests to add. Wait for owner approval on any item marked DECISION.
2. **Never invent recruitment facts.** No made-up dates, fees, ages or qualifications in code, tests, fixtures or docs. Every fact needs a source PDF and page. This rule already exists in the extractor; keep it.
3. **Tests before claims.** A task is done only when: new tests pass, the full suite passes, and the acceptance criteria in this guide are met. Report exact command output, never 'should work'.
4. **Small changes.** One WP per branch, one concern per commit, conventional commit messages (`fix(fee): ...`).
5. **Do not weaken tests to pass.** If a test must change, state why in the commit and flag it for owner review. The 122 eligibility cases encode policy; changing them is a DECISION.
6. **Keep docs honest.** Update `README.md` phase table, `docs/STATUS.md` and the evaluation report in the same PR as the behavior change.
7. **Secrets.** Never commit keys. Use `.env`; update `.env.example` for any new variable.
8. **Migrations.** Any schema change gets an Alembic migration and a test that it applies to an empty SQLite DB (pattern exists in `test_persistence.py`).
9. **Stop conditions.** If blocked, or a fix would need a product/legal decision, stop and ask. Do not guess.

**Verification commands (run all before every PR)**

```
python -m pytest backend/tests -q
cd frontend && npx tsc --noEmit && npm run lint && npm test && npm run build
python evaluation/eligibility_benchmark.py
python evaluation/extraction_benchmark.py
```

---

## 3. Starting state (honest snapshot)

- Backend: FastAPI, SQLAlchemy 2, Alembic, Postgres in Docker. Last recorded run: 167 tests passed (Oct 10).
- Eligibility engine: 122 of 122 cases pass, but the cases are agent-written, so they measure self-consistency, not real-notice accuracy.
- Extraction: **0% recall on all 9 fields across 3 labeled PDFs** (23 failures in `evaluation/results/extraction.json`).
- Frontend: feed, detail, checklist, onboarding, stats, bilingual UI, service worker. Hindi is machine-translated.
- Auth: none. Reminders, tracker, private jobs, extension: stubs or fixtures.
- Docs: partly stale (`EVALUATION.md` dated Oct 10, `pdfs/README.md` says N=0).

---

## 4. Master checklist (tick as you go)

### Gate 0: Baseline

- [ ] 0.1 Clean checkout runs all verification commands; results recorded in `docs/STATUS.md`
- [ ] 0.2 `AGENTS.md` added from section 2
- [ ] 0.3 Branch strategy: `main` protected, work on `pilot/*` branches
- [ ] 0.4 Stale docs corrected (D9)

### Gate 1: Correctness of what users see

- [ ] 1.1 Verified notices can reach 'Eligible' (D3)
- [ ] 1.2 Expired notices never appear in the feed (D10)
- [ ] 1.3 Fee works for real grouped fee tables (D2)
- [ ] 1.4 Fixture data hidden in production (D11)
- [ ] 1.5 Stream/qualification matching no longer causes false 'not eligible' (D8)

### Gate 2: Data truth

- [ ] 2.1 Root cause of 0% extraction identified and written down (D1)
- [ ] 2.2 At least 10 official advertisements hand-labeled
- [ ] 2.3 Extraction metrics recorded; target per field in WP3
- [ ] 2.4 Curator queue endpoints and admin editing flow working (D4)
- [ ] 2.5 Owner can take a PDF to a verified notice in 15 minutes or less

### Gate 3: Security and privacy

- [ ] 3.1 All mutating and admin routes require an admin credential (D6)
- [ ] 3.2 Consent stored server-side with timestamp and version
- [ ] 3.3 Delete-my-data endpoint and privacy notice page
- [ ] 3.4 Rate limiting, no profile data in logs
- [ ] 3.5 Legal/DPDP review by a qualified person (not agent-done)

### Gate 4: Deployment

- [ ] 4.1 One-command production deploy, HTTPS, env-based config
- [ ] 4.2 `/stats` works in the container (D7)
- [ ] 4.3 Automated daily DB backup and a tested restore
- [ ] 4.4 Health check and uptime alert

### Gate 5: Product readiness

- [ ] 5.1 Hindi UI reviewed by a fluent speaker
- [ ] 5.2 'Last verified on' date and 'report an error' link on every notice
- [ ] 5.3 Mobile and offline smoke test on a real low-end phone
- [ ] 5.4 Pilot feedback channel (Telegram or WhatsApp group)

---

## 5. Defect register

| ID | Severity | Problem | Where | Fix in |
| --- | --- | --- | --- | --- |
| D1 | Blocker | Extraction returns nothing on real PDFs. Regex wants labels like `Title:`; Claude path is unmeasured (`model_responses.json` is empty); dates are not normalized to ISO | `mp_sources.py`, `structured_extract.py` | WP3 |
| D2 | Blocker | Fee lookup uses `OBC`, `SC`...; real notices use grouped keys like `MP_SC_ST_OBC_EWS_PwD` and `OTHERS`, so most fees come back `needs_check` | `engine.calculate_fee` | WP2 |
| D3 | Blocker | `extract_structured` always sets `review_required=True`; engine forces `needs_check` when set; `verify()` never clears it | `engine.py`, `repositories.verify` | WP1 |
| D4 | High | Fallback extractor never produces age limits, qualification rules or relaxations; `curator_queue` is written but has no API to read or resolve it | `structured_extract.py`, `routes.py` | WP4 |
| D5 | High | Extension reads `localStorage` from another origin and uses different field names (`candidate_name`, `dob` vs `name`, `date_of_birth`) | `extension/content.js` | WP10 (defer) |
| D6 | Blocker | No authentication: anyone can verify, edit, extract (LLM cost), read audit events, and post profiles with disability/category data | `routes.py` | WP6 |
| D7 | Medium | `/stats` reads `../evaluation/results`; Docker copies only `backend/`, so it is empty in the container | `routes.py`, compose | WP7 |
| D8 | High | Streams compared by exact string (`Civil` vs `Civil Engineering`); higher qualification fails unless `or_above` is set; both produce false 'not eligible' | `qualifications.py` | WP5 |
| D9 | Low | Stale docs (EVALUATION date, N=0 README, 9 unlabeled PDFs are exam rulebooks, a different document type) | docs | WP0 |
| D10 | High | Feed only skips `status == 'closed'`; extracted notices have `status=None`, so past-deadline notices appear with negative days left | `engine.get_for_you_feed` | WP1 |
| D11 | High | Seeded fixtures (example.invalid URLs) would be shown to real users | `seed.py`, feed | WP1 |
| D12 | Low | `PrefillRequest` defined twice in `schemas.py`; `SECRET_KEY` unused; `run_all.py` does not run the extraction benchmark | various | WP0 |

---

## 6. Work packages

Order matters. Do not start a WP until the previous gate items it depends on are ticked.

### WP0: Baseline and hygiene (about half a day)

**Tasks**

- Run every verification command on a clean checkout. Record pass/fail in `docs/STATUS.md`.
- Add `AGENTS.md`. Create `docs/STATUS.md` with a table of gates and a dated log.
- Fix D9: update `pdfs/README.md` to the real labeled count; move the 9 rulebook PDFs to `evaluation/fixtures/rulebooks/` with a note; regenerate `EVALUATION.md`.
- Fix D12 items; add the extraction benchmark to `run_all.py` and CI.

**Acceptance:** all commands green, docs match reality, no untracked junk.

### WP1: Verification flag, expiry, fixtures (highest leverage, small)

**Tasks**

1. `NotificationRepository.verify()` sets `review_required=False` in the stored data, in the same transaction as `verified_by='curator'`.
2. Keep `extract_structured` always setting `review_required=True`. Unverified stays `needs_check`; that is correct behavior.
3. Feed: skip notices whose `last_date` parses and is before today. Also compute an effective status (`closing_soon` within 7 days) rather than relying on a manually set `status`.
4. Add a `SHOW_FIXTURES` setting (default false when `APP_ENV=production`) that excludes `source_kind='fixture'` from the feed and `/notifications`.
5. DECISION (owner): does editing a verified notice via `curator_edit` keep it verified? Recommended: yes, but write an audit event and update `verified_at`.

**Tests to add**

- extract, then verify, then `/feed` returns 'eligible' for a complete notice and a matching profile.
- A notice with `last_date` yesterday is absent from the feed.
- Fixture notices absent when `SHOW_FIXTURES=false`.

**Acceptance:** Gate 1.1, 1.2, 1.4.

### WP2: Fee model

**Context:** labeled PDFs use keys such as `MP_SC_ST_OBC_EWS_PwD: 250` and `OTHERS: 500`.

**Approach (recommended, minimal schema churn):** keep `fee_by_category` as extracted, and add a resolver that parses group keys into tokens.

- Token `MP` means domicile is required.
- Tokens `SC, ST, OBC, EWS, UR` are categories; `PwD` matches a disabled candidate.
- `OTHERS` is the fallback for anyone not matched by another key.
- **The owner must confirm the exact meaning against each PDF.** If the meaning is ambiguous, return `needs_check`; never guess.

**Tasks**

- New `resolve_fee(notification, profile)`; keep `calculate_fee(notification, category)` working for legacy plain keys.
- `/fee` and `/assist/pre-submit-checklist` accept the profile; frontend passes it (`getFee` currently sends only the category).
- Portal charges stay separate and are added only when stated.

**Tests:** grouped-key notices for MP-OBC, non-MP-OBC, PwD, UR; unknown shapes return `needs_check` with no total; existing fee tests still pass.

**Acceptance:** Gate 1.3; the three labeled PDFs resolve to correct totals for each profile type.

### WP3: Extraction that actually works

**Step 1: diagnose before coding.** Write `scripts/dump_pdf_text.py` that prints, per page, the extracted text length and whether OCR was skipped. Run it on the 3 labeled PDFs. Write the finding in `docs/extraction-notes.md`: text layer present? Hindi or English? scanned? tables detected?

**Step 2: choose the path based on the finding**

- Text layer present: tune the LLM prompt and parser (below).
- Scanned: install Tesseract with `eng+hin` data in the Docker image and measure OCR quality.

**Step 3: LLM path**

- Set `ANTHROPIC_API_KEY` locally; run `python evaluation/extraction_benchmark.py`.
- Tighten the system prompt with an explicit JSON schema, ISO date format (`YYYY-MM-DD`), and the fee-group key convention used in `expected.json`.
- Add deterministic post-processing that normalizes `dd/mm/yyyy` and `dd-mm-yyyy` to ISO, only where the source snippet supports it.
- Keep the existing guard that discards any value whose snippet is not found verbatim in the source. This is the project's best safety feature.
- Record accepted responses into `evaluation/fixtures/model_responses.json`, keyed by the SHA-256 of the exact input text, so CI replays without network.

**Step 4: label more data.** Hand-label at least 10 official advertisements (do not generate labels with the extractor). Add the source URL, download date and SHA-256 to `manifest.json`.

**Step 5: targets (for the pilot, with curator review as the safety net)**

- Title, advertisement number, dates, vacancies: at least 90% exact match on the labeled set.
- Fees: at least 80%.
- Any field the extractor is unsure of must come back empty, never wrong. A wrong confident value is worse than a blank one.

**Acceptance:** Gate 2.1 to 2.3, with real numbers published in `EVALUATION.md`.

### WP4: Curator workflow (the real engine of the pilot)

Age limits, qualification rules and relaxations will mostly be entered by a human for now.

**Tasks**

- API: `GET /admin/curator-queue`, `POST /admin/curator-queue/{id}/resolve`, admin-only.
- Minimal protected admin page in the frontend (or a CLI if faster): shows the PDF link, the extracted fields with page and snippet, and an editor for `posts`, `age_limit`, `age_relaxation_rules`, `qualification_rules`, `fee_by_category`, dates. Validate against the Pydantic models and show errors inline.
- One button: 'Save and verify' (calls `curator_edit` then `verify`).
- A written checklist for the curator in `docs/curator-guide.md`: what to read in a PDF, what to leave blank, how to enter relaxations.

**Acceptance:** Gate 2.4 and 2.5, timed on a real notice.

### WP5: Matching that fails safe (DECISION required)

**Principle:** a user wrongly told 'not eligible' silently loses an opportunity; a user told 'needs check' still looks. Prefer `needs_check` when evidence is uncertain.

**Tasks**

- Add `streams.yaml` (aliases such as Civil = Civil Engineering) and normalize both sides; replace the free-text stream input in onboarding with a suggestion list.
- DECISION: for a candidate whose level is above the required level and the rule has no `or_above`, return `needs_check` (not `not_eligible`) with a message to confirm 'or higher' in the notice. This changes several of the 122 cases (for example `qual_11`, `qual_15`, `qual_19`, `qual_20`, `qual_24`); update them with written justification, then re-run the benchmark.
- Add regression cases derived from the real labeled notices.

**Acceptance:** Gate 1.5; benchmark still 100% on the updated corpus.

### WP6: Security and privacy

**Tasks**

- Admin auth: `ADMIN_API_KEY` header check (FastAPI dependency) on `/notifications/extract`, `/extract-pdf`, `/verify`, `PATCH /notifications/{id}`, `/audit-events`, `/admin/*`. Upgrade to real accounts only if more than one curator is needed.
- Data minimization (DECISION): the feed already works with the profile sent per request, so for the pilot consider **not storing profiles server-side at all**. If stored, add: consent record (timestamp, policy version, stored on the server), `DELETE /profiles/{user_id}`, retention period, and a privacy notice page in the app.
- Rate limiting on public endpoints; request logging that never records profile bodies.
- Remove or password-protect `/docs` in production; wire up `SECRET_KEY` or delete it.
- Dependency audit (`pip-audit`, `npm audit`) in CI.
- Have a qualified person review privacy and DPDP obligations. The agent cannot give legal sign-off.

**Tests:** unauthenticated calls to admin routes return 401; delete endpoint removes profile and cascades; no PII in log output (capture and assert).

**Acceptance:** Gate 3.

### WP7: Deployment and operations

**Tasks**

- Compose: mount `./evaluation:/evaluation:ro` into the backend (the `/stats` route resolves to `/evaluation/results` inside the container), fixing D7.
- Add a frontend service or deploy it separately; set `NEXT_PUBLIC_API_BASE_URL`. Note that Next rewrites read it at build/start, so set it in the build step.
- Reverse proxy with HTTPS (Caddy is simplest). Single small VPS or a managed host plus managed Postgres.
- Production env file template; `APP_ENV=production`; `SHOW_FIXTURES=false`; strong DB password (the compose file currently uses `postgres/postgres`).
- Nightly `pg_dump` to off-box storage; document and **test** a restore.
- Uptime monitor on `/health`; error alerts to Telegram (config keys already exist).
- Install Tesseract in the backend image if WP3 requires OCR.

**Acceptance:** Gate 4, demonstrated by deploying from scratch on a clean machine.

### WP8: Product polish

- Show 'Last verified on' and a 'Report an error' link on every notice; show the source PDF prominently.
- Hindi review per `docs/i18n-review.md`; backend reason messages are English-only, so either translate them by reason code or label them clearly.
- Clear empty, error and offline states; test on a low-end Android device and a slow network.
- Accessibility pass (keyboard, contrast, screen reader labels).
- Update README phase table to the true state.

**Acceptance:** Gate 5.

### WP9: Notifications (optional, after launch)

The frontend never creates `applications`, so per-user reminders have nothing to act on yet. For the pilot, a simpler and more useful feature is a **Telegram channel post whenever a notice is verified**, using the existing bot token variables. Per-user reminders can come later with accounts.

### WP10: Extension (deferred)

Do not work on it for the pilot. To revive: capture the profile through the extension's own popup or options page and `chrome.storage`, map to real form field names after inspecting the live MP Online forms, never auto-submit, and keep it fully opt-in.

---

## 7. Per-task workflow

For every task, Antigravity follows this loop:

1. **Plan:** read the WP, list files and tests, flag DECISION items. Owner approves.
2. **Red:** write failing tests first.
3. **Green:** smallest change that passes.
4. **Full verification:** run all commands in section 2.
5. **Docs:** update README, STATUS, EVALUATION as needed.
6. **Report:** files changed, test output, what remains, any risk found.
7. **Owner review and merge.**

**Prompt template (paste into Antigravity per WP)**

```
Role: senior engineer on MP Job Saathi. Read AGENTS.md and the Pilot Delivery Guide.
Task: execute WP<N> only.
First produce a plan: files to change, tests to add, DECISION items. Stop for approval.
After approval: tests first, then implementation. Do not touch unrelated files.
Never invent recruitment facts. Do not edit existing eligibility cases without flagging it.
Finish with: full verification output, acceptance criteria checklist with pass/fail, and any new risks.
```

**Review prompt (second agent or fresh session)**

```
Review the diff for WP<N> against the guide's acceptance criteria. Look for: weakened tests,
hardcoded recruitment facts, missing migrations, PII in logs, unauthenticated routes, stale docs.
Report findings by severity. Do not modify code.
```

---

## 8. Suggested schedule (rough, one focused person plus the agent)

- **Week 1:** WP0, WP1, WP2. Visible win: correct fees and verified notices reach 'Eligible'.
- **Week 2:** WP3, WP4. Real extraction numbers and a working curator flow.
- **Week 3:** WP5, WP6. Safer matching, authentication, privacy.
- **Week 4:** WP7, WP8, then a closed pilot with 10 to 20 users.
- **Weeks 5 to 6:** feedback, fixes, widen to about 100 users.

Estimates are rough; WP3 is the largest unknown because its first step is diagnosis.

---

## 9. Go/No-Go and pilot operations

**Go only if all are true**

- [ ] Every Gate in section 4 is ticked
- [ ] At least 3 live notices verified by the owner against the source PDF
- [ ] A second person cross-checked those 3 notices
- [ ] Production smoke test: onboarding, feed, detail, checklist, language switch, offline saved job
- [ ] Backup restore tested within the last 7 days
- [ ] A named person owns incident response and error reports

**Operating routine**

- Daily: check official MPPSC and MPESB sources, ingest and verify new notices, retire closed ones.
- Weekly: review error reports, update labeled set, re-run benchmarks, update STATUS.
- Metrics: notices verified per week, time to verify, user-reported errors (target: zero wrong 'Eligible' claims), weekly active users.

**Standing user-facing rule:** every notice shows its source link and 'confirm in the official notification before paying'. The product assists; it does not replace the official source.

---

## 10. Risks

| Risk | Mitigation |
| --- | --- |
| Wrong 'Eligible' causes a user to pay a fee or miss a deadline | Verified-only 'Eligible', visible source and last-verified date, fail-safe matching, error-report link |
| Scraping terms or robots restrictions | Existing allowlist plus robots check; manual download workflow remains the fallback |
| Personal data exposure (category, disability) | Minimize server storage, admin auth, deletion endpoint, legal review |
| LLM misreads a notice | Snippet-verification guard, curator verification, measured benchmark |
| LLM cost abuse | Admin-only extraction endpoints, rate limits |
| Single-owner bottleneck | Curator guide, a second reviewer, small notice scope |
| Benchmark overconfidence | Treat the 122-case result as self-consistency only; grow real-notice cases |

---

## 11. Status log template (`docs/STATUS.md`)

```
## YYYY-MM-DD
WP: <n>  Branch: <name>  Commit: <hash>
Done: ...
Tests: backend <passed/total>, frontend <passed/total>, eligibility <x/122>, extraction <metrics>
Gate items ticked: ...
Open risks / decisions needed: ...
```

The first honest entry to make is the Gate 0 run, followed by WP1.
