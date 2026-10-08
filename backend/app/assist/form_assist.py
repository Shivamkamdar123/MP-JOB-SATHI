from __future__ import annotations

from pathlib import Path
from typing import Any

from app.eligibility.engine import calculate_fee, evaluate_eligibility
from app.models import GovtNotification, UserProfile


def validate_document_spec(file_name: str, file_size_bytes: int, width: int, height: int, mime_type: str) -> dict[str, Any]:
    issues: list[str] = []
    extension = Path(file_name).suffix.lower()
    allowed_extensions = {".jpg", ".jpeg", ".png", ".pdf"}
    if extension not in allowed_extensions:
        issues.append("Unsupported file format. Use JPG, PNG, or PDF.")

    if file_name.lower().startswith("photo") and file_size_bytes > 200_000:
        issues.append("Photo is too large. Keep it under 200 KB.")
    if file_name.lower().startswith("signature") and file_size_bytes > 50_000:
        issues.append("Signature is too large. Keep it under 50 KB.")

    if mime_type.startswith("image/") and width and height:
        if "photo" in file_name.lower() and (width < 300 or height < 400):
            issues.append("Photo dimension too small. Use at least 300x400 px.")
        if "signature" in file_name.lower() and (width < 150 or height < 60):
            issues.append("Signature dimension too small. Use at least 150x60 px.")
        if "signature" in file_name.lower() and (width > 180 or height > 180):
            issues.append("Signature dimension is too large. Keep it compact within about 150x60 to 180x180 px.")
        if "photo" in file_name.lower() and (width > 500 or height > 500):
            issues.append("Photo dimension should stay within standard passport-size dimensions.")

    return {"is_valid": not issues, "issues": issues}


def generate_form_prefill(profile: UserProfile) -> dict[str, str]:
    return {
        "candidate_name": profile.name,
        "dob": profile.date_of_birth,
        "category": profile.category.upper(),
        "gender": profile.gender,
        "domicile": "Yes" if profile.mp_domicile else "No",
        "employment_exchange": "Yes" if profile.employment_exchange_registered else "No",
    }


def build_pre_submit_checklist(
    profile: UserProfile,
    notification: GovtNotification,
    category: str = "UR",
    paid: bool = False,
    docs_ready: bool = False,
) -> list[dict[str, str]]:
    fee = calculate_fee(notification, category)
    critical_review = evaluate_eligibility(notification, profile)

    items: list[dict[str, str]] = [
        {
            "title": "Fee payment",
            "status": "done" if paid else "pending",
            "message": f"Pay the fee before final submission: ₹{fee.total:.2f} ({category}).",
        },
        {
            "title": "Documents ready",
            "status": "done" if docs_ready else "pending",
            "message": "Confirm photo, signature, caste/EWS/domicile proofs, and marksheets are ready.",
        },
        {
            "title": "Eligibility review",
            "status": "done" if critical_review.status == "eligible" else "needs_check",
            "message": "Always confirm the final eligibility in the official notification before paying or submitting.",
        },
    ]

    if notification.last_date:
        items.append({
            "title": "Deadline check",
            "status": "warning",
            "message": f"The last date is {notification.last_date}. Confirm the exact deadline in the official PDF.",
        })

    return items
