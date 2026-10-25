"""Explicit level declarations; absence stays unknown until compute_gap is called."""

from collections.abc import Mapping

from .catalog import DATA_DIR
from .skill_extractor import load_aliases, normalize_skill


def canonical_skill(name, aliases=None):
    if not isinstance(name, str) or not normalize_skill(name):
        raise ValueError("Tên kỹ năng phải là chuỗi không rỗng.")
    aliases = load_aliases(DATA_DIR / "skill_aliases.json") if aliases is None else aliases
    result = normalize_skill(name)
    seen = set()
    while result in aliases and result not in seen:
        seen.add(result)
        result = normalize_skill(aliases[result])
    return result


def normalize_levels(levels):
    if not isinstance(levels, Mapping):
        raise TypeError("levels phải là dict tên kỹ năng → int 0–3.")
    aliases = load_aliases(DATA_DIR / "skill_aliases.json")
    result = {}
    for name, value in levels.items():
        key = canonical_skill(name, aliases)
        if key in result:
            raise ValueError(f"Level trùng sau canonical/alias: {key}.")
        if type(value) is not int or not 0 <= value <= 3:
            raise ValueError(f"Level của {key} phải là int 0–3, không nhận bool.")
        result[key] = value
    return result
