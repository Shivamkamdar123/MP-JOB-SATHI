from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "evaluation" / "EVALUATION.md"


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True)


def write_report(timestamp: str, commands: list[tuple[str, subprocess.CompletedProcess[str]]]) -> None:
    existing_report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.exists() else ""
    extraction_marker = "## PDF Extraction Baseline"
    extraction_section = existing_report[existing_report.index(extraction_marker):] if extraction_marker in existing_report else ""
    lines: list[str] = [
        "# MP Job Saathi Evaluation",
        "",
        f"Generated on {timestamp} by `python evaluation/run_all.py`.",
        "",
        "## Benchmarks run",
        "",
    ]

    for label, result in commands:
        command_text = " ".join(result.args)
        lines.extend([
            f"{label}",
            f"- Command: `{command_text}`",
            "- Result:",
            "",
            "```text",
            (result.stdout.strip() or result.stderr.strip() or f"Exit code: {result.returncode}"),
            "```",
            "",
        ])

    lines.extend([
        "## Notes",
        "",
        "- The repo currently contains a measured backend baseline, not a full live-data pipeline.",
        "- Warning output is recorded as-is and reported without hiding failures.",
        "- Fixture-backed data must be treated as such and not presented as curated live source data.",
        "",
        "## Current status",
        "",
        "- WP0: baseline repo and review gates are in place",
        "- WP1: eligibility engine rewrite is measured against the checked-in rule-case corpus",
        "- WP2-WP4: existing partial foundations remain frozen pending review",
    ])
    if extraction_section:
        lines.extend(["", extraction_section.rstrip()])

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    extraction_proc = run_command([sys.executable, "evaluation/extraction_benchmark.py"])
    commands = [
        (
            "Backend test suite",
            run_command([sys.executable, "-m", "pytest", "backend/tests", "-q"]),
        ),
        (
            "Eligibility rule-case benchmark",
            run_command([sys.executable, "evaluation/eligibility_benchmark.py"]),
        ),
        (
            "PDF extraction benchmark",
            extraction_proc,
        ),
    ]
    write_report(timestamp, commands)

    for _, result in commands:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        if result.returncode != 0:
            return result.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
