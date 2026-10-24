from modules.profile import build_profile, build_profile_from_cv, undo_profile_move
from modules.skill_extractor import normalize_skill


def test_returns_fixed_structure():
    result = build_profile({})
    assert set(result) == {
        "skills",
        "interests",
        "experience",
        "unrecognized_skills",
        "moved",
        "levels",
    }
    assert result["skills"] == []
    assert result["interests"] == []
    assert result["experience"] == ""
    assert result["unrecognized_skills"] == []
    assert result["moved"] == []
    assert result["levels"] == {}


def test_removes_whitespace_and_empty_skills():
    result = build_profile({"skills": ["  Python  ", "", "   ", "SQL"]})
    assert result["skills"] == ["python", "sql"]


def test_removes_duplicate_skills_ignoring_case():
    result = build_profile({"skills": ["Python", "python", " PYTHON ", "SQL"]})
    assert result["skills"] == ["python", "sql"]


def test_skills_are_sorted():
    result = build_profile({"skills": ["SQL", "Docker", "Python"]})
    assert result["skills"] == ["docker", "python", "sql"]


def test_skills_string_is_split_and_normalized_from_data():
    result = build_profile({"skills": "python, sql"})
    assert result["skills"] == ["python", "sql"]


def test_comma_separated_skills_list_entry_is_also_split():
    result = build_profile({"skills": ["python, sql"]})
    assert result["skills"] == ["python", "sql"]


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
        "levels": {},
    }


def test_none_and_empty_mapping_return_empty_profiles():
    empty = {
        "skills": [],
        "interests": [],
        "experience": "",
        "unrecognized_skills": [],
        "moved": [],
        "levels": {},
    }
    assert build_profile(None) == empty
    assert build_profile({}) == empty


def test_shared_aliases_are_recognized_and_deduplicated():
    result = build_profile({"skills": "Node.js; NODEJS; Communication; Python3"})
    assert result["skills"] == ["giao tiếp", "nodejs", "python"]
    assert result["unrecognized_skills"] == []


def test_unknown_claims_are_normalized_retained_and_not_recognized_by_substring():
    result = build_profile({"skills": " SQL   wizardry ; ABC; abc;Python"})
    assert result["skills"] == ["abc", "python", "sql wizardry"]
    assert result["unrecognized_skills"] == ["abc", "sql wizardry"]
    assert normalize_skill(" ABC ") == "abc"  # Normalization does not recognize skills.


def test_explicit_skills_override_form_field():
    result = build_profile({"skills": "unknown"}, skills="Node.js; Python")
    assert result["skills"] == ["nodejs", "python"]
    assert result["unrecognized_skills"] == []


def test_cv_only_profile_extracts_skills_without_turning_prose_into_unknown_claims():
    result = build_profile_from_cv(cv_text="I develop with Python3 and Node.js.")
    assert result["skills"] == ["nodejs", "python"]
    assert result["unrecognized_skills"] == []
    assert set(result) == set(build_profile())


def test_cv_and_form_merge_keeps_unknown_and_other_profile_fields():
    result = build_profile_from_cv({
        "skills": "PYTHON; SQL; Custom   Skill; interest: games",
        "interests": "AI", "experience": " Company, Developer ",
    }, "Python3 and Node.js developer")
    assert result["skills"] == ["custom skill", "nodejs", "python", "sql"]
    assert result["unrecognized_skills"] == ["custom skill"]
    assert result["interests"] == ["AI", "games"]
    assert result["experience"] == "Company, Developer"
    assert result["moved"] == [{"item": "games", "from": "Kỹ năng", "to": "Sở thích"}]


def test_empty_cv_does_not_discard_form_claims():
    form = {"skills": "Python; New Skill"}
    assert build_profile_from_cv(form, "") == build_profile(form)


def test_independent_catalog_is_shared_by_cv_and_manual_profile():
    text = "pandas; MySQL; English; Google Tag Manager; JS; .NET Core"
    form = build_profile({"skills": text})
    cv = build_profile_from_cv(cv_text=text)
    assert form["skills"] == cv["skills"] == [".net core", "english", "google tag manager", "javascript", "mysql", "pandas"]
    assert form["unrecognized_skills"] == cv["unrecognized_skills"] == []


def test_all_p02_examples_are_recognized_as_form_claims_and_cv_skills():
    text = "ML; Communication; Git/GitHub; JS; Node.js; pandas; MySQL; English"
    form = build_profile({"skills": text})
    cv = build_profile_from_cv(cv_text=text)
    assert form["skills"] == cv["skills"] == [
        "english", "giao tiếp", "git", "javascript", "mysql", "nodejs", "pandas", "thuật toán học máy"
    ]
    assert form["unrecognized_skills"] == cv["unrecognized_skills"] == []


def test_undo_multiple_moves_keeps_original_interests_and_normalizes_aliases():
    profile = build_profile({"skills": "Python; interest: Node.js; interest: Custom; interest: Custom", "interests": "Custom"})
    first = undo_profile_move(profile, 0, original_interests=["Custom"])
    assert profile["skills"] == ["python"]  # No mutation of caller state.
    assert first["skills"] == ["nodejs", "python"]
    assert len(first["moved"]) == 2
    second = undo_profile_move(first, 0, original_interests=["Custom"])
    assert second["unrecognized_skills"] == ["custom"]
    assert second["interests"] == ["Custom"]
    third = undo_profile_move(second, 0, original_interests=["Custom"])
    assert third["skills"] == ["custom", "nodejs", "python"]
    assert third["interests"] == ["Custom"]
    assert third["moved"] == []
