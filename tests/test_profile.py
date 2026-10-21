from modules.profile import build_profile


def test_returns_fixed_structure():
    result = build_profile({})
    assert set(result) == {
        "skills",
        "interests",
        "experience",
        "unrecognized_skills",
        "moved",
    }
    assert result["skills"] == []
    assert result["interests"] == []
    assert result["experience"] == ""
    assert result["unrecognized_skills"] == []
    assert result["moved"] == []


def test_removes_whitespace_and_empty_skills():
    result = build_profile({"skills": ["  Python  ", "", "   ", "SQL"]})
    assert result["skills"] == ["Python", "SQL"]


def test_removes_duplicate_skills_ignoring_case():
    result = build_profile({"skills": ["Python", "python", " PYTHON ", "SQL"]})
    assert result["skills"] == ["Python", "SQL"]


def test_skills_are_sorted():
    result = build_profile({"skills": ["SQL", "Docker", "Python"]})
    assert result["skills"] == ["Docker", "Python", "SQL"]


def test_skills_string_is_split_and_normalized_from_data():
    result = build_profile({"skills": "python, sql"})
    assert result["skills"] == ["Python", "SQL"]


def test_comma_separated_skills_list_entry_is_also_split():
    result = build_profile({"skills": ["python, sql"]})
    assert result["skills"] == ["Python", "SQL"]


def test_interests_split_by_comma():
    result = build_profile({"interests": "Phân tích dữ liệu, AI ,  , Web"})
    assert result["interests"] == ["AI", "Phân tích dữ liệu", "Web"]


def test_interesting_skill_entry_moves_to_interests():
    result = build_profile({"skills": "interesting: play games"})
    assert result["skills"] == []
    assert result["interests"] == ["play games"]
    assert result["moved"] == [
        {"item": "play games", "from": "Kỹ năng", "to": "Sở thích"}
    ]


def test_unrecognized_skill_is_retained_and_reported():
    result = build_profile({"skills": "abc"})
    assert result["skills"] == ["abc"]
    assert result["unrecognized_skills"] == ["abc"]


def test_experience_is_not_split_on_commas():
    result = build_profile({"experience": "Công Ty A, Data Intern, 2024"})
    assert result["experience"] == "Công Ty A, Data Intern, 2024"


def test_experience_whitespace_cleaned():
    result = build_profile({"experience": "  Thực tập   tại  công ty  X  "})
    assert result["experience"] == "Thực tập tại công ty X"


def test_handles_none_values():
    result = build_profile({"interests": None, "experience": None})
    assert result == {
        "skills": [],
        "interests": [],
        "experience": "",
        "unrecognized_skills": [],
        "moved": [],
    }


def test_none_and_empty_mapping_return_empty_profiles():
    empty = {
        "skills": [],
        "interests": [],
        "experience": "",
        "unrecognized_skills": [],
        "moved": [],
    }
    assert build_profile(None) == empty
    assert build_profile({}) == empty
