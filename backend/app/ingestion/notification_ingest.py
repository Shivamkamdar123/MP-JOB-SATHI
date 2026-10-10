from __future__ import annotations

import hashlib

from sqlalchemy.orm import Session

from app.db.repositories import CatalogRepository, NotificationRepository
from app.ingestion.pdf_extract import extract_pdf
from app.ingestion.source_policy import SourcePolicy
from app.ingestion.structured_extract import extract_structured
from app.models import GovtNotification


def ingest_pdf_url(
    session: Session,
    pdf_url: str,
    listing_url: str | None = None,
    policy: SourcePolicy | None = None,
    fetcher=None,
) -> tuple[int, GovtNotification, bool]:
    source_policy = policy or SourcePolicy()
    catalog = CatalogRepository(session)
    listing_bytes = source_policy.fetch(listing_url, fetcher) if listing_url and fetcher else (
        source_policy.fetch(listing_url) if listing_url else None
    )
    pdf_bytes = source_policy.fetch(pdf_url, fetcher) if fetcher else source_policy.fetch(pdf_url)
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
    listing_hash = hashlib.sha256(listing_bytes).hexdigest() if listing_bytes is not None else None

    cached_hash = catalog.get_source_hash(pdf_url)
    cached_listing_hash = catalog.get_source_hash(listing_url) if listing_url else None
    changed = cached_hash != pdf_hash or (listing_url is not None and cached_listing_hash != listing_hash)
    if not changed:
        cached_record = NotificationRepository(session).get_record_by_pdf_url(pdf_url)
        if cached_record is not None:
            notification = NotificationRepository(session).get(cached_record.id)
            if notification is not None:
                return cached_record.id, notification, False

    extracted_pdf = extract_pdf(pdf_bytes)
    notification = extract_structured(
        extracted_pdf.pages,
        extracted_pdf.tables,
        source_url=pdf_url,
        ocr_pages=extracted_pdf.ocr_pages,
    )
    notification.source_kind = "official"
    notification.review_required = notification.review_required or bool(extracted_pdf.ocr_skipped_pages)
    record = NotificationRepository(session).add_extracted(notification)
    catalog.record_source_hash(pdf_url, pdf_hash, notification_id=record.id)
    if listing_url and listing_hash:
        catalog.record_source_hash(listing_url, listing_hash, notification_id=record.id)
    session.commit()
    return record.id, notification, True