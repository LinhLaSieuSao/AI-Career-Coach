"""Load, select, and reveal interview question guidance from bundled data."""

from __future__ import annotations

import json
import logging
import random
import re
import unicodedata
import math
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from .catalog import load_roles
from .skill_extractor import normalize_skill
from .levels import canonical_skill

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "Data"
# Keep these aliases because existing tests and integrations patch the old
# module-level paths when loading isolated question banks.
_PROJECT_ROOT = PROJECT_ROOT
_DATA_DIR = DATA_DIR / "interview_questions"
_LEGACY_DATA_DIR = DATA_DIR / "interview_question"
_SINGLE_FILE = DATA_DIR / "interview_questions.json"
QUESTION_DIRS = (_DATA_DIR, _LEGACY_DATA_DIR)
SINGLE_FILE = _SINGLE_FILE
ROLES_FILE = DATA_DIR / "roles.json"
_RUBRICS_FILE = DATA_DIR / "interview_rubrics.json"


def _records_by_role(payload: Any) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(payload, dict):
        return {}
    roles = payload.get("roles")
    if isinstance(roles, dict):
        return {
            str(role_id): [record for record in records if isinstance(record, dict)]
            for role_id, records in roles.items()
            if isinstance(records, list)
        }
    # Older bundled files have role names as the top-level keys.
    return {
        str(role_id): [record for record in records if isinstance(record, dict)]
        for role_id, records in payload.items()
        if isinstance(records, list)
    }


@lru_cache(maxsize=1)
def _load_question_data() -> dict[str, list[dict[str, Any]]]:
    """Load every question bank while keeping the first definition of a role."""
    merged: dict[str, list[dict[str, Any]]] = {}
    paths = [
        path
        for directory in (_DATA_DIR, _LEGACY_DATA_DIR)
        if directory.is_dir()
        for path in sorted(directory.glob("*.json"), key=lambda item: item.name)
    ]
    # A directory bank is authoritative. The single-file bank is only a
    # fallback for older deployments that have no question directory.
    if not paths and _SINGLE_FILE.is_file():
        paths.append(_SINGLE_FILE)

    for path in paths:
        try:
            with path.open("r", encoding="utf-8") as source:
                payload = json.load(source)
            for role_id, questions in _records_by_role(payload).items():
                if role_id in merged:
                    logger.warning(
                        "role_id %s bị trùng trong %s; giữ dữ liệu đã đọc trước",
                        role_id,
                        path.name,
                    )
                    continue
                merged[role_id] = questions
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.error("Không đọc được dữ liệu câu hỏi %s: %s", path, exc)

    if not paths:
        logger.error("Không tìm thấy thư mục hoặc file dữ liệu câu hỏi trong %s", DATA_DIR)
    return merged


def _clear_cache() -> None:
    """Clear cached question data after replacing a data file."""
    _load_question_data.cache_clear()
    _role_id_by_name.cache_clear()
    _load_rubrics.cache_clear()


@lru_cache(maxsize=1)
def _role_id_by_name() -> dict[str, str | None]:
    """Map unique names to IDs; mark ambiguous names instead of picking a role."""
    try:
        roles = load_roles(ROLES_FILE)
    except (OSError, ValueError):
        return {}

    names: dict[str, str | None] = {}
    for role in roles:
        for name in (role["id"], role["name"], role["name_vi"], f"{role['name_vi']} · {role['name']}"):
            key = normalize_skill(name)
            if key in names and names[key] != role["id"]:
                names[key] = None
            else:
                names[key] = role["id"]
    return names


def _resolve_role_id(value: str) -> str:
    names = _role_id_by_name()
    key = normalize_skill(value)
    if key in names and names[key] is None:
        raise ValueError(f"Tên vị trí '{value}' bị trùng; hãy dùng ID hoặc tên Việt · tên Anh.")
    return names.get(key) or value


def _question_for_id(question_id: str) -> dict[str, Any]:
    matches = [
        question
        for questions in _load_question_data().values()
        for question in questions
        if question.get("id") == question_id
    ]
    if not matches:
        raise ValueError(f"Không tìm thấy câu hỏi có ID '{question_id}'.")
    if len(matches) > 1:
        raise ValueError(f"ID câu hỏi '{question_id}' bị trùng trong ngân hàng dữ liệu.")
    return matches[0]


