from __future__ import annotations

import urllib.error
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.assist.form_assist import build_pre_submit_checklist, generate_form_prefill, validate_document_spec
from app.core.config import BASE_DIR
from app.db.database import get_session
from app.db.orm import ApplicationRecord
from app.db.repositories import ApplicationRepository, AuditRepository, CatalogRepository, NotificationRepository, UserRepository
from app.eligibility.engine import calculate_fee, evaluate_eligibility, get_for_you_feed
from app.ingestion.mp_sources import extract_notification_from_text
from app.ingestion.notification_ingest import ingest_pdf_url
from app.ingestion.source_policy import SourcePolicy
from app.matching.matcher import match_private_jobs
from app.models import Application, ChecklistItem
from app.tracker.manager import build_admin_snapshot, build_reminders, build_share_card
from app.api.schemas import (
    AdminSnapshotRequest,
    AdminSnapshotResponse,
    AuditEventListResponse,
    ApplicationCreateRequest,
    ApplicationListResponse,
    ApplicationResponse,
    ChecklistResponse,
    CompanyListResponse,
    CuratorEditRequest,
    DocumentValidationRequest,
    DocumentValidationResponse,
    EligibilityCheckRequest,
    EligibilityResponse,
    ExtractionRequest,
    FeeRequest,
    FeeResponse,
    FeedItem,
    FeedRequest,
    FormPrefillResponse,
    HealthResponse,
    ItemsResponse,
    JobFairListResponse,
    MessageResponse,
    NotificationCreatedResponse,
    NotificationDetailResponse,
    PDFExtractionRequest,
    PDFExtractionResponse,
    NotificationListResponse,
    PreSubmitChecklistRequest,
    PrefillRequest,
    PrivateJobsMatchRequest,
    PrivateJobMatchResponse,
    ProfileCreateRequest,
    ProfileResponse,
    ReminderListResponse,
    ReminderRequest,
    ReminderResponse,
    ShareCardRequest,
    ShareCardResponse,
    VerificationRequest,
)

router = APIRouter()


def _application_response(record: ApplicationRecord) -> ApplicationResponse:
    return ApplicationResponse(
        id=record.id,
        user_id=record.user_id,
        notification_id=record.notification_id,
        job_title=record.job_title,
        organization=record.organization,
        stage=record.stage,
        status=record.status,
        data=record.data,
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="MP Job Saathi", phase="government-core")


@router.get("/notifications", response_model=NotificationListResponse)
def notifications(session: Session = Depends(get_session)) -> NotificationListResponse:
    return NotificationListResponse(items=NotificationRepository(session).list())


