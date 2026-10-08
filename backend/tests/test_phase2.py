from app.assist.form_assist import (
    build_pre_submit_checklist,
    generate_form_prefill,
    validate_document_spec,
)
from app.ingestion.mp_sources import get_sample_notifications
from app.models import UserProfile, UserQualification


def test_document_spec_validator_accepts_valid_photo():
    result = validate_document_spec('photo.jpg', 180_000, 350, 450, 'image/jpeg')
    assert result['is_valid'] is True
    assert result['issues'] == []


def test_document_spec_validator_flags_wrong_size_and_dimensions():
    result = validate_document_spec('signature.png', 2_000_000, 200, 200, 'image/png')
    assert result['is_valid'] is False
    assert any('dimension' in issue.lower() for issue in result['issues'])


def test_prefill_generates_targeted_fields_for_mp_online_forms():
    profile = UserProfile(
        name='Amit Verma',
        date_of_birth='2001-08-12',
        gender='male',
        category='OBC',
        mp_domicile=True,
        qualifications=[UserQualification(level='Diploma', stream='Civil', percentage=82.5)],
        employment_exchange_registered=True,
    )
    values = generate_form_prefill(profile)
    assert values['candidate_name'] == 'Amit Verma'
    assert values['dob'] == '2001-08-12'
    assert values['category'] == 'OBC'


def test_pre_submit_checklist_flags_missing_fee_and_documents():
    notification = get_sample_notifications()[0]
    profile = UserProfile(
        name='Amit Verma',
        date_of_birth='2001-08-12',
        gender='male',
        category='OBC',
        mp_domicile=True,
        qualifications=[UserQualification(level='Diploma', stream='Civil', percentage=82.5)],
    )
    items = build_pre_submit_checklist(profile, notification, 'OBC', paid=False, docs_ready=False)
    assert any('fee' in item['title'].lower() for item in items)
    assert any('document' in item['title'].lower() for item in items)
