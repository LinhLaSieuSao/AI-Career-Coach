from modules.skill_extractor import normalize_skill


def test_short_alias_normalizes_to_python():
    assert normalize_skill("py") == "Python"


def test_normalization_ignores_case_and_surrounding_whitespace():
    assert normalize_skill("PY ") == "Python"


def test_unknown_skill_returns_none():
    assert normalize_skill("abc") is None
