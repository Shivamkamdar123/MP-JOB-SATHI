import json
from pathlib import Path

import pytest

from app.eligibility.engine import age_on_date, calculate_fee, days_left, evaluate_eligibility, get_for_you_feed, is_closing_soon
from app.eligibility.qualifications import normalize_level
from app.ingestion.mp_sources import extract_notification_from_text, get_sample_notifications
from app.models import AgeRelaxation, AgeRelaxationApplicability, FieldProvenance, GovtNotification, QualificationRule, UserProfile, UserQualification

ELIGIBILITY_CASES_PATH = Path(__file__).parent / "eligibility" / "cases.json"
ELIGIBILITY_CASES = json.loads(ELIGIBILITY_CASES_PATH.read_text(encoding="utf-8"))


def test_extract_notification_from_text_parses_basic_values():
    raw = """
    Advertisement No: 01/2026
    Title: Junior Engineer (Civil)
    Last Date: 2026-12-15
    """
    notification = extract_notification_from_text(raw)
    assert notification.org is None
    assert notification.title == "Junior Engineer (Civil)"
    assert notification.last_date == "2026-12-15"
    assert notification.total_vacancies is None
    assert notification.fee_by_category == {}
    assert notification.portal_charges is None
    assert notification.posts == []
    assert notification.field_provenance["title"].snippet == "Title: Junior Engineer (Civil)"


def test_extract_notification_from_text_does_not_invent_missing_facts():
    notification = extract_notification_from_text("Title: Engineer")
    assert notification.org is None
    assert notification.advertisement_no is None
    assert notification.last_date is None
    assert notification.total_vacancies is None
    assert notification.fee_by_category == {}
    assert notification.posts == []


def test_eligibility_returns_eligible_for_matching_profile():
    notification = get_sample_notifications()[0]
    profile = UserProfile(
        name="Amit Verma",
        date_of_birth="2001-08-12",
        gender="male",
        category="OBC",
        mp_domicile=True,
        qualifications=[UserQualification(level="Diploma", stream="Civil", percentage=82.5)],
        preferred_districts=["Bhopal"],
        languages=["Hindi", "English"],
        target_roles=["Junior Engineer"],
    )
    result = evaluate_eligibility(notification, profile)
    assert result.status == "eligible"
    assert any("Minimum age requirement is satisfied" in reason.message or "Maximum age requirement is satisfied" in reason.message for reason in result.reasons)


def test_eligibility_rejects_age_limit():
    notification = get_sample_notifications()[0]
    profile = UserProfile(
        name="Rohit Singh",
        date_of_birth="1980-10-10",
        gender="male",
        category="UR",
        mp_domicile=True,
        qualifications=[UserQualification(level="Diploma", stream="Civil", percentage=80)],
    )
    result = evaluate_eligibility(notification, profile)
    assert result.status == "not_eligible"
    assert any("Maximum age is" in reason.message for reason in result.reasons)


def test_fee_calculator_should_include_portal_charges():
    notification = get_sample_notifications()[0]
    fee = calculate_fee(notification, "OBC")
    assert fee.fee == 200.0
    assert fee.total == 225.0


def test_for_you_feed_prioritizes_eligible_notifications():
    notification = get_sample_notifications()[0]
    profile = UserProfile(
        name="Ritika Patel",
        date_of_birth="2000-01-20",
        gender="female",
        category="ST",
        mp_domicile=True,
        qualifications=[UserQualification(level="Diploma", stream="Civil", percentage=75)],
        target_roles=["Junior Engineer"],
    )
    feed = get_for_you_feed(profile, [notification])
    assert feed[0]["status"] == "eligible"


def test_age_on_date_matches_expected_value():
    assert age_on_date("2001-08-12", "2026-01-01") == 24


def test_age_on_date_rejects_ambiguous_year_only_reference():
    try:
        age_on_date("2001-08-12", "2026")
        assert False, "Year-only as-on dates should be rejected as ambiguous."
    except ValueError:
        pass


