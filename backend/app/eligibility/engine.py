from __future__ import annotations

from datetime import date
from typing import Optional

from app.models import EligibilityResult, FeeBreakdown, GovtNotification, Post, UserProfile, UserQualification


def _parse_date(value: str | int | None) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, int):
        value = f"{value}-01-01"
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%Y"):
        try:
            return date.fromisoformat(value) if fmt == "%Y-%m-%d" else None
        except ValueError:
            pass
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def age_on_date(date_of_birth: str, as_on_date: str | int | None) -> int:
    dob = _parse_date(date_of_birth)
    ref = _parse_date(as_on_date)
    if dob is None or ref is None:
        return 0
    return ref.year - dob.year - ((ref.month, ref.day) < (dob.month, dob.day))


def _qualification_matches(profile: UserProfile, rule: UserQualification) -> bool:
    if not profile.qualifications:
        return False
    for q in profile.qualifications:
        if q.level.lower() == rule.level.lower():
            if rule.stream and q.stream and q.stream.lower() != rule.stream.lower():
                continue
            if rule.min_percent is not None and q.percentage is not None and q.percentage < rule.min_percent:
                continue
            return True
    return False


def _check_post(post: Post, profile: UserProfile, notification: GovtNotification) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if post.age_min is not None or post.age_max is not None:
        as_on = notification.age_limit.get("as_on_date") or "2026-01-01"
        age = age_on_date(profile.date_of_birth, as_on)
        if post.age_min is not None and age < post.age_min:
            reasons.append(f"Age minimum is {post.age_min}; you are {age} on the notified as-on date.")
        if post.age_max is not None and age > post.age_max:
            reasons.append(f"Age maximum is {post.age_max}; you are {age} on the notified as-on date.")

    if post.qualification_rules:
        matches = any(_qualification_matches(profile, q) for q in post.qualification_rules)
        if not matches:
            reasons.append("Qualification does not match the notified requirement.")

    if notification.domicile_required and not profile.mp_domicile:
        reasons.append("Madhya Pradesh domicile is required for this recruitment.")

    if notification.employment_exchange_registration_required and not profile.employment_exchange_registered:
        reasons.append("Employment exchange registration is required for this post.")

    return not reasons, reasons


def evaluate_eligibility(notification: GovtNotification, profile: UserProfile) -> EligibilityResult:
    if not notification.posts:
        return EligibilityResult(status="needs_check", reasons=["No post data available. Verify in the official notification."], matched_post=None)

    for post in notification.posts:
        ok, reasons = _check_post(post, profile, notification)
        if ok:
            return EligibilityResult(status="eligible", reasons=["Matches the notified age, qualification, and domicile conditions."], matched_post=post.title)
        if reasons:
            return EligibilityResult(status="not_eligible", reasons=reasons, matched_post=post.title)

    return EligibilityResult(status="likely", reasons=["Some conditions are unclear; verify the official notification before applying."], matched_post=notification.posts[0].title)


def calculate_fee(notification: GovtNotification, category: str) -> FeeBreakdown:
    category_key = category.upper()
    fee = notification.fee_by_category.get(category_key, notification.fee_by_category.get("UR", 0.0))
    portal_charges = notification.portal_charges
    return FeeBreakdown(category=category_key, fee=fee, portal_charges=portal_charges, total=fee + portal_charges)


def get_for_you_feed(profile: UserProfile, notifications: list[GovtNotification]) -> list[dict]:
    ranked: list[dict] = []
    for notification in notifications:
        result = evaluate_eligibility(notification, profile)
        ranked.append({
            "notification": notification.title,
            "org": notification.org,
            "status": result.status,
            "matched_post": result.matched_post,
            "last_date": notification.last_date,
            "source": notification.source_urls[0] if notification.source_urls else notification.notification_pdf_url,
            "reasons": result.reasons,
        })
    ranked.sort(key=lambda x: (0 if x["status"] == "eligible" else 1 if x["status"] == "likely" else 2, x["last_date"] or "9999-12-31"))
    return ranked
