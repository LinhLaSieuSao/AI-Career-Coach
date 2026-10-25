"""Match candidate skills with career roles and job descriptions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from functools import lru_cache
import math
import re
from numbers import Real
from pathlib import Path
from typing import Any

from .catalog import load_roles, load_skill_vocabulary
from .skill_extractor import extract_skills, load_aliases, normalize_skill
from .levels import normalize_levels


_DATA_DIR = Path(__file__).resolve().parent.parent / "Data"


@lru_cache(maxsize=1)
def _load_role_catalog() -> list[dict[str, Any]]:
    """Load role data relative to the repository, independent of cwd."""
    return load_roles(_DATA_DIR / "roles.json")


@lru_cache(maxsize=1)
def _load_alias_map() -> dict[str, str]:
    """Load canonical skill aliases from the project's data directory."""
    path = _DATA_DIR / "skill_aliases.json"
    return load_aliases(path)


def _canonical_skill(value: str, aliases: Mapping[str, str]) -> str:
    """Normalize a skill and follow alias chains while guarding against cycles."""
    canonical = normalize_skill(value)
    visited: set[str] = set()
    while canonical in aliases and canonical not in visited:
        visited.add(canonical)
        canonical = normalize_skill(aliases[canonical])
    return canonical


def _candidate_skill_set(
    skills: Iterable[str] | str | None,
    aliases: Mapping[str, str],
) -> set[str]:
    """Return nonempty canonical candidate skills, ignoring duplicates."""
    if skills is None:
        return set()
    values: Iterable[str] = (skills,) if isinstance(skills, str) else skills
    try:
        iterator = iter(values)
    except TypeError as exc:
        raise TypeError("skills phải là chuỗi hoặc iterable các chuỗi.") from exc

    result: set[str] = set()
    for skill in iterator:
        if not isinstance(skill, str):
            raise TypeError("Mỗi kỹ năng ứng viên phải là chuỗi.")
        canonical = _canonical_skill(skill, aliases)
        if canonical:
            result.add(canonical)
    return result