@pytest.mark.parametrize("case", ELIGIBILITY_CASES, ids=lambda case: case["id"])
def test_eligibility_case_matches_status_and_expected_reason_codes(case):
    notification = GovtNotification.model_validate(case["notification"])
    profile = UserProfile.model_validate(case["profile"])

    result = evaluate_eligibility(notification, profile)

    assert result.status == case["expected_status"]
    actual_reason_pairs = {
        (reason.check, reason.result) for reason in result.reasons
    }
    for post_result in result.post_results:
        actual_reason_pairs.update(
            (reason["check"], reason["result"])
            for reason in post_result["reasons"]
        )
    expected_reason_pairs = {
        (item["check"], item["result"])
        for item in case["expected_reason_codes"]
    }
    assert expected_reason_pairs <= actual_reason_pairs, (
        f"{case['id']}: missing expected reason pairs "
        f"{expected_reason_pairs - actual_reason_pairs}"
    )


def test_eligibility_case_corpus_has_at_least_100_cases():
    assert len(ELIGIBILITY_CASES) >= 100


def test_blank_required_profile_fields_never_preserve_eligible_status():
    for case in ELIGIBILITY_CASES:
        if case["expected_status"] != "eligible":
            continue

        notification = GovtNotification.model_validate(case["notification"])
        required_fields = {"date_of_birth", "qualifications"}
        for post in notification.posts:
            if post.gender_restrictions:
                required_fields.add("gender")
            if post.domicile_required or notification.domicile_required:
                required_fields.add("mp_domicile")
            if post.employment_exchange_required or notification.employment_exchange_registration_required:
                required_fields.add("employment_exchange_registered")
            if post.pwd_required:
                required_fields.add("pwd")
            if post.ex_serviceman_required:
                required_fields.add("ex_serviceman")
        for rule in notification.age_relaxation_rules:
            if rule.category:
                required_fields.add("category")
            if rule.applies_to.gender is not None:
                required_fields.add("gender")
            if rule.applies_to.pwd is not None:
                required_fields.add("pwd")
            if rule.applies_to.ex_serviceman is not None:
                required_fields.add("ex_serviceman")
            if rule.applies_to.domicile is not None:
                required_fields.add("mp_domicile")
        if any(rule.required_certificate for post in notification.posts for rule in post.qualification_rules):
            required_fields.add("certificates")

        for field in required_fields:
            profile = UserProfile.model_validate(case["profile"]).model_copy(update={field: None})
            result = evaluate_eligibility(notification, profile)
            assert result.status != "eligible", f"{case['id']} remained eligible with blank {field}"


def test_eligibility_checks_every_post_and_selects_later_match():
    notification = get_sample_notifications()[0].model_copy(update={
        "posts": [
            get_sample_notifications()[0].posts[0].model_copy(update={"title": "Wrong Stream", "qualification_rules": [
                QualificationRule(level="Diploma", stream="Electrical", min_percent=70)
            ]}),
            get_sample_notifications()[0].posts[0].model_copy(update={"title": "Civil Post"}),
        ]
    })
    profile = UserProfile(
        name="Amit Verma",
        date_of_birth="2001-08-12",
        gender="male",
        category="OBC",
        mp_domicile=True,
        qualifications=[UserQualification(level="Diploma", stream="Civil", percentage=82.5)],
    )

    result = evaluate_eligibility(notification, profile)

    assert len(result.post_results) == 2
    assert result.post_results[0]["status"] == "not_eligible"
    assert result.post_results[1]["status"] == "eligible"
    assert result.matched_posts == ["Civil Post"]


