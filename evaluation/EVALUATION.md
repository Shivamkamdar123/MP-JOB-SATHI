# MP Job Saathi Evaluation

Generated on 2026-10-10 08:57:19 UTC by `python evaluation/run_all.py`.

## Benchmarks run

Backend test suite
- Command: `D:\myproject\MP-JOB-SATHI\.venv312\Scripts\python.exe -m pytest backend/tests -q`
- Result:

```text
........................................................................ [ 43%]
........................................................................ [ 86%]
.......................                                                  [100%]
============================== warnings summary ===============================
.venv312\Lib\site-packages\starlette\testclient.py:40
  D:\myproject\MP-JOB-SATHI\.venv312\Lib\site-packages\starlette\testclient.py:40: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
167 passed, 1 warning in 6.11s
```

Eligibility rule-case benchmark
- Command: `D:\myproject\MP-JOB-SATHI\.venv312\Scripts\python.exe evaluation/eligibility_benchmark.py`
- Result:

```text
{
  "generated_at": "2026-10-10T08:57:27.775250+00:00",
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

- No automated crawling was performed. Official PDFs will be downloaded manually into `evaluation/fixtures/pdfs/`; robots.txt restrictions on crawlers do not prevent that manual workflow.
- Labeled evaluation set: **N=3; this is the current labeled-PDF sample size.**
- `N/A` means no labeled examples support a metric; see [`evaluation/results/extraction.json`](results/extraction.json) for counts and failures.
- Per-field metrics:

| Field | Precision | Recall | Accuracy | TP / FP / FN / TN |
| --- | ---: | ---: | ---: | ---: |
| `org` | N/A | 0.000 | 0.000 | 0 / 0 / 3 / 0 |
| `advertisement_no` | N/A | 0.000 | 0.000 | 0 / 0 / 3 / 0 |
| `title` | N/A | 0.000 | 0.000 | 0 / 0 / 3 / 0 |
| `total_vacancies` | N/A | 0.000 | 0.000 | 0 / 0 / 3 / 0 |
| `opens_date` | N/A | 0.000 | 0.000 | 0 / 0 / 3 / 0 |
| `last_date` | N/A | 0.000 | 0.000 | 0 / 0 / 3 / 0 |
| `fee_by_category` | N/A | 0.000 | 0.000 | 0 / 0 / 3 / 0 |
| `portal_charges` | N/A | 0.000 | 0.667 | 0 / 0 / 1 / 2 |
| `exam_date` | N/A | 0.000 | 0.667 | 0 / 0 / 1 / 2 |

- Method breakdown: `regex`: 33.
- Failed field comparisons: 23.
- The test suite exercises policy checks, provenance persistence, hash-based reuse, and PDF-ingest-to-feed plumbing with a stubbed PDF decoder. It does not establish real-PDF extraction accuracy.
- Next data step: manually add official PDFs and hand-read `expected.json` labels with source URL, download date, and SHA-256 manifest entries. No crawler will be used.
