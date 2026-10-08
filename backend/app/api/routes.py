from fastapi import APIRouter

from app.assist.form_assist import build_pre_submit_checklist, generate_form_prefill, validate_document_spec
from app.eligibility.engine import calculate_fee, evaluate_eligibility, get_for_you_feed
from app.ingestion.mp_sources import get_sample_notifications
from app.models import GovtNotification, UserProfile

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
