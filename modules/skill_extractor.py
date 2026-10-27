# SPDX-License-Identifier: MIT
"""Trích xuất và hợp nhất kỹ năng bằng quy tắc từ vựng."""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable


_VERSIONED_SKILL_BASES = {
    "angular", "angularjs", "asp.net", "asp.net core", "c#", "c++", "django",
    "docker", "flask", "java", "kotlin", "laravel", "maven", "mongodb",
    "mysql", "node", "node.js", "nodejs", "postgresql", "python", "pytorch",
    "react", "react native", "react.js", "reactjs", "redis", "spring boot",
    "sql server", "swift", "tensorflow", "typescript", "vue", "vue.js", "vuejs",
    ".net", ".net core", ".net framework", "windows server",
}

# Explicit statements of missing experience are not evidence of a skill.
# Keep this narrow: ambiguous prose still goes through the review step.
_NEGATED_CLAIM = re.compile(
    r"\b(?:chưa\s+(?:từng\s+)?(?:sử\s+dụng|dùng|học|biết|thành\s+thạo|"
    r"có\s+kinh\s+nghiệm(?:\s+(?:với|về))?)|"
    r"không\s+(?:sử\s+dụng|dùng|biết|thành\s+thạo|"
    r"có\s+kinh\s+nghiệm(?:\s+(?:với|về))?)|"
    r"never\s+(?:used|learned|worked\s+with)|"
    r"not\s+(?:familiar\s+with|experienced\s+with|proficient\s+in)|"
    r"no\s+experience\s+(?:with|in))\b",
    re.IGNORECASE,
)
_POSITIVE_CLAIM = re.compile(
    r"\b(?:đã\s+(?:sử\s+dụng|dùng|học|biết|làm\s+việc\s+với)|"
    r"có\s+kinh\s+nghiệm\s+(?:với|về)|"
    r"(?:have|has)\s+experience\s+(?:with|in)|"
    r"(?:used|learned|worked\s+with))\b",
    re.IGNORECASE,
)
_CLAUSE_BREAK = re.compile(r"[.;!?]|\b(?:nhưng|tuy\s+nhiên|but|however)\b", re.IGNORECASE)


def _is_explicitly_negated(source: str, start: int) -> bool:
    """Exclude a nearby, explicit lack-of-skill claim from extracted evidence."""
    # A bounded window avoids quadratic scans in a long pasted CV with many
    # repeated skill mentions. The rule only considers nearby negation anyway.
    prefix = source[max(0, start - 128):start]
    boundaries = list(_CLAUSE_BREAK.finditer(prefix))
    clause = prefix[boundaries[-1].end():] if boundaries else prefix
    negations = list(_NEGATED_CLAIM.finditer(clause))
    if not negations:
        return False
    last_negation = negations[-1]
    if len(clause) - last_negation.end() > 60:
        return False
    return not any(match.start() >= last_negation.end() for match in _POSITIVE_CLAIM.finditer(clause))


def normalize_skill(name: str) -> str:
    """Normalize labels and strip version suffixes only from known software skills."""
    cleaned = unicodedata.normalize("NFC", name or "").strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    versioned = re.fullmatch(r"(?P<base>.+?)\s+v?\d+(?:\.\d+)*", cleaned, flags=re.IGNORECASE)
    if versioned and versioned.group("base") in _VERSIONED_SKILL_BASES:
        cleaned = versioned.group("base")
    return cleaned


def _skill_names(roles: Iterable[dict[str, Any]]) -> Iterable[str]:
    """Duyệt tên kỹ năng trong danh sách vị trí."""
    for role in roles:
        for skill in role.get("skills", []):
            if isinstance(skill, dict):
                yield str(skill.get("name", ""))
            elif isinstance(skill, str):
                yield skill


def build_vocabulary(roles: list[dict[str, Any]]) -> set[str]:
    """Tạo từ điển kỹ năng đã chuẩn hóa từ dữ liệu vị trí."""
    return {name for raw in _skill_names(roles) if (name := normalize_skill(raw))}


def load_aliases(path: str | Path) -> dict[str, str]:
    """Đọc alias và chuẩn hóa cả khóa lẫn tên kỹ năng đích."""
    with Path(path).open(encoding="utf-8") as file:
        raw_aliases = json.load(file)
    return {
        normalize_skill(alias): normalize_skill(canonical)
        for alias, canonical in raw_aliases.items()
        if normalize_skill(alias) and normalize_skill(canonical)
    }


