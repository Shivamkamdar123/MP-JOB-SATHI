from __future__ import annotations

import re
from datetime import datetime, timezone

from app.models import AgeRelaxation, GovtNotification, Post, QualificationRule


def _label_value(lines: list[str], labels: str) -> tuple[str | None, str | None, int | None]:
    pattern = re.compile(rf"^\s*(?:\[PAGE\s+(\d+)\]\s*)?(?:{labels})\s*[:\-]\s*(.+?)\s*$", re.IGNORECASE)
    current_page = 1
    for line in lines:
        page_marker = re.fullmatch(r"\[PAGE\s+(\d+)\]", line, re.IGNORECASE)
        if page_marker:
            current_page = int(page_marker.group(1))
            continue
        match = pattern.match(line)
        if match:
            return match.group(2).strip(), line.strip(), int(match.group(1) or current_page)
    return None, None, None


def extract_notification_from_text(raw_text: str) -> GovtNotification:
    """Extract only facts explicitly labeled in supplied text."""
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    labels = {
        "org": r"organization|organisation|recruiting authority|department|board",
        "advertisement_no": r"advertisement(?:\s+no\.?|\s+number)|notification\s+no\.?",
        "title": r"title|post(?:\s+name)?|name\s+of\s+post",
        "last_date": r"last\s+date(?:\s+to\s+apply)?|closing\s+date",
        "fee_last_date": r"fee\s+last\s+date|last\s+date\s+for\s+fee",
        "opens_date": r"opening\s+date|start\s+date|application\s+starts",
        "exam_date": r"exam(?:ination)?\s+date",
        "correction_window": r"correction\s+window|correction\s+period",
        "total_vacancies": r"total\s+vacancies|total\s+posts",
        "portal_charges": r"portal\s+charges|portal\s+fee",
    }
    extracted: dict[str, str | None] = {}
    provenance = {}
    for field_name, expression in labels.items():
        value, snippet, source_page = _label_value(lines, expression)
        extracted[field_name] = value
        provenance[field_name] = {
            "source_page": source_page,
            "snippet": snippet or "",
            "confidence": 0.9 if value is not None else 0.0,
            "method": "regex",
        }

    total_vacancies = None
    if extracted["total_vacancies"]:
        match = re.search(r"\d[\d,]*", extracted["total_vacancies"])
        if match:
            total_vacancies = int(match.group().replace(",", ""))
            extracted["total_vacancies"] = total_vacancies
        else:
            extracted["total_vacancies"] = None
            provenance["total_vacancies"] = {
                "source_page": None,
                "snippet": "",
                "confidence": 0.0,
                "method": "regex",
            }

    fee_by_category: dict[str, float] = {}
    fee_snippets: list[str] = []
    current_page = 1
    fee_pages: list[int] = []
    for line in lines:
        page_marker = re.fullmatch(r"\[PAGE\s+(\d+)\]", line, re.IGNORECASE)
        if page_marker:
            current_page = int(page_marker.group(1))
            continue
        match = re.search(r"\b(UR|GENERAL|OBC|SC|ST|EWS)\b[^\n]{0,50}?(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)", line, re.IGNORECASE)
        if match:
            category = "UR" if match.group(1).upper() == "GENERAL" else match.group(1).upper()
            fee_by_category[category] = float(match.group(2).replace(",", ""))
            fee_snippets.append(line.strip())
            fee_pages.append(current_page)
    if fee_snippets:
        provenance["fee_by_category"] = {
            "source_page": fee_pages[0],
            "snippet": "\n".join(fee_snippets),
            "confidence": 0.85,
            "method": "regex",
        }
    else:
        provenance["fee_by_category"] = {
            "source_page": None,
            "snippet": "",
            "confidence": 0.0,
            "method": "regex",
        }

    portal_charges = None
    if extracted["portal_charges"]:
        portal_match = re.search(r"\d[\d,]*(?:\.\d{1,2})?", extracted["portal_charges"])
        if portal_match:
            portal_charges = float(portal_match.group().replace(",", ""))
        else:
            provenance["portal_charges"] = {
                "source_page": None,
                "snippet": "",
                "confidence": 0.0,
                "method": "regex",
            }

    last_date = extracted["last_date"]
    if last_date:
        date_match = re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}", last_date)
        last_date = date_match.group() if date_match else None
        if last_date is None:
            extracted.pop("last_date")
            provenance["last_date"] = {
                "source_page": None,
                "snippet": "",
                "confidence": 0.0,
                "method": "regex",
            }

    return GovtNotification(
        org=extracted["org"],
        advertisement_no=extracted["advertisement_no"],
        title=extracted["title"],
        total_vacancies=total_vacancies,
        last_date=last_date,
        opens_date=extracted["opens_date"],
        fee_last_date=extracted["fee_last_date"],
        exam_date=extracted["exam_date"],
        correction_window=extracted["correction_window"],
        fee_by_category=fee_by_category,
        portal_charges=portal_charges,
        field_provenance=provenance,
        source_kind="fixture",
        review_required=True,
    )


