"""Build a normalized student profile from form input."""

from __future__ import annotations

import re
import unicodedata

from .skill_extractor import normalize_skill


_LIST_SEPARATOR = re.compile(r"[,;\n]+")
_INTEREST_PREFIX = re.compile(r"^(?:interesting|interest|sở thích)\s*:\s*(.+)$", re.IGNORECASE)


def _clean_text(value: str | None) -> str:
    """Collapse whitespace and return an empty string for missing values."""
    if not value:
        return ""
    return " ".join(unicodedata.normalize("NFC", str(value)).split())


def _split_values(value: str | list[str] | tuple[str, ...] | None) -> list[str]:
    """Split skill and interest fields on commas, semicolons, and line breaks."""
    if value is None:
        return []
    sources = value if isinstance(value, (list, tuple)) else (value,)
    result: list[str] = []
    for source in sources:
        result.extend(
            cleaned
            for part in _LIST_SEPARATOR.split(str(source))
            if (cleaned := _clean_text(part))
        )
    return result


def _unique(values: list[str]) -> list[str]:
    seen: dict[str, str] = {}
    for value in values:
        seen.setdefault(value.casefold(), value)
    return sorted(seen.values(), key=str.casefold)


def build_profile(
    form_data: dict | None = None,
    skills: list[str] | str | None = None,
) -> dict:
    """Normalize profile input and classify recognized, moved, and unknown skills.

    ``form_data`` accepts ``skills``, ``interests``, and free-form ``experience``.
    An explicit ``skills`` argument takes precedence over ``form_data['skills']``.
    Experience is deliberately kept as one text field, including commas.

    The returned ``moved`` entries contain ``item``, ``from``, and ``to`` labels.
    Unrecognized skills stay in ``skills`` and are also listed separately so the
    UI can ask whether the user wants to keep each one.
    """
    form_data = form_data or {}
    raw_skills = skills if skills is not None else form_data.get("skills")
    skill_items = _split_values(raw_skills)
    interests = _split_values(form_data.get("interests"))

    kept_skills: list[str] = []
    unrecognized: list[str] = []
    moved: list[dict[str, str]] = []

    for item in skill_items:
        match = _INTEREST_PREFIX.match(item)
        if match:
            interest = _clean_text(match.group(1))
            if interest:
                interests.append(interest)
                moved.append({"item": interest, "from": "Kỹ năng", "to": "Sở thích"})
            continue

        canonical = normalize_skill(item)
        if canonical is None:
            kept_skills.append(item)
            unrecognized.append(item)
        else:
            kept_skills.append(canonical)

    return {
        "skills": _unique(kept_skills),
        "interests": _unique(interests),
        "experience": _clean_text(form_data.get("experience")),
        "unrecognized_skills": _unique(unrecognized),
        "moved": moved,
    }
