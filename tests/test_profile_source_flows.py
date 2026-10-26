"""End-user input-source scenarios for the local career profile workflow."""

from modules.matcher import (
    extract_jd_skill_requirements,
    extract_jd_skills,
    match_role,
    suggest_roles,
)
from modules.catalog import DATA_DIR
from modules.catalog import load_roles
from modules.skill_extractor import load_aliases, suggest_skill_candidates
from test_app import _field, _metric, _start, _submit


def test_experience_only_can_supply_reviewable_skill_evidence():
    app = _start()
    _field(app, "Kinh nghiệm (không bắt buộc)").input(
        "Tôi đã dùng Python và SQL để làm báo cáo vận hành."
    )
    app = _submit(app, "", role_id="data_analyst")

    profile = app.session_state["profile_result"]
    assert {"python", "sql"} <= set(profile["skills"])
    assert {"python", "sql"} <= set(profile["skills_from_experience"])
    assert not profile["skills_from_cv"]
    role = next(item for item in load_roles() if item["id"] == "data_analyst")
    assert _metric(app, "Mức độ đáp ứng kỹ năng vị trí") == f"{match_role(profile['skills'], role)['percent']}%"
    assert any("trích từ kinh nghiệm" in item.value for item in app.caption)
    assert any("không tính sở thích, thâm niên" in item.value for item in app.caption)


def test_pasted_cv_is_parsed_and_compared_with_jd_without_file_upload():
    app = _start()
    _field(app, "Dán nội dung CV (nếu không tải tệp, không bắt buộc)").input(
        "Data analyst. Built reports with Python, SQL and Power BI."
    )
    app = _submit(app, skills="", role_id=None, jd="Python, SQL and Tableau")

    assert app.session_state["cv_extraction"]["filename"] == "CV đã nhập tay"
    assert app.session_state["cv_extraction"]["text"].startswith("Data analyst")
    assert app.session_state["profile_result"]["skills_from_cv"]
    comparison = app.session_state["cv_jd_result"]
    assert comparison["jd_skills"] == ["python", "sql", "tableau"]
    assert comparison["matched"] == ["python", "sql"]
    assert comparison["missing"] == ["tableau"]
    assert _metric(app, "Trùng kỹ năng chưa phân loại") == "66.7%"


def test_postgresql_is_a_distinct_recognized_skill_and_common_spacing_alias():
    app = _submit(_start(), "postgre sql", role_id=None)
    profile = app.session_state["profile_result"]
    assert profile["skills"] == ["postgresql"]
    assert profile["unrecognized_skills"] == []
    aliases = load_aliases(DATA_DIR / "skill_aliases.json")
    assert suggest_skill_candidates("postgre sql", {"postgresql"}, aliases) == []


def test_problem_solving_alias_is_recognized_in_a_mandatory_jd_section():
    requirements = extract_jd_skill_requirements(
        "Yêu cầu bắt buộc:\nCó khả năng xử lý vấn đề."
    )

    assert requirements["must_have"] == ["giải quyết vấn đề"]
    assert requirements["unclassified"] == []


def test_typo_suggestion_requires_user_confirmation_before_normalization():
    app = _start()
    _field(app, "Kỹ năng bạn muốn đưa vào hồ sơ").input("postgress")
    next(button for button in app.button if button.label == "Tiếp tục rà soát hồ sơ").click().run()
    suggestion = next(item for item in app.selectbox if item.label.startswith("Tên gần giống với ‘postgress’"))
    assert suggestion.value is None
    assert suggest_skill_candidates("postgress", {"postgresql"}) == ["postgresql"]
    suggestion.select("postgresql")
    next(button for button in app.button if button.label == "Xác nhận hồ sơ và xem kết quả").click().run()
    profile = app.session_state["profile_result"]
    assert profile["skills"] == ["postgresql"]
    assert profile["unrecognized_skills"] == []


def test_review_new_skill_shows_level_before_confirmation_and_deduplicates_alias():
    app = _start()
    _field(app, "Kỹ năng bạn muốn đưa vào hồ sơ").input("SQL")
    next(button for button in app.button if button.label == "Tiếp tục rà soát hồ sơ").click().run()
    assert app.session_state["profile_step"] == 2

    _field(app, "Thêm hoặc sửa tên kỹ năng khác (không bắt buộc)").input("Docker; SQL").run()
    assert not app.exception
    assert len([box for box in app.selectbox if box.label.casefold() == "level · docker"]) == 1
    assert len([box for box in app.selectbox if box.label.casefold() == "level · sql"]) == 1

    next(box for box in app.selectbox if box.label.casefold() == "level · docker").select(1)
    next(button for button in app.button if button.label == "Xác nhận hồ sơ và xem kết quả").click().run()
    assert not app.exception
    profile = app.session_state["profile_result"]
    assert profile["skills"] == ["docker", "sql"]
    assert profile["levels"]["docker"] == 1


def test_interest_changes_exploratory_suggestion_but_does_not_raise_skill_fit():
    roles = load_roles()
    data_analyst = next(item for item in roles if item["id"] == "data_analyst")
    skill_only = suggest_roles({"skills": ["python"]}, top_k=131)
    both = suggest_roles({"skills": ["python"], "interest_activity_ids": ["analyze_data"]}, top_k=131)
    interest_only = suggest_roles({"interest_activity_ids": ["analyze_data"]}, top_k=131)
    by_role = lambda entries: next(item for item in entries if item["role_id"] == "data_analyst")

    assert by_role(skill_only)["skill_percent"] > 0
    assert match_role(["python"], data_analyst)["percent"] == 10.0
    assert by_role(both)["skill_percent"] == by_role(skill_only)["skill_percent"]
    assert by_role(both)["interest_percent"] > by_role(skill_only)["interest_percent"]
    assert by_role(both)["score"] <= 5  # Interest cannot bypass the skill-gated cap.
    assert by_role(interest_only)["score"] <= 5
    assert by_role(interest_only)["method"] == "role_idf_riasec_skill_gated"


def test_jd_skill_scan_covers_the_full_input_not_just_its_start():
    jd = "Mô tả công việc. " + ("Yêu cầu phối hợp với các nhóm. " * 15_000) + " Bắt buộc sử dụng PostgreSQL, Python và SQL Server."
    detected = extract_jd_skills(jd)

    assert "postgresql" in detected
    assert "python" in detected
    assert "sql server" in detected
