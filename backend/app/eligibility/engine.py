from __future__ import annotations

from datetime import date
from typing import Any

from app.eligibility.dates import age_on_date, days_left, is_closing_soon, parse_date
from app.eligibility.qualifications import qualification_fits_profile
from app.models import AgeRelaxation, EligibilityReason, EligibilityResult, FeeBreakdown, GovtNotification, Post, UserProfile

STATUS_ORDER = {"eligible": 4, "likely": 3, "needs_check": 2, "not_eligible": 1}
SOFT_CONFIDENCE_THRESHOLD = 0.7


def _reason(check: str, result: str, message: str) -> EligibilityReason:
    return EligibilityReason(check=check, result=result, message=message)


def _normalise_category(value: str | None) -> str:
    return (value or "").strip().upper()


def _rule_applies(rule: AgeRelaxation, profile: UserProfile) -> bool | None:
    if rule.category:
        if not profile.category:
            return None
        if rule.category.upper() != profile.category.upper():
            return False

    for key, expected in rule.applies_to.model_dump(exclude_none=True).items():
        actual = {
            "gender": profile.gender,
            "pwd": profile.pwd,
            "ex_serviceman": profile.ex_serviceman,
            "domicile": profile.mp_domicile,
        }[key]
        if actual is None:
            return None
        if isinstance(expected, str):
            if str(actual).lower() != expected.lower():
                return False
        elif actual != expected:
            return False
    return True


def _applicable_relaxations(notification: GovtNotification, profile: UserProfile) -> tuple[list[AgeRelaxation], bool]:
    rules: list[AgeRelaxation] = []
    has_unknown_applicability = False
    for rule in notification.age_relaxation_rules:
        applies = _rule_applies(rule, profile)
        if applies is True:
            rules.append(rule)
        elif applies is None:
            has_unknown_applicability = True
    return rules, has_unknown_applicability


def _resolve_age_bounds(post: Post, notification: GovtNotification, profile: UserProfile) -> tuple[int | None, int | None, int, list[EligibilityReason]]:
    min_age = post.age_min if post.age_min is not None else notification.age_limit.get("min")
    max_age = post.age_max if post.age_max is not None else notification.age_limit.get("max")
    rules, has_unknown_applicability = _applicable_relaxations(notification, profile)
    if has_unknown_applicability:
        return None, None, 0, [
            _reason("age_relaxation", "unknown", "Profile data needed to determine age-relaxation eligibility is missing.")
        ]
    relaxation_years = 0
    if rules:
        if any(rule.years is None for rule in rules):
            return None, None, 0, [
                _reason("age_relaxation", "unknown", "An applicable age-relaxation amount is missing; verify the official notification.")
            ]
        if notification.age_relaxation_combination == "stack":
            relaxation_years = sum(rule.years for rule in rules)
        elif notification.age_relaxation_combination == "max_only":
            relaxation_years = max(rule.years for rule in rules)
        elif len(rules) == 1:
            relaxation_years = rules[0].years
        else:
            return None, None, 0, [
                _reason(
                    "age",
                    "unknown",
                    "Multiple age relaxations apply, but the governing notification does not specify how to combine them.",
                )
            ]

    if max_age is not None:
        max_age = max_age + relaxation_years
    return min_age, max_age, relaxation_years, []


def _check_age_constraints(post: Post, notification: GovtNotification, profile: UserProfile) -> tuple[str, list[EligibilityReason]]:
    reasons: list[EligibilityReason] = []
    min_age = post.age_min if post.age_min is not None else notification.age_limit.get("min")
    max_age = post.age_max if post.age_max is not None else notification.age_limit.get("max")
    if min_age is None or max_age is None:
        return "needs_check", [
            _reason("age", "unknown", "The notified age range is incomplete; verify the official notification.")
        ]
    as_on_raw = notification.age_limit.get("as_on_date")
    if as_on_raw is None:
        return "needs_check", [
            _reason("age", "unknown", "The age limit as-on date is missing from the official notification; verify before applying.")
        ]

    _, is_ambiguous = parse_date(as_on_raw)
    if is_ambiguous:
        return "needs_check", [
            _reason("age", "unknown", f"The age limit as-on date is ambiguous because only a year was provided ({as_on_raw}); verify the official notification.")
        ]

    try:
        age = age_on_date(profile.date_of_birth, as_on_raw)
    except ValueError as exc:
        return "needs_check", [_reason("age", "unknown", str(exc))]

    if (
        max_age is not None
        and age > max_age
        and _normalise_category(profile.category) not in {"", "UR", "GENERAL"}
        and not notification.age_relaxation_rules
    ):
        return "needs_check", [
            _reason("age_relaxation", "unknown", "The candidate exceeds the base age limit, but no non-UR relaxation data was parsed.")
        ]

    min_age, max_age, _, extra_reasons = _resolve_age_bounds(post, notification, profile)
    if extra_reasons:
        return "needs_check", extra_reasons

    if min_age is not None and age < min_age:
        reasons.append(_reason("age", "fail", f"Minimum age is {min_age}; your age is {age} as on the notified date."))
    elif min_age is not None:
        reasons.append(_reason("age", "pass", f"Minimum age requirement is satisfied: {age} >= {min_age}."))

    if max_age is not None and age > max_age:
        reasons.append(_reason("age", "fail", f"Maximum age is {max_age}; your age is {age} as on the notified date."))
    elif max_age is not None:
        reasons.append(_reason("age", "pass", f"Maximum age requirement is satisfied: {age} <= {max_age}."))

    if any(reason.result == "fail" for reason in reasons):
        return "not_eligible", reasons
    if any(reason.result == "unknown" for reason in reasons):
        return "needs_check", reasons
    return "eligible", reasons