def extract_skills(
    text: str | None,
    vocabulary: Iterable[str],
    aliases: dict[str, str] | None = None,
    fuzzy: bool = False,
) -> list[str]:
    """Trích kỹ năng theo thứ tự xuất hiện, ưu tiên cụm dài và che span đã khớp."""
    if not text:
        return []
    working = normalize_skill(text.replace("\r", " ").replace("\n", " "))
    source = working
    alias_map = {normalize_skill(k): normalize_skill(v) for k, v in (aliases or {}).items()}
    canonical_vocab = {normalize_skill(skill) for skill in vocabulary if normalize_skill(skill)}
    candidates: dict[str, str] = {skill: skill for skill in canonical_vocab}
    for alias, canonical in alias_map.items():
        if canonical in canonical_vocab and alias:
            candidates[alias] = canonical

    matches: list[tuple[int, str]] = []
    for phrase, canonical in sorted(candidates.items(), key=lambda item: (-len(item[0]), item[0])):
        pattern = re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)")
        found = list(pattern.finditer(working))
        if found:
            matches.extend(
                (match.start(), canonical) for match in found
                if not _is_explicitly_negated(source, match.start())
            )
            working = pattern.sub(lambda match: " " * len(match.group(0)), working)

    if fuzzy:
        try:
            from rapidfuzz.fuzz import ratio
        except ImportError:
            ratio = None
        if ratio is not None:
            one_word = [skill for skill in canonical_vocab if " " not in skill and len(skill) >= 5 and re.fullmatch(r"\w+", skill)]
            for token_match in re.finditer(r"(?<!\w)\w{5,}(?!\w)", working):
                token = token_match.group(0)
                best = max(((ratio(token, skill), skill) for skill in one_word), default=(0, ""))
                if best[0] >= 90 and not _is_explicitly_negated(source, token_match.start()):
                    matches.append((token_match.start(), best[1]))

    result: list[str] = []
    seen: set[str] = set()
    for _, canonical in sorted(matches, key=lambda item: item[0]):
        if canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result


def merge_skills(
    cv_skills: Iterable[str],
    form_skills: Iterable[str],
    aliases: dict[str, str] | None = None,
) -> list[str]:
    """Gộp kỹ năng CV trước, form sau; chuẩn hóa, ánh xạ alias và khử trùng."""
    alias_map = {normalize_skill(k): normalize_skill(v) for k, v in (aliases or {}).items()}
    result: list[str] = []
    seen: set[str] = set()
    for skill in (*list(cv_skills), *list(form_skills)):
        canonical = alias_map.get(normalize_skill(skill), normalize_skill(skill))
        if canonical and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result


def suggest_skill_candidates(
    value: str,
    vocabulary: Iterable[str],
    aliases: dict[str, str] | None = None,
    *,
    limit: int = 3,
) -> list[str]:
    """Return close catalog labels for a user-confirmed spelling suggestion.

    Suggestions never normalize or replace the user's claim automatically.
    Accent and punctuation are ignored for comparison, which helps with common
    misspellings while keeping canonical matching itself exact.
    """
    if not isinstance(value, str):
        raise TypeError("Tên kỹ năng phải là chuỗi.")
    if type(limit) is not int or limit < 0:
        raise ValueError("limit phải là số nguyên không âm.")
    if not value.strip() or limit == 0:
        return []

    def comparable(text: str) -> str:
        decomposed = unicodedata.normalize("NFD", normalize_skill(text))
        plain = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
        return re.sub(r"[^a-z0-9]+", "", plain)

    source = comparable(value)
    alias_map = {normalize_skill(key): normalize_skill(target) for key, target in (aliases or {}).items()}
    options = set()
    for item in vocabulary:
        canonical = alias_map.get(normalize_skill(item), normalize_skill(item))
        if canonical:
            options.add(canonical)
    # If the entered label is an explicit catalog alias, it is already
    # recognized by the profile parser; do not offer its canonical label as a
    # fuzzy correction (for example, "postgre sql" -> "postgresql").
    if alias_map.get(normalize_skill(value), normalize_skill(value)) in options:
        return []
    ranked = []
    for candidate in options:
        target = comparable(candidate)
        if not target or candidate == normalize_skill(value):
            continue
        similarity = SequenceMatcher(a=source, b=target).ratio()
        if similarity >= 0.76:
            ranked.append((similarity, candidate))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [candidate for _, candidate in ranked[:limit]]


SKILL_DATA_DIR = Path(__file__).resolve().parents[1] / 'data'


def canonical_skill(name, aliases=None):
    if not isinstance(name, str) or not normalize_skill(name):
        raise ValueError("Tên kỹ năng phải là chuỗi không rỗng.")
    aliases = load_aliases(SKILL_DATA_DIR / "skill_aliases.json") if aliases is None else aliases
    result = normalize_skill(name)
    seen = set()
    while result in aliases and result not in seen:
        seen.add(result)
        result = normalize_skill(aliases[result])
    return result


def normalize_levels(levels):
    if not isinstance(levels, Mapping):
        raise TypeError("levels phải là dict tên kỹ năng → int 0–3.")
    aliases = load_aliases(SKILL_DATA_DIR / "skill_aliases.json")
    result = {}
    for name, value in levels.items():
        key = canonical_skill(name, aliases)
        if key in result:
            raise ValueError(f"Level trùng sau canonical/alias: {key}.")
        if type(value) is not int or not 0 <= value <= 3:
            raise ValueError(f"Level của {key} phải là int 0–3, không nhận bool.")
        result[key] = value
    return result
