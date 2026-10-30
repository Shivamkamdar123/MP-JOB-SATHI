# MP Job Saathi Evaluation

Generated on 2026-10-30 04:52:34 UTC by `python evaluation/run_all.py`.

## Benchmarks run

Backend test suite
- Command: `D:\myproject\MP-JOB-SATHI\.venv312\Scripts\python.exe -m pytest backend/tests -q`
- Result:

```text
........................................................................ [ 42%]
........................................................................ [ 84%]
..........................                                               [100%]
============================== warnings summary ===============================
.venv312\Lib\site-packages\starlette\testclient.py:40
  D:\myproject\MP-JOB-SATHI\.venv312\Lib\site-packages\starlette\testclient.py:40: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
170 passed, 1 warning in 4.46s
```

Eligibility rule-case benchmark
- Command: `D:\myproject\MP-JOB-SATHI\.venv312\Scripts\python.exe evaluation/eligibility_benchmark.py`
- Result:

```text
{
  "generated_at": "2026-10-30T04:52:48.598345+00:00",
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

PDF extraction benchmark
- Command: `D:\myproject\MP-JOB-SATHI\.venv312\Scripts\python.exe evaluation/extraction_benchmark.py`
- Result:

```text
{
  "generated_at": "2026-10-30T04:52:41.877134+00:00",
  "n": 3,
  "target_statement": "N=3; this is the current labeled-PDF sample size.",
  "documents": [
    {
      "id": "advt_ad_farmers_welfare_2026",
      "sha256": "983844afc7e6e369fa15aa7824571472cd486c3437ed2d57dd0ac5009b4e3ebb",
      "label": "evaluation\\fixtures\\pdfs\\advt_ad_farmers_welfare_2026\\expected.json"
    },
    {
      "id": "advt_assistant_director_2026",
      "sha256": "7ab4a15ea7558750e4354d0c0e5d2ef93cf99aeefd4ef166cbf7fd5a17cf17aa",
      "label": "evaluation\\fixtures\\pdfs\\advt_assistant_director_2026\\expected.json"
    },
    {
      "id": "advt_law_officer_2026",
      "sha256": "ff6c06c4da6b339889419371acec40a208c5a46cd75d0f6035dc5d5c7ae7651e",
      "label": "evaluation\\fixtures\\pdfs\\advt_law_officer_2026\\expected.json"
    }
  ],
  "unlabelled_pdfs": [],
  "metrics": {
    "org": {
      "tp": 0,
      "fp": 0,
      "fn": 3,
      "tn": 0,
      "precision": null,
      "recall": 0.0,
      "accuracy": 0.0
    },
    "advertisement_no": {
      "tp": 0,
      "fp": 0,
      "fn": 3,
      "tn": 0,
      "precision": null,
      "recall": 0.0,
      "accuracy": 0.0
    },
    "title": {
      "tp": 0,
      "fp": 0,
      "fn": 3,
      "tn": 0,
      "precision": null,
      "recall": 0.0,
      "accuracy": 0.0
    },
    "total_vacancies": {
      "tp": 0,
      "fp": 0,
      "fn": 3,
      "tn": 0,
      "precision": null,
      "recall": 0.0,
      "accuracy": 0.0
    },
    "opens_date": {
      "tp": 0,
      "fp": 0,
      "fn": 3,
      "tn": 0,
      "precision": null,
      "recall": 0.0,
      "accuracy": 0.0
    },
    "last_date": {
      "tp": 0,
      "fp": 0,
      "fn": 3,
      "tn": 0,
      "precision": null,
      "recall": 0.0,
      "accuracy": 0.0
    },
    "fee_by_category": {
      "tp": 0,
      "fp": 0,
      "fn": 3,
      "tn": 0,
      "precision": null,
      "recall": 0.0,
      "accuracy": 0.0
    },
    "portal_charges": {
      "tp": 0,
      "fp": 0,
      "fn": 1,
      "tn": 2,
      "precision": null,
      "recall": 0.0,
      "accuracy": 0.6666666666666666
    },
    "exam_date": {
      "tp": 0,
      "fp": 0,
      "fn": 1,
      "tn": 2,
      "precision": null,
      "recall": 0.0,
      "accuracy": 0.6666666666666666
    }
  },
  "failures": [
    {
      "document": "advt_ad_farmers_welfare_2026",
      "field": "org",
      "expected": "MPPSC",
      "actual": null
    },
    {
      "document": "advt_ad_farmers_welfare_2026",
      "field": "advertisement_no",
      "expected": "09/2026",
      "actual": null
    },
    {
      "document": "advt_ad_farmers_welfare_2026",
      "field": "title",
      "expected": "Assistant Director, Farmers Welfare & Agriculture Development (Statistics)",
      "actual": null
    },
    {
      "document": "advt_ad_farmers_welfare_2026",
      "field": "total_vacancies",
      "expected": 2,
      "actual": null
    },
    {
      "document": "advt_ad_farmers_welfare_2026",
      "field": "opens_date",
      "expected": "2026-08-04",
      "actual": null
    },
    {
      "document": "advt_ad_farmers_welfare_2026",
      "field": "last_date",
      "expected": "2026-09-03",
      "actual": null
    },
    {
      "document": "advt_ad_farmers_welfare_2026",
      "field": "fee_by_category",
      "expected": {
        "MP_SC_ST_OBC_EWS_PwD": 250,
        "OTHERS": 500
      },
      "actual": {}
    },
    {
      "document": "advt_ad_farmers_welfare_2026",
      "field": "portal_charges",
      "expected": 40,
      "actual": null
    },
    {
      "document": "advt_assistant_director_2026",
      "field": "org",
      "expected": "MPPSC",
      "actual": null
    },
    {
      "document": "advt_assistant_director_2026",
      "field": "advertisement_no",
      "expected": "12/2026",
      "actual": null
    },
    {
      "document": "advt_assistant_director_2026",
      "field": "title",
      "expected": "Assistant Director (Higher Education Department)",
      "actual": null
    },
    {
      "document": "advt_assistant_director_2026",
      "field": "total_vacancies",
      "expected": 3,
      "actual": null
    },
    {
      "document": "advt_assistant_director_2026",
      "field": "opens_date",
      "expected": "2026-07-17",
      "actual": null
    },
    {
      "document": "advt_assistant_director_2026",
      "field": "last_date",
      "expected": "2026-08-16",
      "actual": null
    },
    {
      "document": "advt_assistant_director_2026",
      "field": "fee_by_category",
      "expected": {
        "MP_SC_ST_OBC_EWS_PwD": 250,
        "OTHERS": 500
      },
      "actual": {}
    },
    {
      "document": "advt_law_officer_2026",
      "field": "org",
      "expected": "MPPSC",
      "actual": null
    },
    {
      "document": "advt_law_officer_2026",
      "field": "advertisement_no",
      "expected": "13/2026",
      "actual": null
    },
    {
      "document": "advt_law_officer_2026",
      "field": "title",
      "expected": "Law Officer (Jail Department)",
      "actual": null
    },
    {
      "document": "advt_law_officer_2026",
      "field": "total_vacancies",
      "expected": 4,
      "actual": null
    },
    {
      "document": "advt_law_officer_2026",
      "field": "opens_date",
      "expected": "2026-10-15",
      "actual": null
    },
    {
      "document": "advt_law_officer_2026",
      "field": "last_date",
      "expected": "2026-11-05",
      "actual": null
    },
    {
      "document": "advt_law_officer_2026",
      "field": "fee_by_category",
      "expected": {
        "MP_SC_ST_OBC_EWS_PwD": 250,
        "OTHERS": 500
      },
      "actual": {}
    },
    {
      "document": "advt_law_officer_2026",
      "field": "exam_date",
      "expected": "2026-12-13",
      "actual": null
    }
  ],
  "method_breakdown": {
    "regex": 33
  },
  "limitations": "No accuracy claim is supported without hand-labeled official PDF fixtures."
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
