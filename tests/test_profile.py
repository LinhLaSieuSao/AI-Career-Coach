from modules.profile import build_profile


def test_returns_fixed_structure():
    result = build_profile({}, [])
    assert set(result.keys()) == {"skills", "interests", "experience"}
    assert result["skills"] == []
    assert result["interests"] == []
    assert result["experience"] == ""


def test_removes_whitespace_and_empty_skills():
    result = build_profile({}, ["  Python  ", "", "   ", "SQL"])
    assert result["skills"] == ["Python", "SQL"]


def test_removes_duplicate_skills_ignoring_case():
    result = build_profile({}, ["Python", "python", " PYTHON ", "SQL"])
    assert result["skills"] == ["Python", "SQL"]


def test_skills_are_sorted():
    result = build_profile({}, ["SQL", "Docker", "Python"])
    assert result["skills"] == ["Docker", "Python", "SQL"]


def test_interests_split_by_comma():
    result = build_profile({"interests": "Phân tích dữ liệu, AI ,  , Web"}, [])
    assert result["interests"] == ["Phân tích dữ liệu", "AI", "Web"]


def test_experience_whitespace_cleaned():
    result = build_profile({"experience": "  Thực tập   tại  công ty  X  "}, [])
    assert result["experience"] == "Thực tập tại công ty X"


def test_handles_none_values():
    result = build_profile({"interests": None, "experience": None}, None)
    assert result == {"skills": [], "interests": [], "experience": ""}
print('cc')