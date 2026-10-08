# MP Job Saathi Evaluation

Generated on 2026-10-08 07:14:44 UTC by `python evaluation/run_all.py`.

## Benchmarks run

Backend test suite
- Command: `C:\Users\Hp\AppData\Local\Programs\Python\Python312\python.exe -m pytest backend/tests -q`
- Result:

```text
..................                                                       [100%]
============================== warnings summary ===============================
C:\Users\Hp\AppData\Local\Programs\Python\Python312\Lib\site-packages\starlette\formparsers.py:12
  C:\Users\Hp\AppData\Local\Programs\Python\Python312\Lib\site-packages\starlette\formparsers.py:12: PendingDeprecationWarning: Please use `import python_multipart` instead.
    import multipart

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
18 passed, 1 warning in 1.01s
```

## Notes

- The repo currently contains a measured backend baseline, not a full live-data pipeline.
- Warning output is recorded as-is and reported without hiding failures.
- Fixture-backed data must be treated as such and not presented as curated live source data.

## Current status

- Phase 1: partial, fixture-backed, model + rules + engine verified by tests
- Phases 2-4: scaffold-only and not yet production-grade
