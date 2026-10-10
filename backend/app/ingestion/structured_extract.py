from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from pydantic import ValidationError

from app.ingestion.mp_sources import extract_notification_from_text
from app.models import FieldProvenance, GovtNotification, Post

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5-5"


def _table_text(tables: list[tuple[int, list[list[str | None]]]]) -> tuple[str, set[str]]:
    lines: list[str] = []
    fields: set[str] = set()
    label_map = {
        "org": ("organization", "organisation", "recruiting authority", "department", "board"),
        "advertisement_no": ("advertisement no", "advertisement number", "notification no"),
        "title": ("title", "post name", "name of post"),
        "last_date": ("last date", "last date to apply", "closing date"),
        "total_vacancies": ("total vacancies", "total posts"),
        "portal_charges": ("portal charges", "portal fee"),
    }
    for page_number, table in tables:
        for row in table:
            cells = [str(cell).strip() for cell in row if cell and str(cell).strip()]
            if len(cells) >= 2:
                label = cells[0].lower().rstrip(":")
                for field, labels in label_map.items():
                    value_is_header = cells[1].lower() in {
                        "vacancy", "vacancies", "posts", "no. of posts", "total posts", "fee", "amount",
                    }
                    if any(label.startswith(candidate) for candidate in labels) and not value_is_header:
                        fields.add(field)
                        lines.append(f"[PAGE {page_number}] {cells[0]}: {cells[1]}")
                        break
            elif cells:
                lines.append(f"[PAGE {page_number}] {cells[0]}")
    return "\n".join(lines), fields


def _posts_from_tables(tables: list[tuple[int, list[list[str | None]]]]) -> tuple[list[Post], int | None, dict[str, int], FieldProvenance | None]:
    posts: list[Post] = []
    category_totals: dict[str, int] = {}
    vacancy_sum = 0
    vacancy_count = 0
    evidence: list[str] = []
    source_page: int | None = None

    for page_number, table in tables:
        for row_index, header_row in enumerate(table):
            headers = [str(cell or "").strip().casefold() for cell in header_row]
            title_index = next((i for i, header in enumerate(headers) if any(word in header for word in ("post name", "name of post", "designation", "position"))), None)
            vacancy_index = next((i for i, header in enumerate(headers) if "vacanc" in header or "no. of post" in header or "number of post" in header), None)
            if title_index is None or vacancy_index is None:
                continue

            category_indices = {
                category: next((i for i, header in enumerate(headers) if header.strip(" .") == category.casefold()), None)
                for category in ("UR", "OBC", "SC", "ST", "EWS")
            }
            for row in table[row_index + 1:]:
                if title_index >= len(row) or vacancy_index >= len(row):
                    continue
                title = str(row[title_index] or "").strip()
                vacancy_raw = str(row[vacancy_index] or "").replace(",", "").strip()
                vacancy_match = re.fullmatch(r"\d+", vacancy_raw)
                if not title or not vacancy_match:
                    continue
                vacancies = int(vacancy_raw)
                snippet = " | ".join(str(cell or "").strip() for cell in row)
                category_vacancies: dict[str, int] = {}
                for category, index in category_indices.items():
                    if index is not None and index < len(row):
                        raw_count = str(row[index] or "").replace(",", "").strip()
                        if raw_count.isdigit():
                            category_vacancies[category] = int(raw_count)
                            category_totals[category] = category_totals.get(category, 0) + int(raw_count)
                posts.append(Post(
                    title=title,
                    vacancies=vacancies,
                    category_vacancies=category_vacancies,
                    field_provenance={
                        "title": FieldProvenance(source_page=page_number, snippet=snippet, confidence=0.85, method="table"),
                        "vacancies": FieldProvenance(source_page=page_number, snippet=snippet, confidence=0.85, method="table"),
                    },
                ))
                vacancy_sum += vacancies
                vacancy_count += 1
                evidence.append(snippet)
                source_page = page_number
            break

    provenance = FieldProvenance(
        source_page=source_page,
        snippet="\n".join(evidence),
        confidence=0.85,
        method="table",
    ) if evidence else None
    return posts, vacancy_sum if vacancy_count else None, category_totals, provenance


def _fees_from_tables(tables: list[tuple[int, list[list[str | None]]]]) -> tuple[dict[str, float], FieldProvenance | None]:
    fees: dict[str, float] = {}
    snippets: list[str] = []
    source_page: int | None = None
    categories = {"ur": "UR", "general": "UR", "obc": "OBC", "sc": "SC", "st": "ST", "ews": "EWS"}
    for page_number, table in tables:
        for row_index, header_row in enumerate(table):
            headers = [str(cell or "").strip().casefold() for cell in header_row]
            category_index = next((i for i, cell in enumerate(headers) if "categor" in cell), None)
            fee_index = next((i for i, cell in enumerate(headers) if "fee" in cell or "amount" in cell), None)
            if category_index is None or fee_index is None:
                continue
            for row in table[row_index + 1:]:
                if category_index >= len(row) or fee_index >= len(row):
                    continue
                category = categories.get(str(row[category_index] or "").strip().casefold())
                amount_match = re.search(r"\d[\d,]*(?:\.\d{1,2})?", str(row[fee_index] or ""))
                if category and amount_match:
                    fees[category] = float(amount_match.group().replace(",", ""))
                    snippets.append(" | ".join(str(cell or "").strip() for cell in row))
                    source_page = page_number
    provenance = FieldProvenance(
        source_page=source_page,
        snippet="\n".join(snippets),
        confidence=0.85,
        method="table",
    ) if snippets else None
    return fees, provenance