def _evaluate_qualification(post: Post, profile: UserProfile) -> tuple[str, list[EligibilityReason]]:
    rules = list(post.qualification_rules)
    if not rules:
        return "needs_check", [
            _reason("qualification", "unknown", "No qualification requirement is available for this post; verify the official notification.")
        ]

    reasons: list[EligibilityReason] = []
    pass_found = False
    unknown_found = False
    fail_found = False

    for rule in rules:
        ok, message, unknown = qualification_fits_profile(
            profile,
            rule.level,
            rule.stream,
            rule.min_percent,
            rule.or_above,
            rule.required_certificate,
        )
        if ok:
            pass_found = True
            reasons.append(_reason("qualification", "pass", message or f"Qualification rule satisfied: {rule.level}.") )
        elif unknown:
            unknown_found = True
            reasons.append(_reason("qualification", "unknown", message or f"Qualification details are incomplete for {rule.level}."))
        else:
            fail_found = True
            reasons.append(_reason("qualification", "fail", message or f"Qualification rule failed for {rule.level}."))

    if pass_found:
        return "eligible", [reason for reason in reasons if reason.result == "pass"]
    if unknown_found:
        return "needs_check", reasons
    return "not_eligible", reasons


def _check_post(post: Post, notification: GovtNotification, profile: UserProfile) -> tuple[str, list[EligibilityReason]]:
    reasons: list[EligibilityReason] = []

    if post.gender_restrictions:
        allowed = str(post.gender_restrictions).lower()
        if allowed not in {"male", "female", "any"}:
            return "not_eligible", [_reason("gender", "fail", f"Unsupported gender restriction in the notification: {post.gender_restrictions}.")]
        if profile.gender is None:
            reasons.append(_reason("gender", "unknown", "Gender is missing from the profile; verify this post's restriction."))
        elif allowed != "any" and str(profile.gender).lower() != allowed:
            return "not_eligible", [_reason("gender", "fail", f"This post is restricted to {allowed} candidates; your gender is {profile.gender}.")]
        else:
            reasons.append(_reason("gender", "pass", f"Gender restriction is satisfied for {profile.gender}."))

    if post.pwd_required and profile.pwd is None:
        reasons.append(_reason("pwd", "unknown", "PwD status is missing from the profile; verify this post's restriction."))
    elif post.pwd_required and not profile.pwd:
        return "not_eligible", [_reason("pwd", "fail", "This post is reserved for persons with disabilities and your profile does not show PwD status.")]
    elif post.pwd_required:
        reasons.append(_reason("pwd", "pass", "PwD status satisfies this post's restriction."))
    if post.ex_serviceman_required and profile.ex_serviceman is None:
        reasons.append(_reason("ex_serviceman", "unknown", "Ex-serviceman status is missing from the profile; verify this post's restriction."))
    elif post.ex_serviceman_required and not profile.ex_serviceman:
        return "not_eligible", [_reason("ex_serviceman", "fail", "This post is reserved for ex-servicemen and your profile does not show that status.")]
    elif post.ex_serviceman_required:
        reasons.append(_reason("ex_serviceman", "pass", "Ex-serviceman status satisfies this post's restriction."))

    age_status, age_reasons = _check_age_constraints(post, notification, profile)
    reasons.extend(age_reasons)

    qualification_status, qualification_reasons = _evaluate_qualification(post, profile)
    reasons.extend(qualification_reasons)

    if notification.domicile_required or post.domicile_required:
        if profile.mp_domicile is None:
            reasons.append(_reason("domicile", "unknown", "Domicile status is missing from the profile; verify the requirement."))
        elif not profile.mp_domicile:
            return "not_eligible", [_reason("domicile", "fail", "Madhya Pradesh domicile is required for this recruitment.")]
        else:
            reasons.append(_reason("domicile", "pass", "Madhya Pradesh domicile requirement is satisfied."))

    if notification.employment_exchange_registration_required or post.employment_exchange_required:
        if profile.employment_exchange_registered is None:
            reasons.append(_reason("employment_exchange", "unknown", "Employment exchange status is missing from the profile; verify the requirement."))
        elif not profile.employment_exchange_registered:
            return "not_eligible", [_reason("employment_exchange", "fail", "Employment exchange registration is required for this recruitment.")]
        else:
            reasons.append(_reason("employment_exchange", "pass", "Employment exchange registration requirement is satisfied."))

    if age_status == "not_eligible" or qualification_status == "not_eligible":
        return "not_eligible", reasons
    if age_status == "needs_check" or qualification_status == "needs_check" or any(reason.result == "unknown" for reason in reasons):
        return "needs_check", reasons
    if age_status == "likely" or qualification_status == "likely":
        return "likely", reasons
    title_provenance = post.field_provenance.get("title")
    if title_provenance and title_provenance.confidence < SOFT_CONFIDENCE_THRESHOLD:
        reasons.append(_reason(
            "role_relevance",
            "unknown",
            f"Post-title confidence is {title_provenance.confidence:.2f}; role relevance is a soft check and needs confirmation.",
        ))
        return "likely", reasons
    return "eligible", reasons


