"""Match candidate skills with career roles and job descriptions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from functools import lru_cache
import math
import re
from numbers import Real
from pathlib import Path
from typing import Any
import unicodedata

from .catalog import load_roles, load_skill_vocabulary
from .interests import interest_fit, load_role_family_vectors, load_interest_activities, resolve_activity_ids, user_interest_vector
from .skill_extractor import extract_skills, load_aliases, normalize_skill
from .levels import normalize_levels


_DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
MIN_SKILL_SIGNAL_FOR_UNCAPPED_ROLE_SCORE = 0.15
LOW_SKILL_ROLE_SCORE_CAP = 0.05
LOW_CONFIDENCE_SKILL_COUNT = 3
LOW_CONFIDENCE_ROLE_MESSAGE = (
    "Độ tin cậy sơ bộ: Hồ sơ có ít kỹ năng; hãy bổ sung kỹ năng để gợi ý chính xác hơn."
)


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


_JD_SECTION_HEADINGS = {
    "must_have": {
        "yeu cau", "yeu cau bat buoc", "yeu cau chinh", "yeu cau cong viec",
        "yeu cau ung vien", "yeu cau chuyen mon", "ky nang bat buoc",
        "tieu chi tuyen chon", "bat buoc",
        "requirements", "requirement", "qualifications", "qualification",
        "candidate requirements", "must have", "you must have", "essential",
        "required skills", "skills and qualifications",
    },
    "nice_to_have": {
        "uu tien", "uu tien neu co", "diem cong", "la diem cong", "loi the",
        "nice to have", "good to have", "preferred", "preferred qualifications",
        "desirable", "bonus", "bonus skills",
    },
    "unclassified": {
        "mo ta cong viec", "trach nhiem", "nhiem vu", "vai tro",
        "responsibilities", "job description", "about the role",
        "what you will do", "what you ll do", "phuc loi", "quyen loi",
        "che do dai ngo", "benefits", "what we offer", "ve cong ty",
        "about us", "dia diem lam viec", "thong tin khac", "cach ung tuyen",
        "how to apply", "application process",
    },
}


def _fold_jd_heading(value: str) -> str:
    """Fold accents/punctuation for matching explicit JD section labels."""
    value = unicodedata.normalize("NFKD", value.casefold()).replace("đ", "d")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _jd_heading(line: str) -> tuple[str | None, str]:
    """Recognize standalone or fragment-leading headings, returning label/body."""
    cleaned = re.sub(r"^\s*(?:#{1,6}\s*|[-*+]\s*|\d+[.)]\s*)", "", line).strip()
    folded = _fold_jd_heading(cleaned)
    for kind, labels in _JD_SECTION_HEADINGS.items():
        if folded in labels:
            return kind, ""
    # Inline headings are accepted only with an explicit separator. This keeps
    # prose such as "requirements include Python" from being guessed as a
    # section boundary.
    for separator in (":", "：", "—", "–", " - "):
        if separator not in cleaned:
            continue
        before, _, body = cleaned.partition(separator)
        heading = _fold_jd_heading(before)
        for kind, labels in _JD_SECTION_HEADINGS.items():
            if heading in labels:
                return kind, body.strip()
    return None, line


def extract_jd_skill_requirements(jd_text: str) -> dict[str, list[str]]:
    """Extract catalog skills and conservatively classify explicit JD sections.

    Skills mentioned without a recognized section heading remain unclassified.
    The function does not infer requirement priority from wording in paragraphs.
    """
    if not isinstance(jd_text, str) or not jd_text.strip():
        raise ValueError("Mô tả công việc đang trống.")
    roles = _load_role_catalog()
    vocabulary = load_skill_vocabulary(roles, data_dir=_DATA_DIR)
    aliases = _load_alias_map()
    sections: dict[str, list[str]] = {
        "must_have": [], "nice_to_have": [], "unclassified": []
    }
    current = "unclassified"
    for line in jd_text.splitlines():
        # Pasted JDs sometimes put several labeled sections in one paragraph.
        # Split only at sentence/list boundaries, then still require an exact
        # known heading and an explicit colon/dash before changing category.
        fragments = re.split(r"(?<=[.!?;])\s+", line)
        for fragment in fragments:
            heading, body = _jd_heading(fragment)
            if heading is not None:
                current = heading
                if body:
                    sections[current].append(body)
            elif fragment.strip():
                sections[current].append(fragment)

    all_skills = extract_skills(jd_text, vocabulary, aliases=aliases)
    if not all_skills:
        raise ValueError("Không nhận diện được kỹ năng trong mô tả công việc.")
    detected = {
        kind: set(extract_skills("\n".join(lines), vocabulary, aliases=aliases))
        for kind, lines in sections.items()
    }
    # A skill mentioned in more than one section keeps its strongest explicit
    # classification: must-have, then nice-to-have, then unclassified.
    must = [skill for skill in all_skills if skill in detected["must_have"]]
    must_set = set(must)
    nice = [
        skill for skill in all_skills
        if skill in detected["nice_to_have"] and skill not in must_set
    ]
    classified = must_set | set(nice)
    unclassified = [
        skill for skill in all_skills
        if skill not in classified
    ]
    return {
        "all_skills": all_skills,
        "must_have": must,
        "nice_to_have": nice,
        "unclassified": unclassified,
    }


def extract_jd_skills(jd_text: str) -> list[str]:
    """Return catalog skills recognized in a JD for user confirmation."""
    requirements = extract_jd_skill_requirements(jd_text)
    skills = requirements["all_skills"]
    if not skills:
        raise ValueError("Không nhận diện được kỹ năng trong mô tả công việc.")
    return skills


def compare_confirmed_jd_requirements(
    candidate_skills: Iterable[str],
    must_have_skills: Iterable[str],
    nice_to_have_skills: Iterable[str],
    unclassified_skills: Iterable[str] = (),
    *,
    must_weight: float = 0.85,
    nice_weight: float = 0.15,
) -> dict[str, Any]:
    """Compare user-confirmed JD categories with catalog skills in a profile.

    The optional weighted aggregate exists only when at least one must-have
    skill is confirmed. Unclassified skills have their own coverage and never
    affect that aggregate. This is a presence heuristic, not hiring readiness.
    """
    if isinstance(must_weight, bool) or not isinstance(must_weight, Real):
        raise ValueError("must_weight phải là số hữu hạn dương.")
    if isinstance(nice_weight, bool) or not isinstance(nice_weight, Real):
        raise ValueError("nice_weight phải là số hữu hạn không âm.")
    try:
        must_weight_value = float(must_weight)
        nice_weight_value = float(nice_weight)
        total_weight = must_weight_value + nice_weight_value
    except OverflowError as exc:
        raise ValueError("Tổng trọng số phải là số hữu hạn.") from exc
    if not math.isfinite(must_weight_value) or must_weight_value <= 0:
        raise ValueError("must_weight phải là số hữu hạn dương.")
    if not math.isfinite(nice_weight_value) or nice_weight_value < 0:
        raise ValueError("nice_weight phải là số hữu hạn không âm.")
    if not math.isfinite(total_weight) or total_weight <= 0:
        raise ValueError("Tổng trọng số phải lớn hơn 0.")

    aliases = _load_alias_map()
    candidate = _candidate_skill_set(candidate_skills, aliases)

    def canonical_list(values: Iterable[str], label: str) -> list[str]:
        if isinstance(values, str):
            raise TypeError(f"{label} phải là iterable các kỹ năng đã xác nhận.")
        try:
            items = list(values)
        except TypeError as exc:
            raise TypeError(f"{label} phải là iterable các kỹ năng đã xác nhận.") from exc
        result: list[str] = []
        seen: set[str] = set()
        for value in items:
            if not isinstance(value, str):
                raise TypeError(f"Mỗi kỹ năng trong {label} phải là chuỗi.")
            canonical = _canonical_skill(value, aliases)
            if canonical and canonical not in seen:
                seen.add(canonical)
                result.append(canonical)
        return result

    categories = {
        "must_have": canonical_list(must_have_skills, "must_have_skills"),
        "nice_to_have": canonical_list(nice_to_have_skills, "nice_to_have_skills"),
        "unclassified": canonical_list(unclassified_skills, "unclassified_skills"),
    }
    owner: dict[str, str] = {}
    for kind, values in categories.items():
        for skill in values:
            if skill in owner:
                raise ValueError(
                    f"Kỹ năng {skill} đang nằm ở cả {owner[skill]} và {kind}; hãy chọn một nhóm."
                )
            owner[skill] = kind

    results: dict[str, dict[str, Any]] = {}
    for kind, values in categories.items():
        matched = [skill for skill in values if skill in candidate]
        missing = [skill for skill in values if skill not in candidate]
        results[kind] = {
            "skills": values,
            "matched": matched,
            "missing": missing,
            "count": len(values),
            "percent": round(100.0 * len(matched) / len(values), 1) if values else None,
        }

    must_count = len(categories["must_have"])
    nice_count = len(categories["nice_to_have"])
    overall: float | None = None
    if must_count:
        if nice_count:
            overall = round(
                (must_weight_value / total_weight) * results["must_have"]["percent"]
                + (nice_weight_value / total_weight) * results["nice_to_have"]["percent"],
                1,
            )
        else:
            overall = results["must_have"]["percent"]

    all_skills = [skill for values in categories.values() for skill in values]
    matched = [skill for skill in all_skills if skill in candidate]
    missing = [skill for skill in all_skills if skill not in candidate]
    return {
        "percent": overall,
        "overall_percent": overall,
        "candidate_skills": sorted(candidate),
        "jd_skills": all_skills,
        "matched": matched,
        "missing": missing,
        "recognized_count": len(all_skills),
        "must_have": results["must_have"],
        "nice_to_have": results["nice_to_have"],
        "unclassified": results["unclassified"],
        "low_confidence": bool(must_count and must_count < 3),
        "method": "confirmed_categorized_skill_overlap",
        "weights": {"must_have": must_weight_value, "nice_to_have": nice_weight_value},
    }


def compare_confirmed_skills_to_jd(
    candidate_skills: Iterable[str], jd_skills: Iterable[str]
) -> dict[str, Any]:
    """Compare user-confirmed skill sets without claiming semantic JD coverage.

    The caller is responsible for showing the extracted JD list and allowing
    the user to remove unsuitable matches. ``low_confidence`` is a conservative
    warning based on a small recognized skill count, not a calibrated score.
    """
    candidate = _candidate_skill_set(candidate_skills, _load_alias_map())
    if isinstance(jd_skills, str):
        raise TypeError("jd_skills phải là iterable các kỹ năng đã xác nhận.")
    try:
        jd_values = list(jd_skills)
    except TypeError as exc:
        raise TypeError("jd_skills phải là iterable các kỹ năng đã xác nhận.") from exc
    if any(not isinstance(skill, str) for skill in jd_values):
        raise TypeError("Mỗi kỹ năng JD đã xác nhận phải là chuỗi.")
    aliases = _load_alias_map()
    normalized_jd = []
    seen = set()
    for value in jd_values:
        canonical = _canonical_skill(value, aliases)
        if canonical and canonical not in seen:
            normalized_jd.append(canonical)
            seen.add(canonical)
    if not normalized_jd:
        raise ValueError("Chưa xác nhận được kỹ năng nào trong mô tả công việc.")
    matched = [skill for skill in normalized_jd if skill in candidate]
    missing = [skill for skill in normalized_jd if skill not in candidate]
    return {
        "percent": round(100.0 * len(matched) / len(normalized_jd), 1),
        "candidate_skills": sorted(candidate),
        "jd_skills": normalized_jd,
        "matched": matched,
        "missing": missing,
        "recognized_count": len(normalized_jd),
        "low_confidence": len(normalized_jd) < 3,
        "method": "confirmed_catalog_skill_overlap",
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


def _role_idf_weights(roles: list[dict[str, Any]], aliases: Mapping[str, str]) -> dict[str, float]:
    """Calculate inverse role frequency once per canonical required skill."""
    frequencies: dict[str, int] = {}
    for role in roles:
        names = {record[1] for record in _role_skill_records(role, aliases)}
        for skill in names:
            frequencies[skill] = frequencies.get(skill, 0) + 1
    role_count = len(roles)
    return {
        skill: math.log((role_count + 1) / (frequency + 1)) + 1
        for skill, frequency in frequencies.items()
    }


def _weighted_role_skill_fit(
    candidate_skills: set[str],
    role: Mapping[str, Any],
    aliases: Mapping[str, str],
    idf: Mapping[str, float],
) -> float:
    records = _role_skill_records(role, aliases)
    denominator = sum(float(idf.get(name, 1.0)) * float(weight) for _, name, weight, _ in records)
    if denominator <= 0:
        return 0.0
    numerator = sum(
        float(idf.get(name, 1.0)) * float(weight)
        for _, name, weight, _ in records
        if name in candidate_skills
    )
    return min(1.0, max(0.0, numerator / denominator))


def role_recommendation_is_low_confidence(profile: Mapping[str, Any]) -> bool:
    """Flag recommendations from profiles with fewer than three claimed skills."""
    if not isinstance(profile, Mapping):
        raise TypeError("profile phải là object.")
    return len(_candidate_skill_set(profile.get("skills", []), _load_alias_map())) < LOW_CONFIDENCE_SKILL_COUNT


def suggest_roles(profile, top_k=5) -> list[dict]:
    """Rank local roles with Role-IDF and bounded, static RIASEC interest fit."""
    if type(top_k) is not int or top_k < 0:
        raise ValueError("top_k phải là int không âm.")
    if not isinstance(profile, Mapping):
        raise TypeError("profile phải là object.")
    if top_k == 0:
        return []
    aliases = _load_alias_map()
    skills = _candidate_skill_set(profile.get("skills", []), aliases)
    roles = _load_role_catalog()
    activities = load_interest_activities()
    activity_ids = resolve_activity_ids(
        profile.get("interest_activity_ids", []), profile.get("interests") or []
    )
    user_vector = user_interest_vector(activity_ids)
    if not skills and not user_vector:
        return []
    role_families = load_role_family_vectors()
    idf = _role_idf_weights(roles, aliases)
    activity_labels = {activity["id"]: activity["label"] for activity in activities}
    results = []
    for role in roles:
        match = _build_role_result(skills, role, aliases)
        skill_part = _weighted_role_skill_fit(skills, role, aliases, idf)
        family = role.get("riasec_vector")
        family_info = role_families.get(role.get("id"), {})
        if not isinstance(family, Mapping):
            family = family_info.get("vector")
        interest_part = interest_fit(user_vector, family) if user_vector else 0.0
        raw_score = 0.75 * skill_part + 0.25 * interest_part
        if skill_part < MIN_SKILL_SIGNAL_FOR_UNCAPPED_ROLE_SCORE:
            raw_score = min(raw_score, LOW_SKILL_ROLE_SCORE_CAP)
        score = round(100 * raw_score, 1)
        if score <= 0:
            continue
        reasons = []
        if match["matched"]:
            reasons.append("Kỹ năng trùng yêu cầu: " + ", ".join(match["matched"]))
        if user_vector and interest_part:
            activity_names = [activity_labels[value] for value in activity_ids]
            family_label = family_info.get("family_label")
            reason = "Sở thích hoạt động tương đồng theo RIASEC"
            if family_label:
                reason += f" với họ nghề {family_label}"
            if activity_names:
                reason += ": " + ", ".join(activity_names)
            reasons.append(reason)
        if skill_part < MIN_SKILL_SIGNAL_FOR_UNCAPPED_ROLE_SCORE:
            reasons.append("Điểm bị giới hạn vì mức trùng kỹ năng dưới ngưỡng 15%.")
        results.append({"role_id": role["id"], "role_name": role.get("name_vi") or role.get("name"),
                        "score": score, "skill_percent": round(100 * skill_part, 1),
                        "interest_percent": round(100 * interest_part, 1), "matched": match["matched"],
                        "missing": match["missing"], "interest_activity_ids": activity_ids,
                        "role_family_id": family_info.get("family_id"),
                        "reasons": reasons, "method": "role_idf_riasec_skill_gated"})
    return sorted(
        results,
        key=lambda row: (-row["score"], -row["skill_percent"], -row["interest_percent"], row["role_id"]),
    )[:top_k]