def get_questions(role_id: str, n: int = 5, seed: int | None = None, focus_skills=None) -> list[dict[str, Any]]:
    """Select up to ``n`` questions, alternating types and hiding answer rubrics."""
    if type(n) is not int or n <= 0:
        raise ValueError("Số câu hỏi phải là int lớn hơn 0.")
    if focus_skills is None:
        focus = None
    else:
        values = [focus_skills] if isinstance(focus_skills, str) else focus_skills
        focus = {canonical_skill(value) for value in values}

    roles = _load_question_data()
    role_id = _resolve_role_id(role_id)
    if role_id not in roles:
        if not roles:
            raise ValueError("Không có dữ liệu câu hỏi trong thư mục Data/interview_question/.")
        raise ValueError(f"Không tìm thấy câu hỏi cho vị trí '{role_id}'.")

    questions = roles[role_id]
    by_type: dict[str, list[dict[str, Any]]] = {"technical": [], "scenario": []}
    for question in questions:
        raw_kind = str(question.get("type", "")).casefold()
        kind = {
            "technical": "technical",
            "kỹ thuật": "technical",
            "scenario": "scenario",
            "tình huống": "scenario",
        }.get(raw_kind)
        if kind in by_type:
            by_type[kind].append(question)

    rng = random.Random(seed)
    for group in by_type.values():
        rng.shuffle(group)

    first_type = next((kind for kind in ("technical", "scenario") if by_type[kind]), "technical")
    order = [first_type, "scenario" if first_type == "technical" else "technical"]
    target = min(n, sum(len(group) for group in by_type.values()))
    if focus is not None:
        target = sum(len(group) for group in by_type.values())
    selected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    safe_fields = ("id", "type", "skill", "level", "weight", "question", "time_minutes", "quality")

    while len(selected) < target:
        progressed = False
        for kind in order:
            while by_type[kind]:
                question = by_type[kind].pop()
                question_id = question.get("id")
                if not isinstance(question_id, str) or question_id in seen_ids:
                    continue
                seen_ids.add(question_id)
                public_question = {key: deepcopy(question[key]) for key in safe_fields if key in question}
                public_question["type"] = kind
                public_question["role_id"] = role_id
                selected.append(public_question)
                progressed = True
                break
            if len(selected) >= target:
                break
        if not progressed:
            break
    if focus is not None:
        selected.sort(key=lambda question: canonical_skill(question.get("skill")) not in focus)
    return selected[:n]


@lru_cache(maxsize=1)
def _load_rubrics():
    if not _RUBRICS_FILE.is_file():
        return {}
    try:
        with _RUBRICS_FILE.open(encoding="utf-8") as source:
            payload = json.load(source)
        result = payload.get("questions", {}) if isinstance(payload, dict) else {}
        return result if isinstance(result, dict) else {}
    except (OSError, ValueError) as exc:
        logger.error("Không đọc được rubric %s: %s", _RUBRICS_FILE, exc)
        return {}


def _valid_rubric(rubric):
    if not isinstance(rubric, dict) or rubric.get("review_status") != "reviewed" or not rubric.get("review_note"):
        return False
    criteria = rubric.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        return False
    ids = set()
    for criterion in criteria:
        if not isinstance(criterion, dict):
            return False
        key, points = criterion.get("id"), criterion.get("points")
        groups = criterion.get("groups")
        if not isinstance(key, str) or not key or key in ids or not criterion.get("label"):
            return False
        ids.add(key)
        if type(points) not in (int, float) or not math.isfinite(points) or points <= 0:
            return False
        if not isinstance(groups, list) or not groups or any(
            not isinstance(group, list) or not group or any(not isinstance(term, str) or not term.strip() for term in group)
            for group in groups
        ):
            return False
    return math.isclose(sum(c["points"] for c in criteria), 10)


def _answer_text(value):
    text = unicodedata.normalize("NFD", normalize_skill(value)).replace("đ", "d")
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).split())


def _term_present(text, term):
    term = _answer_text(term)
    for match in re.finditer(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text):
        # Conservative local negation check. This is not semantic understanding.
        prefix = re.split(r"[.;!?]", text[max(0, match.start()-45):match.start()])[-1]
        if not re.search(r"\b(?:khong|chua|never|not|bo qua)\b(?:\W+\w+){0,3}\W*$", prefix):
            return True
    return False


