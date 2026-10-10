from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.ingestion.pdf_extract import extract_pdf
from app.ingestion.structured_extract import extract_structured

FIXTURE_ROOT = ROOT / "evaluation" / "fixtures" / "pdfs"
RESULT_PATH = ROOT / "evaluation" / "results" / "extraction.json"
FIELDS = (
    "org", "advertisement_no", "title", "total_vacancies", "opens_date", "last_date",
    "fee_by_category", "portal_charges", "exam_date",
)


def _nonempty(value: Any) -> bool:
    return value is not None and value != "" and value != {} and value != []


def _score(counts: Counter[str]) -> dict[str, float | int | None]:
    tp, fp, fn, tn = (counts[name] for name in ("tp", "fp", "fn", "tn"))
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "accuracy": (tp + tn) / (tp + fp + fn + tn) if tp + fp + fn + tn else None,
    }


def _format_metric(value: float | int | None) -> str:
    return "N/A" if value is None else f"{value:.3f}" if isinstance(value, float) else str(value)


def _write_evaluation_section(result: dict[str, Any]) -> None:
    report_path = ROOT / "evaluation" / "EVALUATION.md"
    existing = report_path.read_text(encoding="utf-8") if report_path.exists() else "# MP Job Saathi Evaluation\n"
    marker = "## PDF Extraction Baseline"
    prefix = existing.split(marker, 1)[0].rstrip()
    lines = [
        marker,
        "",
        "- No automated crawling was performed. Official PDFs will be downloaded manually into `evaluation/fixtures/pdfs/`; robots.txt restrictions on crawlers do not prevent that manual workflow.",
        f"- Labeled evaluation set: **{result['target_statement']}**",
        "- `N/A` means no labeled examples support a metric; see [`evaluation/results/extraction.json`](results/extraction.json) for counts and failures.",
        "- Per-field metrics:",
        "",
        "| Field | Precision | Recall | Accuracy | TP / FP / FN / TN |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for field, metrics in result["metrics"].items():
        counts = " / ".join(str(metrics[name]) for name in ("tp", "fp", "fn", "tn"))
        lines.append(
            f"| `{field}` | {_format_metric(metrics['precision'])} | {_format_metric(metrics['recall'])} | "
            f"{_format_metric(metrics['accuracy'])} | {counts} |"
        )
    methods = result["method_breakdown"]
    method_text = ", ".join(f"`{name}`: {count}" for name, count in methods.items()) or "none (N=0)"
    lines.extend([
        "",
        f"- Method breakdown: {method_text}.",
        f"- Failed field comparisons: {len(result['failures'])}.",
        "- The test suite exercises policy checks, provenance persistence, hash-based reuse, and PDF-ingest-to-feed plumbing with a stubbed PDF decoder. It does not establish real-PDF extraction accuracy.",
        "- Next data step: manually add official PDFs and hand-read `expected.json` labels with source URL, download date, and SHA-256 manifest entries. No crawler will be used.",
    ])
    report_path.write_text(prefix + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def run_benchmark() -> dict[str, Any]:
    counts: dict[str, Counter[str]] = {field: Counter() for field in FIELDS}
    failures: list[dict[str, Any]] = []
    methods: Counter[str] = Counter()
    documents: list[dict[str, Any]] = []
    unlabelled: list[str] = []

    for pdf_path in sorted(FIXTURE_ROOT.rglob("*.pdf")):
        expected_path = pdf_path.parent / "expected.json"
        if not expected_path.exists():
            unlabelled.append(str(pdf_path.relative_to(ROOT)))
            continue
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        parsed_pdf = extract_pdf(pdf_path)
        actual = extract_structured(
            parsed_pdf.pages,
            parsed_pdf.tables,
            source_url=None,
            ocr_pages=parsed_pdf.ocr_pages,
        )
        actual_data = actual.model_dump(mode="json")
        for field, provenance in actual.field_provenance.items():
            methods[provenance.method] += 1
        for field in FIELDS:
            if field not in expected:
                continue
            expected_value = expected[field]
            actual_value = actual_data.get(field)
            expected_present = _nonempty(expected_value)
            actual_present = _nonempty(actual_value)
            if expected_present and actual_value == expected_value:
                counts[field]["tp"] += 1
            elif expected_present and not actual_present:
                counts[field]["fn"] += 1
            elif expected_present:
                counts[field]["fp"] += 1
                counts[field]["fn"] += 1
            elif actual_present:
                counts[field]["fp"] += 1
            else:
                counts[field]["tn"] += 1
            if expected_value != actual_value:
                failures.append({
                    "document": pdf_path.parent.name,
                    "field": field,
                    "expected": expected_value,
                    "actual": actual_value,
                })
        documents.append({
            "id": pdf_path.parent.name,
            "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
            "label": str(expected_path.relative_to(ROOT)),
        })

    n = len(documents)
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n": n,
        "target_statement": f"N={n}; this is the current labeled-PDF sample size.",
        "documents": documents,
        "unlabelled_pdfs": unlabelled,
        "metrics": {field: _score(counts[field]) for field in FIELDS},
        "failures": failures,
        "method_breakdown": dict(sorted(methods.items())),
        "limitations": "No accuracy claim is supported without hand-labeled official PDF fixtures.",
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_evaluation_section(result)
    return result


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), ensure_ascii=False, indent=2))