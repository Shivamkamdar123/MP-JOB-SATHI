from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class QualificationRule(BaseModel):
    level: str
    stream: Optional[str] = None
    min_percent: Optional[float] = None
    required_certificate: Optional[str] = None


class Post(BaseModel):
    title: str
    vacancies: int
    qualification_rules: list[QualificationRule] = Field(default_factory=list)
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    category_vacancies: dict[str, int] = Field(default_factory=dict)
    gender_restrictions: Optional[str] = None
    domicile_required: bool = False
    employment_exchange_required: bool = False


class GovtNotification(BaseModel):
    org: str
    advertisement_no: str
    title: str
    posts: list[Post] = Field(default_factory=list)
    total_vacancies: int
    category_vacancies: dict[str, int] = Field(default_factory=dict)
    opens_date: Optional[str] = None
    last_date: Optional[str] = None
    fee_last_date: Optional[str] = None
    correction_window: Optional[str] = None
    exam_date: Optional[str] = None
    fee_by_category: dict[str, float] = Field(default_factory=dict)
    portal_charges: float = 0.0
    age_limit: dict[str, Optional[int]] = {"min": None, "max": None, "as_on_date": None}
    age_relaxation_rules: list[str] = Field(default_factory=list)
    qualification_rules: list[QualificationRule] = Field(default_factory=list)
    domicile_required: bool = False
    employment_exchange_registration_required: bool = False
    source_urls: list[str] = Field(default_factory=list)
    notification_pdf_url: Optional[str] = None
    verified_at: Optional[str] = None
    verified_by: Literal["auto", "curator"] = "auto"
    discrepancies: list[str] = Field(default_factory=list)
    status: Literal["upcoming", "open", "closing_soon", "closed", "exam", "result"] = "open"


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
    experience_years: float = 0.0
    preferred_districts: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    employment_exchange_registered: bool = False
    target_roles: list[str] = Field(default_factory=list)


class EligibilityResult(BaseModel):
    status: Literal["eligible", "likely", "not_eligible", "needs_check"]
    reasons: list[str] = Field(default_factory=list)
    matched_post: Optional[str] = None


class FeeBreakdown(BaseModel):
    category: str
    fee: float
    portal_charges: float
    total: float


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


class JobFair(BaseModel):
    title: str
    district: str
    venue: str
    date_time: str
    companies: list[str] = Field(default_factory=list)
    eligibility: str
    documents_to_carry: list[str] = Field(default_factory=list)
    source_url: str


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
