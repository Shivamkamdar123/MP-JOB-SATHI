from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class FieldProvenance(BaseModel):
    source_page: Optional[int] = None
    snippet: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    method: Literal["regex", "table", "llm", "ocr"] = "regex"


class QualificationRule(BaseModel):
    level: str
    stream: Optional[str] = None
    min_percent: Optional[float] = None
    required_certificate: Optional[str] = None
    or_above: bool = False


class Post(BaseModel):
    title: Optional[str] = None
    vacancies: Optional[int] = None
    field_provenance: dict[str, FieldProvenance] = Field(default_factory=dict)
    qualification_rules: list[QualificationRule] = Field(default_factory=list)
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    category_vacancies: dict[str, int] = Field(default_factory=dict)
    gender_restrictions: Optional[str] = None
    domicile_required: Optional[bool] = None
    employment_exchange_required: Optional[bool] = None
    pwd_required: Optional[bool] = None
    ex_serviceman_required: Optional[bool] = None


class AgeRelaxationApplicability(BaseModel):
    gender: Optional[str] = None
    pwd: Optional[bool] = None
    ex_serviceman: Optional[bool] = None
    domicile: Optional[bool] = None


class AgeRelaxation(BaseModel):
    category: Optional[str] = None
    years: Optional[int] = None
    applies_to: AgeRelaxationApplicability = Field(default_factory=AgeRelaxationApplicability)
    source_snippet: str = ""


class GovtNotification(BaseModel):
    org: Optional[str] = None
    advertisement_no: Optional[str] = None
    title: Optional[str] = None
    posts: list[Post] = Field(default_factory=list)
    total_vacancies: Optional[int] = None
    category_vacancies: dict[str, int] = Field(default_factory=dict)
    opens_date: Optional[str] = None
    last_date: Optional[str] = None
    fee_last_date: Optional[str] = None
    correction_window: Optional[str] = None
    exam_date: Optional[str] = None
    fee_by_category: dict[str, float] = Field(default_factory=dict)
    portal_charges: Optional[float] = None
    age_limit: dict[str, Optional[str | int]] = {"min": None, "max": None, "as_on_date": None}
    age_relaxation_rules: list[AgeRelaxation] = Field(default_factory=list)
    age_relaxation_combination: Literal["stack", "max_only", "unknown"] = "unknown"
    qualification_rules: list[QualificationRule] = Field(default_factory=list)
    domicile_required: Optional[bool] = None
    employment_exchange_registration_required: Optional[bool] = None
    source_urls: list[str] = Field(default_factory=list)
    notification_pdf_url: Optional[str] = None
    source_kind: Literal["official", "fixture", "lead"] = "fixture"
    verified_at: Optional[str] = None
    verified_by: Literal["auto", "curator"] = "auto"
    discrepancies: list[str] = Field(default_factory=list)
    field_provenance: dict[str, FieldProvenance] = Field(default_factory=dict)
    review_required: bool = False
    status: Optional[Literal["upcoming", "open", "closing_soon", "closed", "exam", "result"]] = None


class UserQualification(BaseModel):
    level: str
    stream: Optional[str] = None
    board: Optional[str] = None
    year: Optional[int] = None
    percentage: Optional[float] = None


class UserProfile(BaseModel):
    name: str
    date_of_birth: str
    gender: str
    category: str = "UR"
    mp_domicile: bool = True
    pwd: bool = False
    ex_serviceman: bool = False
    qualifications: list[UserQualification] = Field(default_factory=list)
    certificates: Optional[list[str]] = None
    experience_years: float = 0.0
    preferred_districts: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    employment_exchange_registered: bool = False
    target_roles: list[str] = Field(default_factory=list)


class EligibilityReason(BaseModel):
    check: str
    result: Literal["pass", "fail", "unknown"]
    message: str


class EligibilityResult(BaseModel):
    status: Literal["eligible", "likely", "not_eligible", "needs_check"]
    reasons: list[EligibilityReason] = Field(default_factory=list)
    matched_post: Optional[str] = None
    matched_posts: list[str] = Field(default_factory=list)
    post_results: list[dict] = Field(default_factory=list)


class FeeBreakdown(BaseModel):
    category: str
    fee: Optional[float] = None
    portal_charges: Optional[float] = None
    total: Optional[float] = None
    needs_check: bool = False
    message: Optional[str] = None


class DocumentValidationResult(BaseModel):
    is_valid: bool
    issues: list[str] = Field(default_factory=list)


class ChecklistItem(BaseModel):
    title: str
    status: str
    message: str


class FormPrefillPlan(BaseModel):
    candidate_name: str
    dob: str
    category: str
    gender: str
    domicile: str
    employment_exchange: str


class CompanySource(BaseModel):
    name: str
    city: str
    industry: str
    careers_url: str
    ats_type: Optional[str] = None
    board_slug: Optional[str] = None
    last_verified: Optional[str] = None
    is_fixture: bool = True


class PrivateJob(BaseModel):
    title: str
    company: str
    city: str
    work_mode: str = "Onsite"
    experience_min: int = 0
    experience_max: Optional[int] = None
    salary_inr_lpa: Optional[float] = None
    employment_type: str = "Full-time"
    ats_type: str = "unknown"
    apply_url: str
    posted_at: str
    first_seen_at: str
    last_seen_at: str
    closed_at: Optional[str] = None
    scam_score: float = 0.0
    required_skills: list[str] = Field(default_factory=list)
    location_scope: str = "MP"
    is_fixture: bool = True


class JobFair(BaseModel):
    title: str
    district: str
    venue: str
    date_time: str
    companies: list[str] = Field(default_factory=list)
    eligibility: str
    documents_to_carry: list[str] = Field(default_factory=list)
    source_url: str
    is_fixture: bool = True


class Application(BaseModel):
    job_title: str
    organization: str
    stage: Literal["saved", "preparing", "ready", "user_submitted", "exam_scheduled", "admit_card", "result", "closed"]
    deadline: Optional[str] = None
    exam_date: Optional[str] = None
    result_date: Optional[str] = None
    notes: list[str] = Field(default_factory=list)
    status: Literal["active", "paused", "done"] = "active"


class Reminder(BaseModel):
    title: str
    kind: str
    date: str
    message: str


class ShareCard(BaseModel):
    title: str
    share_url: str
    message: str


class AdminSnapshot(BaseModel):
    center_name: str
    totals: dict[str, int] = Field(default_factory=dict)
    applications: list[dict] = Field(default_factory=list)