def _role_skill_records(
    role: Mapping[str, Any], aliases: Mapping[str, str]
) -> list[tuple[str, str, Real, Any]]:
    """Return display name, canonical name, weight, and required role level."""
    raw_skills = role.get("skills")
    if not isinstance(raw_skills, list):
        raise ValueError("role phải có trường 'skills' là một danh sách.")

    records: list[tuple[str, str, Real, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_skills):
        level = None
        if isinstance(item, str):
            display_name = item.strip()
            weight: Real = 1
        elif isinstance(item, Mapping):
            raw_name = item.get("name")
            if not isinstance(raw_name, str) or not raw_name.strip():
                raise ValueError(f"role.skills[{index}] thiếu tên kỹ năng hợp lệ.")
            display_name = raw_name.strip()
            weight = item.get("weight", 1)
            level = item.get("level")
        else:
            raise ValueError(f"role.skills[{index}] phải là chuỗi hoặc object skill.")

        canonical = _canonical_skill(display_name, aliases)
        if not canonical:
            raise ValueError(f"role.skills[{index}] có tên kỹ năng rỗng.")
        if canonical in seen:
            raise ValueError(f"role chứa kỹ năng trùng sau chuẩn hóa: {display_name!r}.")
        if (
            isinstance(weight, bool)
            or not isinstance(weight, Real)
            or weight <= 0
            or not math.isfinite(float(weight))
        ):
            raise ValueError(f"role.skills[{index}].weight phải là số dương.")

        seen.add(canonical)
        records.append((display_name, canonical, weight, level))
    return records


def _build_role_result(
    candidate_skills: set[str],
    role: Mapping[str, Any],
    aliases: Mapping[str, str],
) -> dict[str, Any]:
    """Shared role comparison used by the public role matcher."""
    role_skills = _role_skill_records(role, aliases)
    matched: list[str] = []
    missing: list[str] = []
    missing_details: list[dict[str, Any]] = []
    matched_weight = 0.0
    total_weight = sum(float(record[2]) for record in role_skills)

    for display_name, canonical, weight, level in role_skills:
        if canonical in candidate_skills:
            matched.append(display_name)
            matched_weight += float(weight)
        else:
            missing.append(display_name)
            missing_details.append({"name": display_name, "weight": weight, "level": level})

    percent = round(100.0 * matched_weight / total_weight, 1) if total_weight else 0.0
    role_id = role.get("id")
    role_name = role.get("name") or role.get("name_vi") or role_id
    return {
        "role_id": role_id,
        "role_name": role_name,
        "percent": min(100.0, max(0.0, percent)),
        "matched": matched,
        "missing": missing,
        "missing_details": missing_details,
    }


def match_role(skills: Iterable[str] | str | None, role: Mapping[str, Any]) -> dict[str, Any]:
    """Compare candidate skills with one role using that role's skill weights.

    The result's ``percent`` is the share of the role's total skill weight
    represented by the candidate's skills. ``matched`` and ``missing`` use
    the role's skill names and preserve the role's declared order.
    ``missing_details`` has one entry per missing skill in that same order,
    with its name, role weight, and required role level. Missing weights
    default to 1; missing levels are None. Level is passed through from the
    role and does not affect matching or estimate the candidate's proficiency.

    Args:
        skills: Candidate skill names, usually ``profile["skills"]``.
        role: A role object from ``Data/roles.json``.

    Returns:
        A dictionary containing role identity, weighted percentage, matched
        skills, missing skills, and their role metadata for roadmap planning.

    Raises:
        TypeError: if skills or role has an unsupported type.
        ValueError: if the role's required-skill data is malformed.
    """
    if not isinstance(role, Mapping):
        raise TypeError("role phải là một object/dictionary.")
    aliases = _load_alias_map()
    candidate_skills = _candidate_skill_set(skills, aliases)
    return _build_role_result(candidate_skills, role, aliases)


def match_cv_to_jd(cv_text: str, jd_text: str) -> dict[str, Any]:
    """Extract known skills from a CV and JD, then compare the skill sets.

    The percentage is the fraction of unique skills recognized in the JD that
    also appear in the CV. Unknown terms are omitted because the project does
    not have a canonical skill entry for them.

    Raises:
        ValueError: if either text is empty or yields no recognized skills.
    """
    if not isinstance(cv_text, str) or not cv_text.strip():
        raise ValueError("CV không có nội dung văn bản.")
    if not isinstance(jd_text, str) or not jd_text.strip():
        raise ValueError("Mô tả công việc đang trống.")

    roles = _load_role_catalog()
    vocabulary = load_skill_vocabulary(roles, data_dir=_DATA_DIR)
    aliases = _load_alias_map()
    cv_skills = extract_skills(cv_text, vocabulary, aliases=aliases)
    jd_skills = extract_skills(jd_text, vocabulary, aliases=aliases)

    if not cv_skills:
        raise ValueError("Không nhận diện được kỹ năng trong CV.")
    if not jd_skills:
        raise ValueError("Không nhận diện được kỹ năng trong mô tả công việc.")

    cv_skill_set = set(cv_skills)
    matched = [skill for skill in jd_skills if skill in cv_skill_set]
    missing = [skill for skill in jd_skills if skill not in cv_skill_set]
    percent = round(100.0 * len(matched) / len(jd_skills), 1)
    return {
        "percent": percent,
        "cv_skills": cv_skills,
        "jd_skills": jd_skills,
        "matched": matched,
        "missing": missing,
    }


def compute_gap(levels: dict[str, int], role: dict) -> dict:
    """Explicit assessment: every undeclared role skill has current=0 here only."""
    levels = normalize_levels(levels)
    if not isinstance(role, Mapping):
        raise TypeError("role phải là một object/dictionary.")
    records = _role_skill_records(role, _load_alias_map())
    items = []
    total = earned = 0.0
    scale = max((float(r[2]) for r in records if type(r[3]) is int and r[3] > 0), default=1)
    for _, skill, weight, required in records:
        if type(required) is not int or not 0 <= required <= 3:
            raise ValueError(f"Required level của {skill} phải là int 0–3.")
        current = levels.get(skill, 0)
        gap = max(0, required - current)
        priority = weight * gap
        if not math.isfinite(priority):
            raise ValueError("priority vượt phạm vi số hữu hạn.")
        items.append({"skill": skill, "required": required, "current": current,
                      "gap": gap, "priority": priority,
                      "status": "met" if gap == 0 else "missing" if current == 0 else "below_required"})
        if required > 0:
            total += float(weight) / scale
            earned += float(weight) / scale * min(current / required, 1)
    return {"role_id": role.get("id"), "items": items,
            "match_percent": min(100.0, max(0.0, round(100 * earned / total, 1))) if total else 0.0,
            "missing": [item["skill"] for item in items if item["gap"] > 0]}


def suggest_roles(profile, top_k=5) -> list[dict]:
    """Explainable presence/interest heuristic over the local catalog, no network."""
    if type(top_k) is not int or top_k < 0:
        raise ValueError("top_k phải là int không âm.")
    if not isinstance(profile, Mapping):
        raise TypeError("profile phải là object.")
    if top_k == 0:
        return []
    aliases = _load_alias_map()
    skills = _candidate_skill_set(profile.get("skills", []), aliases)
    interests = profile.get("interests") or []
    if isinstance(interests, str):
        interests = re.split(r"[,;\n]+", interests)
    interests = sorted(_candidate_skill_set(interests, aliases))
    if not skills and not interests:
        return []
    results = []
    for role in _load_role_catalog():
        match = _build_role_result(skills, role, aliases)
        texts = [normalize_skill(str(role.get("name", ""))), normalize_skill(str(role.get("name_vi", ""))),
                 *(s[1] for s in _role_skill_records(role, aliases))]
        matched_interests = [term for term in interests if any(
            re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text) for text in texts)]
        skill_part = match["percent"] / 100
        interest_part = len(matched_interests) / len(interests) if interests else 0
        value = .8 * skill_part + .2 * interest_part if skills and interests else skill_part if skills else interest_part
        score = round(100 * value, 1)
        if score <= 0:
            continue
        reasons = []
        if match["matched"]:
            reasons.append("Kỹ năng trùng yêu cầu: " + ", ".join(match["matched"]))
        if matched_interests:
            reasons.append("Sở thích có trong tên/yêu cầu role: " + ", ".join(matched_interests))
        results.append({"role_id": role["id"], "role_name": role.get("name_vi") or role.get("name"),
                        "score": score, "skill_percent": match["percent"],
                        "interest_percent": round(100 * interest_part, 1), "matched": match["matched"],
                        "missing": match["missing"], "matched_interests": matched_interests,
                        "reasons": reasons, "method": "heuristic"})
    return sorted(results, key=lambda r: (-r["score"], r["role_id"]))[:top_k]
