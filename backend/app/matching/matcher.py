from __future__ import annotations

import re

from app.models import PrivateJob, UserProfile


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def score_private_job(profile: UserProfile, job: PrivateJob) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    profile_text = " ".join(profile.target_roles + [qualification.level for qualification in profile.qualifications])
    profile_tokens = set(_norm(profile_text).split())
    job_tokens = set(_norm(job.title).split())
    overlap = sorted(profile_tokens & job_tokens)
    if overlap:
        score += 35
        reasons.append(f"Role match: {', '.join(overlap)}")
    else:
        reasons.append("Role match is weak; review the actual job title and responsibilities.")

    if profile.experience_years <= (job.experience_max or 99):
        score += 20
        reasons.append(f"Experience fit: {profile.experience_years} years versus {job.experience_max or 'no upper bound'} years.")
    else:
        reasons.append("Experience exceeds the posted upper bound.")

    if job.location_scope == "MP" or job.city.lower() in {d.lower() for d in profile.preferred_districts}:
        score += 25
        reasons.append(f"Location fit: {job.city} matches MP or your preferred districts.")
    elif job.work_mode.lower() == "remote":
        score += 10
        reasons.append("Remote role from an MP-based employer is acceptable.")
    else:
        reasons.append(f"Location may not match your preferred MP districts: {job.city}.")

    if job.required_skills:
        skill_overlap = [skill for skill in job.required_skills if _norm(skill) in _norm(" ".join(profile.target_roles + [q.level for q in profile.qualifications]))]
        if skill_overlap:
            score += 15
            reasons.append(f"Skill overlap: {', '.join(skill_overlap)}")

    score -= float(job.scam_score)
    if job.scam_score >= 70:
        reasons.append("Scam risk is high; confirm employer identity and official careers link before applying.")
    else:
        reasons.append("Employer and listing look reasonably trustworthy.")

    if score < 0:
        score = 0.0

    return round(score, 2), reasons


def match_private_jobs(profile: UserProfile, jobs: list[PrivateJob]) -> list[dict]:
    ranked = []
    for job in jobs:
        total_score, reasons = score_private_job(profile, job)
        ranked.append({
            "job": job,
            "score": total_score,
            "reasons": reasons,
            "status": "likely" if total_score >= 50 else "needs_check",
        })
    ranked.sort(key=lambda item: (-item["score"], item["job"].posted_at))
    return ranked