def compare_sources(official: GovtNotification, lead: GovtNotification) -> GovtNotification:
    if lead.source_kind != "lead":
        raise ValueError("The comparison source must be labeled source_kind='lead'.")
    comparisons = ("opens_date", "last_date", "fee_by_category", "portal_charges")
    for field_name in comparisons:
        official_value = getattr(official, field_name)
        lead_value = getattr(lead, field_name)
        if official_value != lead_value and (official_value is not None or lead_value is not None):
            message = f"{field_name} differs: official={official_value!r}; lead={lead_value!r}."
            if message not in official.discrepancies:
                official.discrepancies.append(message)
    return official


def get_sample_notifications() -> list[GovtNotification]:
    return [
        GovtNotification(
            org="MPESB",
            advertisement_no="01/2026",
            title="Junior Engineer (Civil)",
            posts=[Post(
                title="Junior Engineer (Civil)",
                vacancies=24,
                qualification_rules=[QualificationRule(level="Diploma", stream="Civil")],
                age_min=18,
                age_max=40,
                domicile_required=True,
            )],
            total_vacancies=24,
            category_vacancies={"UR": 12, "OBC": 6, "SC": 4, "ST": 2},
            fee_by_category={"UR": 200.0, "OBC": 200.0, "SC": 0.0, "ST": 0.0},
            portal_charges=25.0,
            age_limit={"min": 18, "max": 40, "as_on_date": "2026-01-01"},
            source_urls=["https://example.invalid/fixture/notification"],
            notification_pdf_url="https://example.invalid/fixture/notification.pdf",
            source_kind="fixture",
            last_date="2026-12-15",
        ),
        GovtNotification(
            org="MPPSC",
            advertisement_no="02/2026",
            title="State Services Preliminary Exam",
            posts=[
                Post(
                    title="State Services",
                    vacancies=120,
                    qualification_rules=[QualificationRule(level="Graduate")],
                    age_min=21,
                    age_max=40,
                )
            ],
            total_vacancies=120,
            category_vacancies={"UR": 60, "OBC": 30, "SC": 20, "ST": 10},
            fee_by_category={"UR": 500.0, "OBC": 250.0, "SC": 0.0, "ST": 0.0},
            portal_charges=50.0,
            age_limit={"min": 21, "max": 40, "as_on_date": "2026-01-01"},
            age_relaxation_rules=[
                AgeRelaxation(
                    category=None,
                    years=0,
                    source_snippet="As per official notification.",
                )
            ],
            source_urls=["https://mppsc.mp.gov.in/advertisement/02-2026"],
            notification_pdf_url="https://mppsc.mp.gov.in/advertisement/02-2026.pdf",
            source_kind="fixture",
            verified_at=None,
            verified_by="auto",
            status="open",
            last_date="2026-12-15",
        ),
    ]