def _api_response(text: str, tables: list[tuple[int, list[list[str | None]]]], model: str) -> str:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")
    body = json.dumps({
        "model": model,
        "max_tokens": 5000,
        "system": (
            "Extract only facts explicitly evidenced in the supplied official notification. "
            "Return JSON only, no markdown. Unknown values must be null or empty. "
            "For each populated top-level fact include field_provenance with source_page, "
            "snippet, confidence from 0 to 1, and method 'llm'. Never infer missing facts."
        ),
        "messages": [{"role": "user", "content": json.dumps({"text": text, "tables": tables}, ensure_ascii=False)}],
    }).encode()
    request = urllib.request.Request(
        ANTHROPIC_MESSAGES_URL,
        data=body,
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    return "".join(block.get("text", "") for block in payload.get("content", []) if block.get("type") == "text")


def _recorded_model_response(text: str) -> str | None:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    path = os.getenv("MODEL_RESPONSE_FIXTURES", "evaluation/fixtures/model_responses.json")
    try:
        with open(path, encoding="utf-8") as fixture_file:
            recorded: dict[str, str] = json.load(fixture_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return recorded.get(digest)


def _llm_notification(text: str, tables: list[tuple[int, list[list[str | None]]]], model: str) -> GovtNotification | None:
    for attempt in range(2):
        try:
            response = _recorded_model_response(text) if os.getenv("CI") or os.getenv("APP_ENV") == "test" else _api_response(text, tables, model)
            if response is None:
                return None
            data: Any = json.loads(response)
            notification = GovtNotification.model_validate(data)
            normalized_text = " ".join(text.split()).casefold()
            fact_fields = (
                "org", "advertisement_no", "title", "posts", "total_vacancies",
                "category_vacancies", "opens_date", "last_date", "fee_last_date",
                "correction_window", "exam_date", "fee_by_category", "portal_charges",
                "age_limit", "age_relaxation_rules", "qualification_rules",
                "domicile_required", "employment_exchange_registration_required",
            )
            for field_name in fact_fields:
                value = getattr(notification, field_name)
                provenance = notification.field_provenance.get(field_name)
                snippet = " ".join(provenance.snippet.split()).casefold() if provenance else ""
                has_value = value is not None and value != "" and value != {} and value != []
                supported = bool(snippet and snippet in normalized_text)
                if has_value and not supported:
                    value = [] if isinstance(value, list) else {} if isinstance(value, dict) else None
                    setattr(notification, field_name, value)
                if provenance is not None and (not has_value or not supported):
                    provenance.source_page = None
                    provenance.snippet = ""
                    provenance.confidence = 0.0
                elif provenance is not None:
                    provenance.method = "llm"
            notification.status = None
            return notification
        except (ValueError, ValidationError, urllib.error.URLError, TimeoutError, RuntimeError):
            if attempt:
                return None
    return None


def extract_structured(
    pages: list[str],
    tables: list[Any] | None = None,
    source_url: str | None = None,
    model: str | None = None,
    ocr_pages: list[int] | None = None,
) -> GovtNotification:
    page_text = "\n\n".join(f"[PAGE {index}]\n{text}" for index, text in enumerate(pages, 1))
    page_tables = [item if isinstance(item, tuple) else (1, item) for item in (tables or [])]
    table_text, table_fields = _table_text(page_tables)
    llm_result = _llm_notification(page_text + "\n\n" + table_text, page_tables, model or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)) if os.getenv("ANTHROPIC_API_KEY") else None

    if llm_result is not None:
        notification = llm_result
    else:
        notification = extract_notification_from_text(page_text + "\n" + table_text)
        posts, table_vacancies, table_category_vacancies, table_vacancy_provenance = _posts_from_tables(page_tables)
        if posts:
            notification.posts = posts
            if notification.total_vacancies is None:
                notification.total_vacancies = table_vacancies
                if table_vacancy_provenance is not None:
                    notification.field_provenance["total_vacancies"] = table_vacancy_provenance
            notification.category_vacancies = table_category_vacancies
        table_fees, table_fee_provenance = _fees_from_tables(page_tables)
        if not notification.fee_by_category and table_fees:
            notification.fee_by_category = table_fees
            if table_fee_provenance is not None:
                notification.field_provenance["fee_by_category"] = table_fee_provenance
        for field_name in table_fields:
            field_provenance = notification.field_provenance.get(field_name)
            if field_provenance is not None:
                field_provenance.method = "table"
                field_provenance.confidence = min(field_provenance.confidence, 0.85)

    for field_name in (
        "org", "advertisement_no", "title", "total_vacancies", "opens_date", "last_date",
        "fee_by_category", "portal_charges", "exam_date",
    ):
        notification.field_provenance.setdefault(field_name, FieldProvenance(
            source_page=None,
            snippet="",
            confidence=0.0,
            method="llm" if llm_result is not None else "regex",
        ))

    for field_provenance in notification.field_provenance.values():
        if field_provenance.source_page in (ocr_pages or []):
            field_provenance.method = "ocr"

    if source_url:
        notification.source_urls = [source_url]
        notification.notification_pdf_url = source_url
    notification.review_required = True
    return notification