@router.get("/notifications/{notification_id}", response_model=NotificationDetailResponse)
def notification_detail(notification_id: int, session: Session = Depends(get_session)) -> NotificationDetailResponse:
    notification = NotificationRepository(session).get(notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationDetailResponse(id=notification_id, notification=notification)


@router.post("/notifications/extract", response_model=NotificationCreatedResponse, status_code=status.HTTP_201_CREATED)
def extract_notification(request: ExtractionRequest, session: Session = Depends(get_session)) -> NotificationCreatedResponse:
    notification = extract_notification_from_text(request.raw_text)
    record = NotificationRepository(session).add_extracted(notification, actor=request.actor)
    return NotificationCreatedResponse(id=record.id, notification=notification)


@router.post("/notifications/extract-pdf", response_model=PDFExtractionResponse, status_code=status.HTTP_200_OK)
def extract_notification_pdf(request: PDFExtractionRequest, session: Session = Depends(get_session)) -> PDFExtractionResponse:
    try:
        notification_id, notification, changed = ingest_pdf_url(
            session,
            request.pdf_url,
            listing_url=request.listing_url,
            policy=SourcePolicy(),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise HTTPException(status_code=502, detail=f"Official source fetch failed: {exc}") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return PDFExtractionResponse(id=notification_id, notification=notification, changed=changed)


@router.post("/notifications/{notification_id}/verify", response_model=NotificationCreatedResponse)
def verify_notification(
    notification_id: int,
    request: VerificationRequest,
    session: Session = Depends(get_session),
) -> NotificationCreatedResponse:
    notification = NotificationRepository(session).verify(notification_id, request.actor, request.source_url)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationCreatedResponse(id=notification_id, notification=notification)


@router.patch("/notifications/{notification_id}", response_model=NotificationCreatedResponse)
def edit_notification(
    notification_id: int,
    request: CuratorEditRequest,
    session: Session = Depends(get_session),
) -> NotificationCreatedResponse:
    notification = NotificationRepository(session).curator_edit(notification_id, request.changes, request.actor)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationCreatedResponse(id=notification_id, notification=notification)


@router.post("/eligibility/check", response_model=EligibilityResponse)
def eligibility_check(request: EligibilityCheckRequest, session: Session = Depends(get_session)) -> EligibilityResponse:
    notification = NotificationRepository(session).get(request.notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return evaluate_eligibility(notification, request.profile)


@router.post("/feed", response_model=ItemsResponse[FeedItem])
def feed(request: FeedRequest, session: Session = Depends(get_session)) -> ItemsResponse[FeedItem]:
    records = NotificationRepository(session).list_with_ids(include_closed=False)
    notifications = [notification for _, notification in records]
    ids = {id(notification): notification_id for notification_id, notification in records}
    items = get_for_you_feed(request.profile, notifications, notification_ids=ids)
    return ItemsResponse[FeedItem](items=[FeedItem.model_validate(item) for item in items])


@router.get("/stats")
def stats() -> dict:
    results_dir = BASE_DIR.parent / "evaluation" / "results"
    files = []
    if results_dir.exists():
        for result_path in sorted(results_dir.glob("*.json")):
            try:
                data = json.loads(result_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            files.append({"name": result_path.name, "generated_at": data.get("generated_at"), "data": data})
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "items": files}


@router.post("/fee", response_model=FeeResponse)
def fee(request: FeeRequest, session: Session = Depends(get_session)) -> FeeResponse:
    notification = NotificationRepository(session).get(request.notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return calculate_fee(notification, request.category)


@router.post("/profiles", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(request: ProfileCreateRequest, session: Session = Depends(get_session)) -> ProfileResponse:
    profile_record = UserRepository(session).save_profile(request.profile, email=request.email)
    return ProfileResponse(user_id=profile_record.user_id, profile=request.profile)


@router.post("/assist/prefill", response_model=FormPrefillResponse)
def assist_prefill(request: PrefillRequest) -> FormPrefillResponse:
    return FormPrefillResponse.model_validate(generate_form_prefill(request.profile))


@router.post("/assist/validate-document", response_model=DocumentValidationResponse)
def assist_validate_document(request: DocumentValidationRequest) -> DocumentValidationResponse:
    result = validate_document_spec(
        file_name=request.file_name,
        file_size_bytes=request.file_size_bytes,
        width=request.width,
        height=request.height,
        mime_type=request.mime_type,
    )
    return DocumentValidationResponse.model_validate(result)


@router.post("/assist/pre-submit-checklist", response_model=ChecklistResponse)
def assist_pre_submit_checklist(request: PreSubmitChecklistRequest, session: Session = Depends(get_session)) -> ChecklistResponse:
    notification = NotificationRepository(session).get(request.notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    items = build_pre_submit_checklist(
        request.profile,
        notification,
        category=request.category,
        paid=request.paid,
        docs_ready=request.docs_ready,
    )
    return ChecklistResponse(items=[ChecklistItem.model_validate(item) for item in items])


@router.get("/companies", response_model=CompanyListResponse)
def companies(session: Session = Depends(get_session)) -> CompanyListResponse:
    return CompanyListResponse(items=CatalogRepository(session).list_companies())


@router.get("/job-fairs", response_model=JobFairListResponse)
def job_fairs(session: Session = Depends(get_session)) -> JobFairListResponse:
    return JobFairListResponse(items=CatalogRepository(session).list_job_fairs())


@router.post("/private-jobs/match", response_model=PrivateJobMatchResponse)
def private_jobs_match(request: PrivateJobsMatchRequest, session: Session = Depends(get_session)) -> PrivateJobMatchResponse:
    jobs = CatalogRepository(session).list_private_jobs()
    matches = match_private_jobs(request.profile, jobs)
    return PrivateJobMatchResponse(items=[{
        "job": item["job"],
        "score": item["score"],
        "reasons": item["reasons"],
        "status": item["status"],
    } for item in matches])


@router.post("/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(request: ApplicationCreateRequest, session: Session = Depends(get_session)) -> ApplicationResponse:
    application = Application.model_validate(request.model_dump(exclude={"user_id", "notification_id"}))
    if request.notification_id is not None and NotificationRepository(session).get(request.notification_id) is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if request.user_id is not None and not UserRepository(session).exists(request.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    record = ApplicationRepository(session).create(application, request.user_id, request.notification_id)
    return _application_response(record)


@router.get("/applications", response_model=ApplicationListResponse)
def list_applications(user_id: int | None = None, session: Session = Depends(get_session)) -> ApplicationListResponse:
    return ApplicationListResponse(items=[_application_response(item) for item in ApplicationRepository(session).list(user_id)])


@router.post("/applications/reminders", response_model=ReminderListResponse, status_code=status.HTTP_201_CREATED)
def application_reminders(request: ReminderRequest, session: Session = Depends(get_session)) -> ReminderListResponse:
    if request.user_id is not None and not UserRepository(session).exists(request.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if request.application_id is not None and not ApplicationRepository(session).exists(request.application_id):
        raise HTTPException(status_code=404, detail="Application not found")
    reminders = build_reminders(request.deadline, request.exam_date, request.result_date)
    records = ApplicationRepository(session).add_reminders(reminders, request.user_id, request.application_id)
    return ReminderListResponse(items=[ReminderResponse(
        id=item.id,
        title=item.title,
        kind=item.kind,
        date=item.due_date,
        message=item.message,
    ) for item in records])


@router.post("/share-card", response_model=ShareCardResponse)
def share_card(request: ShareCardRequest) -> ShareCardResponse:
    return ShareCardResponse.model_validate(build_share_card(request.title, request.share_url))


@router.post("/admin/snapshot", response_model=AdminSnapshotResponse)
def admin_snapshot(request: AdminSnapshotRequest) -> AdminSnapshotResponse:
    return AdminSnapshotResponse.model_validate(build_admin_snapshot(request.center_name, request.applications))


@router.get("/audit-events", response_model=AuditEventListResponse)
def audit_events(session: Session = Depends(get_session)) -> AuditEventListResponse:
    records = AuditRepository(session).list()
    items = [{
        "id": record.id,
        "event_type": record.event_type,
        "entity_type": record.entity_type,
        "entity_id": record.entity_id,
        "actor": record.actor,
        "payload": record.payload,
        "created_at": record.created_at.isoformat(),
    } for record in records]
    return AuditEventListResponse(items=items)
