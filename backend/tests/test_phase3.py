from fastapi.testclient import TestClient

from app.main import app
from app.matching.matcher import match_private_jobs
from app.ingestion.private_jobs import get_company_registry, get_private_job_fixtures
from app.models import UserProfile, UserQualification


client = TestClient(app)


def test_company_registry_contains_mp_relevant_employers():
    companies = get_company_registry()
    assert len(companies) >= 3
    assert any(company.city.lower() == "bhopal" for company in companies)


def test_private_jobs_matcher_ranks_the_best_fit_first():
    profile = UserProfile(
        name="Amit Verma",
        date_of_birth="2001-08-12",
        gender="male",
        category="OBC",
        mp_domicile=True,
        experience_years=1.5,
        preferred_districts=["Pithampur", "Indore"],
        qualifications=[UserQualification(level="Diploma", stream="Civil", percentage=82.5)],
        target_roles=["Civil Engineer", "Junior Engineer"],
    )
    jobs = get_private_job_fixtures()
    matches = match_private_jobs(profile, jobs)
    top = matches[0]
    assert top["job"].title == "Junior Engineer - Civil"
    assert top["score"] >= 50


def test_scam_risk_is_flagged_for_untrusted_listing():
    profile = UserProfile(
        name="Riya Soni",
        date_of_birth="1999-02-02",
        gender="female",
        category="UR",
        mp_domicile=True,
        experience_years=0.5,
        preferred_districts=["Bhopal"],
        target_roles=["Nursing Officer"],
    )
    matches = match_private_jobs(profile, get_private_job_fixtures())
    suspicious = next(job for job in matches if job["job"].scam_score >= 70)
    assert suspicious["status"] == "needs_check"
    assert any("Scam risk" in reason for reason in suspicious["reasons"])


def test_private_job_match_endpoint_returns_ranked_results():
    payload = {
        "profile": {
            "name": "Amit Verma",
            "date_of_birth": "2001-08-12",
            "gender": "male",
            "category": "OBC",
            "mp_domicile": True,
            "experience_years": 1.5,
            "preferred_districts": ["Pithampur", "Indore"],
            "qualifications": [{"level": "Diploma", "stream": "Civil", "percentage": 82.5}],
            "target_roles": ["Civil Engineer", "Junior Engineer"],
        }
    }
    response = client.post("/private-jobs/match", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["items"][0]["score"] >= 50
