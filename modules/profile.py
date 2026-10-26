"""Build a normalized student profile from form input."""

from __future__ import annotations

import re
import unicodedata
from copy import deepcopy

from .catalog import DATA_DIR, load_skill_vocabulary
from .levels import normalize_levels
from .skill_extractor import extract_skills, load_aliases, merge_skills, normalize_skill


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

    ``form_data`` accepts ``skills``, ``interests``, free-form ``experience``,
    and explicit integer ``levels``. Missing levels remain undeclared.
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
    raw_activity_ids = form_data.get("interest_activity_ids", ())
    activity_ids = _unique([
        value.strip() for value in raw_activity_ids
        if isinstance(value, str) and value.strip()
    ]) if isinstance(raw_activity_ids, (list, tuple)) else []

    kept_skills: list[str] = []
    unrecognized: list[str] = []
    moved: list[dict[str, str]] = []
    vocabulary = load_skill_vocabulary()
    aliases = load_aliases(DATA_DIR / "skill_aliases.json")

    for item in skill_items:
        match = _INTEREST_PREFIX.match(item)
        if match:
            interest = _clean_text(match.group(1))
            if interest:
                interests.append(interest)
                moved.append({"item": interest, "from": "Kỹ năng", "to": "Sở thích"})
            continue

        # A form entry is one claimed skill. Do not treat a known substring
        # (e.g. SQL in "SQL wizardry") as recognition of the entire entry.
        canonical = merge_skills([], [item], aliases)[0]
        kept_skills.append(canonical)
        if canonical not in vocabulary:
            unrecognized.append(canonical)

    levels = normalize_levels(form_data.get("levels", {}))
    for canonical, value in levels.items():
        if value > 0:
            kept_skills.append(canonical)
            if canonical not in vocabulary:
                unrecognized.append(canonical)
    result = {
        "skills": _unique(kept_skills),
        "interests": _unique(interests),
        "experience": _clean_text(form_data.get("experience")),
        "unrecognized_skills": _unique(unrecognized),
        "moved": moved,
        "levels": levels,
    }
    if activity_ids:
        result["interest_activity_ids"] = activity_ids
    return result


def build_profile_from_cv(
    form_data: dict | None = None,
    cv_text: str = "",
    *,
    include_source_metadata: bool = False,
) -> dict:
    """Merge recognized CV skills with form claims, retaining unknown claims.

    Free CV prose is extracted against the shared role vocabulary; arbitrary
    words in that prose are not interpreted as claimed unknown skills. The
    optional source metadata is intended for UI flows that ask users to review
    extracted evidence; the default preserves the established profile schema.
    """
    profile = build_profile(form_data)
    vocabulary = load_skill_vocabulary()
    aliases = load_aliases(DATA_DIR / "skill_aliases.json")
    cv_skills = extract_skills(cv_text, vocabulary, aliases=aliases)
    experience_skills = extract_skills(profile["experience"], vocabulary, aliases=aliases)
    profile["skills"] = _unique(merge_skills(
        [*cv_skills, *experience_skills], profile["skills"], aliases
    ))
    if include_source_metadata:
        profile["skills_from_cv"] = _unique(cv_skills)
        profile["skills_from_experience"] = _unique(experience_skills)
    return profile


def undo_profile_move(profile: dict, index: int, *, original_interests=()) -> dict:
    """Restore one moved entry as a canonical skill without losing base interests."""
    result = deepcopy(profile)
    item = result["moved"].pop(index)["item"]
    interest_key = normalize_skill(item)
    remaining = {normalize_skill(moved["item"]) for moved in result["moved"]}
    original = {normalize_skill(value) for value in original_interests}
    if interest_key not in original | remaining:
        result["interests"] = [value for value in result["interests"] if normalize_skill(value) != interest_key]
    aliases = load_aliases(DATA_DIR / "skill_aliases.json")
    restored = merge_skills([], [item], aliases)[0]
    result["skills"] = _unique([*result["skills"], restored])
    if restored not in load_skill_vocabulary():
        result["unrecognized_skills"] = _unique([*result["unrecognized_skills"], restored])
    return result
