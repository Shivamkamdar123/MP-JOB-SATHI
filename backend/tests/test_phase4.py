from app.tracker.manager import (
    build_admin_snapshot,
    build_reminders,
    build_share_card,
    create_application_tracking,
)


def test_create_application_tracking_tracks_stage_and_deadline():
    tracker = create_application_tracking(
        job_title='Junior Engineer (Civil)',
        company='MPESB',
        stage='ready',
        deadline='2026-12-15',
        exam_date='2026-12-28',
    )
    assert tracker['stage'] == 'ready'
    assert tracker['deadline'] == '2026-12-15'
    assert tracker['status'] == 'active'


def test_build_reminders_hints_for_admit_card_and_results():
    reminders = build_reminders(
        deadline='2026-12-15',
        exam_date='2026-12-28',
        result_date='2027-02-18',
    )
    assert any('admit card' in item['title'].lower() for item in reminders)
    assert any('result' in item['title'].lower() for item in reminders)


def test_build_share_card_includes_public_title_and_link():
    card = build_share_card('Junior Engineer (Civil)', 'https://esb.mp.gov.in/notification')
    assert card['title'] == 'Junior Engineer (Civil)'
    assert card['share_url'] == 'https://esb.mp.gov.in/notification'
    assert 'Official' in card['message']


def test_admin_snapshot_groups_applications_by_center():
    snapshot = build_admin_snapshot(
        center_name='Indore coaching center',
        applications=[{'candidate': 'Amit', 'status': 'ready'}, {'candidate': 'Riya', 'status': 'saved'}],
    )
    assert snapshot['center_name'] == 'Indore coaching center'
    assert snapshot['totals']['ready'] == 1
    assert snapshot['totals']['saved'] == 1
