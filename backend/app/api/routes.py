from fastapi import APIRouter

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
