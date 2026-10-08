from fastapi import APIRouter

from app.assist.form_assist import build_pre_submit_checklist, generate_form_prefill, validate_document_spec
from app.eligibility.engine import calculate_fee, evaluate_eligibility, get_for_you_feed
from app.ingestion.mp_sources import get_sample_notifications
from app.ingestion.private_jobs import get_company_registry, get_job_fair_calendar, get_private_job_fixtures
from app.matching.matcher import match_private_jobs
from app.models import GovtNotification, UserProfile
from app.tracker.manager import build_admin_snapshot, build_reminders, build_share_card, create_application_tracking

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "MP Job Saathi", "phase": "government-core"}


@router.get("/notifications")
def notifications() -> dict:
    return {"items": [n.model_dump(mode="json") for n in get_sample_notifications()]}


@router.post("/eligibility/check")
def eligibility_check(payload: dict) -> dict:
    notification = GovtNotification.model_validate(payload["notification"])
    profile = UserProfile.model_validate(payload["profile"])
    return evaluate_eligibility(notification, profile).model_dump(mode="json")


@router.post("/feed")
def feed(payload: dict) -> dict:
    profile = UserProfile.model_validate(payload["profile"])
    notifications = [GovtNotification.model_validate(item) for item in payload["notifications"]]
    return {"items": get_for_you_feed(profile, notifications)}


@router.post("/fee")
def fee(payload: dict) -> dict:
    notification = GovtNotification.model_validate(payload["notification"])
    category = payload.get("category", "UR")
    return calculate_fee(notification, category).model_dump(mode="json")


@router.post("/assist/prefill")
def assist_prefill(payload: dict) -> dict:
    profile = UserProfile.model_validate(payload["profile"])
    return generate_form_prefill(profile)


@router.post("/assist/validate-document")
def assist_validate_document(payload: dict) -> dict:
    return validate_document_spec(
        file_name=payload.get("file_name", "photo.jpg"),
        file_size_bytes=int(payload.get("file_size_bytes", 150000)),
        width=int(payload.get("width", 350)),
        height=int(payload.get("height", 450)),
        mime_type=payload.get("mime_type", "image/jpeg"),
    )


@router.post("/assist/pre-submit-checklist")
def assist_pre_submit_checklist(payload: dict) -> dict:
    notification = GovtNotification.model_validate(payload["notification"])
    profile = UserProfile.model_validate(payload["profile"])
    return {
        "items": build_pre_submit_checklist(
            profile,
            notification,
            category=payload.get("category", "UR"),
            paid=bool(payload.get("paid", False)),
            docs_ready=bool(payload.get("docs_ready", False)),
        )
    }


@router.get("/companies")
def companies() -> dict:
    return {"items": [company.model_dump(mode="json") for company in get_company_registry()]}


@router.get("/job-fairs")
def job_fairs() -> dict:
    return {"items": [fair.model_dump(mode="json") for fair in get_job_fair_calendar()]}


@router.post("/private-jobs/match")
def private_jobs_match(payload: dict) -> dict:
    profile = UserProfile.model_validate(payload["profile"])
    jobs = [job for job in get_private_job_fixtures()]
    matches = match_private_jobs(profile, jobs)
    return {"items": [{"job": item["job"].model_dump(mode="json"), "score": item["score"], "reasons": item["reasons"], "status": item["status"]} for item in matches]}


@router.post("/applications")
def applications(payload: dict) -> dict:
    tracker = create_application_tracking(
        job_title=payload.get("job_title", "New Application"),
        company=payload.get("company", "Unknown"),
        stage=payload.get("stage", "saved"),
        deadline=payload.get("deadline"),
        exam_date=payload.get("exam_date"),
    )
    return tracker


@router.post("/applications/reminders")
def application_reminders(payload: dict) -> dict:
    reminders = build_reminders(
        deadline=payload.get("deadline"),
        exam_date=payload.get("exam_date"),
        result_date=payload.get("result_date"),
    )
    return {"items": reminders}


@router.post("/share-card")
def share_card(payload: dict) -> dict:
    return build_share_card(payload.get("title", "Public job card"), payload.get("share_url", "https://mpjobs.example/job"))


@router.post("/admin/snapshot")
def admin_snapshot(payload: dict) -> dict:
    center_name = payload.get("center_name", "MP Job Saathi center")
    apps = payload.get("applications", [])
    return build_admin_snapshot(center_name, apps)
