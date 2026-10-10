# MP Job Saathi Evaluation

Generated on 2026-10-10 07:52:55 UTC by `python evaluation/run_all.py`.

## Benchmarks run

Backend test suite
- Command: `C:\Users\Hp\AppData\Local\Programs\Python\Python312\python.exe -m pytest backend/tests -q`
- Result:

```text
........................................................................ [ 43%]
........................................................................ [ 86%]
.......................                                                  [100%]
============================== warnings summary ===============================
C:\Users\Hp\AppData\Local\Programs\Python\Python312\Lib\site-packages\starlette\formparsers.py:12
  C:\Users\Hp\AppData\Local\Programs\Python\Python312\Lib\site-packages\starlette\formparsers.py:12: PendingDeprecationWarning: Please use `import python_multipart` instead.
    import multipart

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
167 passed, 1 warning in 4.27s
```

Eligibility rule-case benchmark
- Command: `C:\Users\Hp\AppData\Local\Programs\Python\Python312\python.exe evaluation/eligibility_benchmark.py`
- Result:

```text
{
  "generated_at": "2026-10-10T07:53:01.288952+00:00",
  "n": 122,
  "passed": 122,
  "failed": 0,
  "pass_rate": 1.0,
  "status_passed": 122,
  "status_pass_rate": 1.0,
  "reason_passed": 122,
  "reason_pass_rate": 1.0,
  "actual_status_counts": {
    "eligible": 61,
    "likely": 4,
    "needs_check": 21,
    "not_eligible": 36
  },
  "failures": [],
  "limitations": "This benchmark measures curated rule cases, not real recruitment-notice accuracy."
}
```

## Notes

- The repo currently contains a measured backend baseline, not a full live-data pipeline.
- Warning output is recorded as-is and reported without hiding failures.
- Fixture-backed data must be treated as such and not presented as curated live source data.

## Current status

- WP0: baseline repo and review gates are in place
- WP1: eligibility engine rewrite is measured against the checked-in rule-case corpus
- WP2-WP4: existing partial foundations remain frozen pending review

## PDF Extraction Baseline

- No automated crawling was performed. Official PDFs will be downloaded manually into `evaluation/fixtures/pdfs/`.
- Labeled evaluation set: **N=0; this is the true current sample size.**
- No extraction accuracy claim is supported; all per-field metrics are N/A at N=0.
- The test suite covers pipeline behavior with a stubbed PDF decoder, not real-PDF extraction accuracy.
- Next data step: manually add official PDFs and hand-read `expected.json` labels with source URL, download date, and SHA-256 manifest entries. Do not crawl.