def test_unknown_qualification_level_requires_review():
    notification = get_sample_notifications()[0].model_copy(update={
        "posts": [get_sample_notifications()[0].posts[0].model_copy(update={
            "qualification_rules": [QualificationRule(level="Diploma", stream="Civil", min_percent=70)]
        })]
    })
    profile = UserProfile(
        name="Candidate",
        date_of_birth="2000-01-01",
        gender="male",
        qualifications=[UserQualification(level="Unlisted Certificate", stream="Civil", percentage=90)],
    )

    result = evaluate_eligibility(notification, profile)

    assert result.status == "needs_check"
    assert any(reason.result == "unknown" for reason in result.reasons)


def test_qualification_hierarchy_normalizes_degree_aliases_from_yaml():
    assert normalize_level("B.E.") == "Graduate"
    assert normalize_level("B.Com.") == "Graduate"
    assert normalize_level("PhD") == "Doctorate"


def test_structured_age_relaxation_applies_to_matching_profile():
    notification = GovtNotification.model_validate({
        "title": "Recruitment",
        "age_limit": {"min": 18, "max": 30, "as_on_date": "2026-01-01"},
        "age_relaxation_combination": "max_only",
        "age_relaxation_rules": [AgeRelaxation(
            category="OBC",
            years=5,
            applies_to=AgeRelaxationApplicability(gender="female", domicile=True),
        )],
        "posts": [{
            "title": "Post",
            "qualification_rules": [QualificationRule(level="Diploma", stream="Civil")],
        }],
    })
    profile = UserProfile(
        name="Candidate",
        date_of_birth="1992-01-01",
        gender="female",
        category="OBC",
        mp_domicile=True,
        qualifications=[UserQualification(level="Diploma", stream="Civil")],
    )

    result = evaluate_eligibility(notification, profile)

    assert result.status == "eligible"


def test_missing_age_range_and_qualification_rule_require_review():
    notification = GovtNotification.model_validate({
        "title": "Incomplete notice",
        "age_limit": {"as_on_date": "2026-01-01"},
        "posts": [{"title": "Post"}],
    })
    profile = UserProfile(name="Candidate", date_of_birth="2000-01-01", gender="male")

    result = evaluate_eligibility(notification, profile)

    assert result.status == "needs_check"
    assert {reason.check for reason in result.reasons} >= {"age", "qualification"}


def test_unknown_fee_category_sets_needs_check_flag():
    notification = GovtNotification.model_validate({
        "fee_by_category": {"UR": 100},
        "portal_charges": 25,
    })

    fee = calculate_fee(notification, "OBC")

    assert fee.fee is None
    assert fee.total is None
    assert fee.needs_check is True


def test_days_left_and_closing_soon_use_injected_today():
    notification = GovtNotification.model_validate({"last_date": "2026-10-17"})

    assert days_left(notification, "2026-10-10") == 7
    assert is_closing_soon(notification, "2026-10-10") is True
    assert days_left(notification, "2026-10-09") == 8
    assert is_closing_soon(notification, "2026-10-09") is False


def test_feed_orders_by_eligibility_and_excludes_closed_notice():
    closed_case = next(case for case in ELIGIBILITY_CASES if case["id"] == "manual_closed_notification")
    closed = GovtNotification.model_validate(closed_case["notification"])
    profile = UserProfile.model_validate(closed_case["profile"])
    eligible = get_sample_notifications()[0].model_copy(update={
        "title": "Eligible soon",
        "last_date": "2026-10-12",
        "status": "open",
    })
    likely = get_sample_notifications()[0].model_copy(update={
        "title": "Likely sooner",
        "last_date": "2026-10-11",
        "status": "open",
        "posts": [get_sample_notifications()[0].posts[0].model_copy(update={
            "field_provenance": {
                "title": FieldProvenance(confidence=0.5, snippet="uncertain title", method="ocr")
            }
        })],
    })

    feed = get_for_you_feed(profile, [likely, closed, eligible], today="2026-10-10")

    assert [item["notification"] for item in feed] == ["Eligible soon", "Likely sooner"]
    assert [item["status"] for item in feed] == ["eligible", "likely"]
