# MP Job Saathi: Pilot Status

## Master Checklist

### Gate 0: Baseline
- [x] 0.1 Clean checkout runs all verification commands; results recorded in `docs/STATUS.md`
- [x] 0.2 `AGENTS.md` added from section 2
- [x] 0.3 Branch strategy: `main` protected, work on `pilot/*` branches
- [x] 0.4 Stale docs corrected (D9)

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

## Log

### 2026-10-30
WP: WP0  Branch: pilot/wp0-baseline
Done:
- Executed all 4 verification commands against clean checkout; recorded results.
- Added and tracked `AGENTS.md` with agent operating contract.
- Established `pilot/*` branch workflow starting on `pilot/wp0-baseline`.
- Resolved D9: moved 9 MPESB exam rulebooks from `evaluation/fixtures/pdfs/` to `evaluation/fixtures/rulebooks/` with documentation; updated `pdfs/README.md` to honest N=3 sample size; updated `manifest.json`.
- Resolved D12: eliminated duplicate `PrefillRequest` definition in `backend/app/api/schemas.py`; wired `SECRET_KEY` into `backend/app/core/config.py`; added extraction benchmark to `evaluation/run_all.py`.
- Added hygiene tests in `backend/tests/test_hygiene.py` covering schema uniqueness, `SECRET_KEY`, and fixture structure cleanliness.
Tests: backend 170/170 passed (1 warning), frontend 9/9 passed (tsc, lint, build clean), eligibility 122/122 passed, extraction N=3 evaluated (0% recall baseline honestly recorded).
Gate items ticked: Gate 0.1, Gate 0.2, Gate 0.3, Gate 0.4.
Open risks / decisions needed:
- D1 extraction blocker (0% recall across 9 fields on real PDFs) is scheduled for diagnosis and fix in WP3.
- D2 fee resolver and D3 verification review flag are the immediate next gates (WP1 and WP2).

