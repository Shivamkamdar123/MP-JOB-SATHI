from __future__ import annotations

from pathlib import Path

import yaml

from app.models import UserProfile, UserQualification


def _load_config() -> dict:
    path = Path(__file__).resolve().parent / "data" / "qualifications.yaml"
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


_CONFIG = _load_config()
_LEVEL_ORDER = _CONFIG.get("levels", {}).get("order", [])
_ALIASES = {}


def _normalise_key(level: str) -> str:
    return " ".join(level.strip().lower().replace(".", "").split())


for canonical, aliases in (_CONFIG.get("levels", {}).get("aliases", {}) or {}).items():
    _ALIASES[_normalise_key(canonical)] = canonical
    for alias in aliases:
        _ALIASES[_normalise_key(alias)] = canonical


def normalize_level(level: str | None) -> str | None:
    if level is None:
        return None
    key = _normalise_key(level)
    return _ALIASES.get(key, key.title())


def qualification_rank(level: str | None) -> int:
    normalized = normalize_level(level)
    if normalized is None:
        return -1
    try:
        return _LEVEL_ORDER.index(normalized)
    except ValueError:
        return -1


def qualification_matches_rule(
    qualification: UserQualification,
    rule_level: str,
    rule_stream: str | None = None,
    rule_min_percent: float | None = None,
    or_above: bool = False,
    required_certificate: str | None = None,
    certificates: list[str] | None = None,
) -> tuple[bool, str | None]:
    q_level = normalize_level(qualification.level)
    target = normalize_level(rule_level)
    if q_level is None or target is None:
        return False, None

    q_rank = qualification_rank(q_level)
    target_rank = qualification_rank(target)
    if q_rank < 0 or target_rank < 0:
        return False, f"Qualification level could not be matched to the configured hierarchy: {qualification.level} / {rule_level}."
    if q_rank < target_rank:
        return False, f"Requires {target}; you have {q_level}: not eligible"
    if q_rank > target_rank and not or_above:
        # broader than asked is still generally acceptable only when the rule uses or_above.
        if q_level == target:
            pass
        else:
            return False, f"Requires {target}; you have {q_level}: not eligible"
    if rule_stream:
        if not qualification.stream:
            return False, f"Requires stream {rule_stream}; your qualification record has no stream recorded"
        if qualification.stream.strip().lower() != rule_stream.strip().lower():
            return False, f"Requires {rule_stream}; you have {qualification.stream}: not eligible"
    if rule_min_percent is not None:
        if qualification.percentage is None:
            return False, f"Requires at least {rule_min_percent}% in {target}; your percentage is missing"
        if qualification.percentage < rule_min_percent:
            return False, f"Requires at least {rule_min_percent}% in {target}; you have {qualification.percentage}%: not eligible"
    if required_certificate:
        if certificates is None:
            return False, f"Required certificate {required_certificate} is not recorded in the profile"
        if required_certificate.casefold() not in {certificate.casefold() for certificate in certificates}:
            return False, f"Required certificate {required_certificate} is not listed in the profile"
    return True, None


def qualification_fits_profile(
    profile: UserProfile,
    level: str,
    stream: str | None,
    min_percent: float | None,
    or_above: bool = False,
    required_certificate: str | None = None,
) -> tuple[bool, str | None, bool]:
    if not profile.qualifications:
        return False, f"No qualification data recorded; required {level}.", True

    for qualification in profile.qualifications:
        exact_match, message = qualification_matches_rule(
            qualification,
            level,
            stream,
            min_percent,
            or_above,
            required_certificate,
            profile.certificates,
        )
        if exact_match:
            return True, f"You have {qualification.level}; qualifies for {level}.", False
        if message and "your qualification record has no stream recorded" in message:
            return False, message, True
        if message and "percentage is missing" in message:
            return False, message, True
        if message and "could not be matched to the configured hierarchy" in message:
            return False, message, True
        if message and "is not recorded in the profile" in message:
            return False, message, True
        if message and "is not listed in the profile" in message:
            continue

    best_match = None
    for qualification in profile.qualifications:
        q_level = normalize_level(qualification.level)
        target = normalize_level(level)
        if q_level and target and qualification_rank(q_level) >= qualification_rank(target):
            best_match = qualification
            break

    if best_match is not None:
        return False, f"Requires {level}; you have {best_match.level}: not eligible", False
    return False, f"Requires {level}; no matching qualification found.", False
