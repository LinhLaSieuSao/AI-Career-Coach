"""Trích xuất và hợp nhất kỹ năng bằng quy tắc từ vựng."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable


def normalize_skill(name: str) -> str:
    """Chuẩn hóa tên kỹ năng; matcher và recommender nên dùng chung hàm này."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", name or "").strip().lower())


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
            matches.extend((match.start(), canonical) for match in found)
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
                if best[0] >= 90:
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
