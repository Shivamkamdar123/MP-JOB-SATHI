from app.eligibility.engine import age_on_date, calculate_fee, evaluate_eligibility, get_for_you_feed
from app.ingestion.mp_sources import extract_notification_from_text, get_sample_notifications
from app.models import UserProfile, UserQualification


def test_extract_notification_from_text_parses_basic_values():
    raw = """
    Advertisement No: 01/2026
    Title: Junior Engineer (Civil)
    Last Date: 2026-12-15
    """
    notification = extract_notification_from_text(raw)
    assert notification.org == "MPESB"
    assert notification.title == "Junior Engineer (Civil)"
    assert notification.last_date == "2026-12-15"


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
    assert "Matches the notified age, qualification" in result.reasons[0]


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
    assert any("Age maximum" in reason for reason in result.reasons)


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