def score_answer(question_id, answer) -> dict:
    """Local concept rubric; never infer criteria from the reference answer."""
    if not isinstance(question_id, str) or not question_id.strip():
        raise ValueError("question_id phải là chuỗi không rỗng.")
    question = _question_for_id(question_id)
    if not isinstance(answer, str):
        raise TypeError("answer phải là chuỗi.")
    rubric = _load_rubrics().get(question_id)
    if not _valid_rubric(rubric) or question.get("quality") != "reviewed":
        return {"score": None, "criteria": [], "feedback": ["Câu hỏi chưa có rubric máy chấm được review; chưa thể chấm điểm."],
                "method": "rubric", "status": "unavailable", "reason": "missing_or_unreviewed_rubric"}
    text = _answer_text(answer)
    criteria, feedback = [], []
    for criterion in rubric["criteria"]:
        passed = all(any(_term_present(text, term) for term in group) for group in criterion["groups"])
        criteria.append({"id": criterion["id"], "label": criterion["label"], "met": passed,
                         "score": criterion["points"] if passed else 0, "max_score": criterion["points"]})
        feedback.append(("Đạt: " if passed else "Còn thiếu: ") + criterion["label"])
    feedback.append("Chấm từ các nhóm khái niệm được nhắc; không xác minh tính đúng của lập luận, kinh nghiệm hay kết quả thực tế. Có thể bỏ sót cách diễn đạt khác.")
    return {"score": round(min(10, max(0, sum(c["score"] for c in criteria))), 1),
            "criteria": criteria, "feedback": feedback, "method": "rubric", "status": "scored"}


def get_question_feedback(question_id: str) -> dict[str, Any]:
    """Return reference points and warnings after a candidate submits an answer."""
    if not isinstance(question_id, str) or not question_id.strip():
        raise ValueError("question_id phải là chuỗi không rỗng.")

    question = _question_for_id(question_id)
    answer = question.get("reference_answer")
    has_reference_answer = isinstance(answer, str) and bool(answer.strip())
    points = question.get("good_answer_points")
    good_answer_points = (
        [point.strip() for point in points if isinstance(point, str) and point.strip()]
        if isinstance(points, list)
        else []
    )
    if has_reference_answer:
        reference_answer = answer.strip()
    else:
        if not good_answer_points:
            raise ValueError(f"Câu hỏi '{question_id}' chưa có đáp án tham khảo.")
        reference_answer = "\n".join(f"- {point}" for point in good_answer_points)

    red_flags = question.get("red_flags", [])
    return {
        "reference_answer": reference_answer,
        "has_reference_answer": has_reference_answer,
        "good_answer_points": good_answer_points,
        "red_flags": [item for item in red_flags if isinstance(item, str)] if isinstance(red_flags, list) else [],
        "time_minutes": question.get("time_minutes"),
    }


def get_reference_answer(question_id: str) -> str:
    """Return a sample answer or scoring points for a question ID."""
    return get_question_feedback(question_id)["reference_answer"]


def generate_interview_questions(
    missing_skills: Iterable[str],
    max_per_skill: int = 2,
    *,
    role: str | None = None,
) -> list[str]:
    """Compatibility API for callers that still expect question strings."""
    if max_per_skill <= 0:
        return []

    question_data = _load_question_data()
    role_id = _resolve_role_id(role or "")
    role_id = role_id if role_id in question_data else None
    if role_id:
        return [item["question"] for item in get_questions(role_id, max_per_skill) if item.get("question")]

    skills = {skill.strip().casefold() for skill in missing_skills if isinstance(skill, str) and skill.strip()}
    if not skills:
        return []

    exact_matches: list[str] = []
    other_matches: list[str] = []
    for questions in question_data.values():
        for question in questions:
            question_skill = question.get("skill", "")
            keywords = question.get("keywords", [])
            if isinstance(keywords, str):
                keywords = [keywords]
            values = {str(value).strip().casefold() for value in keywords if value}
            if isinstance(question_skill, str) and question_skill.strip():
                values.add(question_skill.strip().casefold())
            if not skills.intersection(values) or not question.get("question"):
                continue
            target = exact_matches if question.get("keywords") else other_matches
            target.append(question["question"])

    rng = random.Random()
    selected: list[str] = []
    for pool in (exact_matches, other_matches):
        remaining = max_per_skill - len(selected)
        if remaining > 0 and pool:
            selected.extend(rng.sample(pool, min(remaining, len(pool))))
    return selected
