from __future__ import annotations

from app.models import CompanySource, JobFair, PrivateJob


def get_company_registry() -> list[CompanySource]:
    return [
        CompanySource(
            name="Tata Consultancy Services",
            city="Bhopal",
            industry="IT Services",
            careers_url="https://www.tcs.com/careers",
            ats_type="greenhouse",
            board_slug="tcs",
            last_verified="2026-10-08",
        ),
        CompanySource(
            name="Mahindra & Mahindra",
            city="Pithampur",
            industry="Manufacturing",
            careers_url="https://www.mahindra.com/careers",
            ats_type="lever",
            board_slug="mahindra",
            last_verified="2026-10-08",
        ),
        CompanySource(
            name="Apollo Hospitals",
            city="Indore",
            industry="Healthcare",
            careers_url="https://careers.apollohospitals.com",
            ats_type="workable",
            board_slug="apollo",
            last_verified="2026-10-08",
        ),
    ]


def get_job_fair_calendar() -> list[JobFair]:
    return [
        JobFair(
            title="MP Rozgar Mela – Indore",
            district="Indore",
            venue="District Employment Office, Indore",
            date_time="2026-11-15T10:00:00",
            companies=["Apollo Hospitals", "Reliance Retail"],
            eligibility="10th/12th/Graduate, age as per notification",
            documents_to_carry=["Resume", "ID proof", "Education documents"],
            source_url="https://mprojgar.gov.in/rozgar-mela/indore",
        )
    ]


def get_private_job_fixtures() -> list[PrivateJob]:
    return [
        PrivateJob(
            title="Junior Engineer - Civil",
            company="Mahindra & Mahindra",
            city="Pithampur",
            work_mode="Onsite",
            experience_min=0,
            experience_max=2,
            salary_inr_lpa=4.8,
            employment_type="Full-time",
            ats_type="lever",
            apply_url="https://jobs.mahindra.com/123",
            posted_at="2026-10-01T09:00:00",
            first_seen_at="2026-10-01T09:00:00",
            last_seen_at="2026-10-01T09:00:00",
            closed_at=None,
            scam_score=16.0,
            required_skills=["civil", "site engineering", "autocad"],
            location_scope="MP",
        ),
        PrivateJob(
            title="IT Support Executive",
            company="Tata Consultancy Services",
            city="Bhopal",
            work_mode="Hybrid",
            experience_min=0,
            experience_max=3,
            salary_inr_lpa=3.5,
            employment_type="Full-time",
            ats_type="greenhouse",
            apply_url="https://www.tcs.com/careers/job-details/it-support-executive",
            posted_at="2026-10-04T12:00:00",
            first_seen_at="2026-10-04T12:00:00",
            last_seen_at="2026-10-04T12:00:00",
            closed_at=None,
            scam_score=8.0,
            required_skills=["it support", "windows", "hardware"],
            location_scope="MP",
        ),
        PrivateJob(
            title="Nursing Officer",
            company="Unknown Health Network",
            city="Bhopal",
            work_mode="Onsite",
            experience_min=0,
            experience_max=1,
            salary_inr_lpa=2.8,
            employment_type="Full-time",
            ats_type="unknown",
            apply_url="https://untrusted-jobs.example/apply",
            posted_at="2026-10-06T08:00:00",
            first_seen_at="2026-10-06T08:00:00",
            last_seen_at="2026-10-06T08:00:00",
            closed_at=None,
            scam_score=88.0,
            required_skills=["nursing", "patient care"],
            location_scope="MP",
        ),
    ]
