Operating contract for the agent
Copy this section into AGENTS.md at the repo root (or your Antigravity workspace rules, if your version supports them).
1. Checklist first, code second. Before each work package (WP), write a plan listing files to touch and tests to add. Wait for owner approval on any item marked DECISION.
2. Never invent recruitment facts. No made-up dates, fees, ages or qualifications in code, tests, fixtures or docs. Every fact needs a source PDF and page. This rule already exists in the extractor; keep it.
3. Tests before claims. A task is done only when: new tests pass, the full suite passes, and the acceptance criteria in this guide are met. Report exact command output, never 'should work'.
4. Small changes. One WP per branch, one concern per commit, conventional commit messages (fix(fee): ...).
5. Do not weaken tests to pass. If a test must change, state why in the commit and flag it for owner review. The 122 eligibility cases encode policy; changing them is a DECISION.
6. Keep docs honest. Update README.md phase table, docs/STATUS.md and the evaluation report in the same PR as the behavior change.
7. Secrets. Never commit keys. Use .env; update .env.example for any new variable.
8. Migrations. Any schema change gets an Alembic migration and a test that it applies to an empty SQLite DB (pattern exists in test_persistence.py).
9. Stop conditions. If blocked, or a fix would need a product/legal decision, stop and ask. Do not guess.
Verification commands (run all before every PR)
python -m pytest backend/tests -q
cd frontend && npx tsc --noEmit && npm run lint && npm test && npm run build
python evaluation/eligibility_benchmark.py
python evaluation/extraction_benchmark.py