def evaluate_eligibility(notification: GovtNotification, profile: UserProfile) -> EligibilityResult:
    if not notification.posts:
        return EligibilityResult(
            status="needs_check",
            reasons=[_reason("notification", "unknown", "No post data is available in the official notification; verify before applying.")],
            matched_post=None,
            matched_posts=[],
            post_results=[],
        )

    post_results: list[dict[str, Any]] = []
    valid_statuses: list[str] = []
    matched_posts: list[str] = []

    for post in notification.posts:
        status, reasons = _check_post(post, notification, profile)
        records = [{
            "title": post.title,
            "status": status,
            "reasons": [reason.model_dump(mode="json") for reason in reasons],
        }]
        post_results.extend(records)
        valid_statuses.append(status)
        if status == "eligible":
            matched_posts.append(post.title)

    best_status = max(valid_statuses, key=lambda item: STATUS_ORDER.get(item, 0), default="not_eligible")
    if notification.review_required:
        best_status = "needs_check"
    if best_status == "eligible" and matched_posts:
        selected_title = matched_posts[0]
    elif post_results:
        selected_title = post_results[0]["title"]
    else:
        selected_title = None

    selected_reasons = []
    for item in post_results:
        if item["title"] == selected_title:
            selected_reasons = [EligibilityReason.model_validate(reason) for reason in item["reasons"]]
            break
    if not selected_reasons and post_results:
        selected_reasons = [EligibilityReason.model_validate(reason) for reason in post_results[0]["reasons"]]
    if notification.review_required:
        selected_reasons.append(_reason(
            "verification",
            "unknown",
            "This notification was auto-extracted; verify its details before applying.",
        ))

    return EligibilityResult(
        status=best_status,
        reasons=selected_reasons,
        matched_post=selected_title,
        matched_posts=matched_posts,
        post_results=post_results,
    )


def calculate_fee(notification: GovtNotification, category: str) -> FeeBreakdown:
    normalized = _normalise_category(category)
    fee_value = notification.fee_by_category.get(normalized)
    if fee_value is None:
        return FeeBreakdown(
            category=normalized,
            fee=None,
            portal_charges=notification.portal_charges,
            total=None,
            needs_check=True,
            message=f"Fee category {normalized} is not in the official notification; verify the fee table before paying.",
        )

    fee = float(fee_value)
    portal_charges = notification.portal_charges
    return FeeBreakdown(
        category=normalized,
        fee=fee,
        portal_charges=portal_charges,
        total=fee + portal_charges if portal_charges is not None else None,
        needs_check=portal_charges is None,
        message="Portal charges are not stated; verify the final payable amount." if portal_charges is None else None,
    )


def get_for_you_feed(
    profile: UserProfile,
    notifications: list[GovtNotification],
    notification_ids: dict[int, int] | None = None,
    today: str | date | None = None,
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for notification in notifications:
        if notification.status == "closed":
            continue
        result = evaluate_eligibility(notification, profile)
        remaining = days_left(notification, today if today is not None else date.today())
        ranked.append({
            "id": (notification_ids or {}).get(id(notification)),
            "notification": notification.title,
            "org": notification.org,
            "status": result.status,
            "matched_post": result.matched_post,
            "matched_posts": result.matched_posts,
            "last_date": notification.last_date,
            "days_left": remaining,
            "source": notification.source_urls[0] if notification.source_urls else notification.notification_pdf_url,
            "reasons": [reason.model_dump(mode="json") for reason in result.reasons],
            "review_required": notification.review_required,
            "verification_notice": "Auto-extracted, verify before applying." if notification.review_required else None,
            "verification_status": (
                "fixture" if notification.source_kind == "fixture"
                else "verified" if notification.verified_by == "curator"
                else "auto"
            ),
        })

    ranked.sort(
        key=lambda item: (
            -STATUS_ORDER.get(item["status"], 0),
            item["days_left"] if item["days_left"] is not None else 9_999_999,
            item["notification"] or "",
        )
    )
    return ranked


__all__ = [
    "evaluate_eligibility",
    "calculate_fee",
    "get_for_you_feed",
    "days_left",
    "is_closing_soon",
    "parse_date",
    "age_on_date",
]
