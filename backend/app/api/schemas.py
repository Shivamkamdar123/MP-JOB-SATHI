from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from app.models import (
    AdminSnapshot,
    Application,
    ChecklistItem,
    CompanySource,
    DocumentValidationResult,
    EligibilityResult,
    FeeBreakdown,
    FormPrefillPlan,
    GovtNotification,
    JobFair,
    PrivateJob,
    Reminder,
    ShareCard,
    UserProfile,
)

T = TypeVar("T")


class ItemsResponse(BaseModel, Generic[T]):
    items: list[T]


class HealthResponse(BaseModel):
    status: str
    service: str
    phase: str


class ProfileCreateRequest(BaseModel):
    profile: UserProfile
    email: str | None = None


class ProfileResponse(BaseModel):
    user_id: int
    profile: UserProfile


class EligibilityCheckRequest(BaseModel):
    notification_id: int
    profile: UserProfile


class FeedRequest(BaseModel):
    profile: UserProfile


class PrefillRequest(BaseModel):
    profile: UserProfile


class FeedItem(BaseModel):
    id: int | None = None
    notification: str | None = None
    org: str | None = None
    status: str
    matched_post: str | None = None
    matched_posts: list[str] = Field(default_factory=list)
    last_date: str | None = None
    days_left: int | None = None
    source: str | None = None
    reasons: list[dict[str, Any]] = Field(default_factory=list)
    review_required: bool = False
    verification_notice: str | None = None
    verification_status: str = "auto"


class FeeRequest(BaseModel):
    notification_id: int
    category: str = "UR"


class PrefillRequest(BaseModel):
    profile: UserProfile


class DocumentValidationRequest(BaseModel):
    file_name: str = "photo.jpg"
    file_size_bytes: int = Field(default=150000, ge=0)
    width: int = Field(default=350, ge=0)
    height: int = Field(default=450, ge=0)
    mime_type: str = "image/jpeg"


class PreSubmitChecklistRequest(BaseModel):
    notification_id: int
    profile: UserProfile
    category: str = "UR"
    paid: bool = False
    docs_ready: bool = False


class PrivateJobsMatchRequest(BaseModel):
    profile: UserProfile


class ApplicationCreateRequest(Application):
    user_id: int | None = None
    notification_id: int | None = None


class ApplicationResponse(BaseModel):
    id: int
    user_id: int | None
    notification_id: int | None
    job_title: str
    organization: str
    stage: str
    status: str
    data: dict[str, Any]


class ReminderRequest(BaseModel):
    deadline: str | None = None
    exam_date: str | None = None
    result_date: str | None = None
    user_id: int | None = None
    application_id: int | None = None


class ReminderResponse(BaseModel):
    id: int
    title: str
    kind: str
    date: str
    message: str


class ShareCardRequest(BaseModel):
    title: str = "Public job card"
    share_url: str = "https://mpjobs.example/job"


class AdminSnapshotRequest(BaseModel):
    center_name: str = "MP Job Saathi center"
    applications: list[dict[str, Any]] = Field(default_factory=list)


class ExtractionRequest(BaseModel):
    raw_text: str = Field(min_length=1)
    actor: str = "system"


class PDFExtractionRequest(BaseModel):
    pdf_url: str
    listing_url: str | None = None
    actor: str = "system"


class NotificationCreatedResponse(BaseModel):
    id: int
    notification: GovtNotification


class NotificationDetailResponse(NotificationCreatedResponse):
    pass


class PDFExtractionResponse(NotificationCreatedResponse):
    changed: bool


class VerificationRequest(BaseModel):
    actor: str = "curator"
    source_url: str | None = None


class CuratorEditRequest(BaseModel):
    actor: str = "curator"
    changes: dict[str, Any] = Field(min_length=1)


class AuditEventResponse(BaseModel):
    id: int
    event_type: str
    entity_type: str
    entity_id: str
    actor: str
    payload: dict[str, Any]
    created_at: str


class AuditEventListResponse(BaseModel):
    items: list[AuditEventResponse]


class NotificationListResponse(BaseModel):
    items: list[GovtNotification]


class CompanyListResponse(BaseModel):
    items: list[CompanySource]


class JobFairListResponse(BaseModel):
    items: list[JobFair]


class PrivateJobMatchItem(BaseModel):
    job: PrivateJob
    score: float
    reasons: list[str]
    status: str


class PrivateJobMatchResponse(BaseModel):
    items: list[PrivateJobMatchItem]


class ChecklistResponse(BaseModel):
    items: list[ChecklistItem]


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]


class ReminderListResponse(BaseModel):
    items: list[ReminderResponse]


class ShareCardResponse(ShareCard):
    pass


class AdminSnapshotResponse(AdminSnapshot):
    pass


class DocumentValidationResponse(DocumentValidationResult):
    pass


class FormPrefillResponse(FormPrefillPlan):
    pass


class FeeResponse(FeeBreakdown):
    pass


class EligibilityResponse(EligibilityResult):
    pass


class MessageResponse(BaseModel):
    message: str
