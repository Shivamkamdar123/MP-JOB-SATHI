from __future__ import annotations

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

from app.eligibility.engine import evaluate_eligibility
from app.models import GovtNotification, UserProfile

CASES_PATH = BACKEND / "tests" / "eligibility" / "cases.json"
RESULT_PATH = ROOT / "evaluation" / "results" / "eligibility.json"


def run_benchmark() -> dict[str, Any]:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    by_status: Counter[str] = Counter()
    failures: list[dict[str, Any]] = []
    status_passed = 0
    reason_passed = 0
    passed = 0

    for case in cases:
        result = evaluate_eligibility(
            GovtNotification.model_validate(case["notification"]),
            UserProfile.model_validate(case["profile"]),
        )
        by_status[result.status] += 1
        status_ok = result.status == case["expected_status"]
        status_passed += int(status_ok)

        actual_reason_pairs = {
            (reason.check, reason.result) for reason in result.reasons
        }
        for post_result in result.post_results:
            actual_reason_pairs.update(
                (reason["check"], reason["result"])
                for reason in post_result["reasons"]
            )
        expected_reason_pairs = {
            (item["check"], item["result"])
            for item in case["expected_reason_codes"]
        }
        missing_reason_pairs = expected_reason_pairs - actual_reason_pairs
        reason_ok = not missing_reason_pairs
        reason_passed += int(reason_ok)
        passed += int(status_ok and reason_ok)
        if not status_ok or not reason_ok:
            failures.append({
                "id": case["id"],
                "expected": case["expected_status"],
                "actual": result.status,
                "missing_reason_codes": [
                    {"check": check, "result": outcome}
                    for check, outcome in sorted(missing_reason_pairs)
                ],
            })

    n = len(cases)
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n": n,
        "passed": passed,
        "failed": len(failures),
        "pass_rate": passed / n if n else None,
        "status_passed": status_passed,
        "status_pass_rate": status_passed / n if n else None,
        "reason_passed": reason_passed,
        "reason_pass_rate": reason_passed / n if n else None,
        "actual_status_counts": dict(sorted(by_status.items())),
        "failures": failures,
        "limitations": "This benchmark measures curated rule cases, not real recruitment-notice accuracy.",
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = run_benchmark()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["failed"] else 0)