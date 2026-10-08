from __future__ import annotations


def create_application_tracking(job_title: str, company: str, stage: str, deadline: str | None = None, exam_date: str | None = None) -> dict:
    return {
        "job_title": job_title,
        "company": company,
        "stage": stage,
        "deadline": deadline,
        "exam_date": exam_date,
        "status": "active" if stage in {"saved", "preparing", "ready", "user_submitted", "exam_scheduled", "admit_card"} else "done",
    }


def build_reminders(deadline: str | None = None, exam_date: str | None = None, result_date: str | None = None) -> list[dict]:
    reminders: list[dict] = []
    if deadline:
        reminders.append({
            "title": "Deadline reminder",
            "kind": "deadline",
            "date": deadline,
            "message": "Final application deadline is approaching. Confirm the official notification before paying or submitting.",
        })
    if exam_date:
        reminders.append({
            "title": "Admit card window",
            "kind": "admit_card",
            "date": exam_date,
            "message": "Check for admit card release and print/download requirements in the official portal.",
        })
    if result_date:
        reminders.append({
            "title": "Result check",
            "kind": "result",
            "date": result_date,
            "message": "Track the result date and verify any official announcement against the recruiting body's website.",
        })
    return reminders


def build_share_card(title: str, share_url: str) -> dict:
    return {
        "title": title,
        "share_url": share_url,
        "message": "Official notification: verify the last date and eligibility before applying.",
    }


def build_admin_snapshot(center_name: str, applications: list[dict]) -> dict:
    totals = {"saved": 0, "preparing": 0, "ready": 0, "submitted": 0, "closed": 0}
    for app in applications:
        key = app.get("status", "saved")
        if key in totals:
            totals[key] += 1
        else:
            totals["saved"] += 1
    return {
        "center_name": center_name,
        "totals": totals,
        "applications": applications,
    }
