from modules.practice_guidance import get_partial_resource_assignment, get_practice_routes


def _resource(**changes):
    return {
        "id": "partial-resource",
        "title": "Intro resource",
        "url": "https://example.org/intro",
        "verified": True,
        "content_review_status": "partial",
        "review_note": "Covers the basics only; applied practice is not included.",
        **changes,
    }


def test_partial_sql_resource_becomes_a_role_contextual_portfolio_task():
    resources = {"sql": {"category": "technical", "resources": [_resource()]}}

    task = get_partial_resource_assignment(
        "sql", _resource(), resources, role_context="Data Analyst"
    )

    assert task is not None
    assert task["title"] == "Bài tập/portfolio theo bối cảnh"
    assert task["scope"] == "Covers the basics only; applied practice is not included."
    assert "Data Analyst" in " ".join(task["steps"])
    assert "dữ liệu giả lập" in " ".join(task["steps"])
    assert "README" in task["evidence"]


def test_partial_soft_skill_resource_keeps_supervised_roleplay_and_feedback():
    resources = {"giao tiếp": {"category": "soft_skill", "resources": [_resource()]}}

    task = get_partial_resource_assignment("giao tiếp", _resource(), resources)

    assert task is not None
    assert "phản hồi" in " ".join(task["steps"])
    assert "người quan sát" in task["evidence"]
    assert get_practice_routes(["giao tiếp"], resources)


def test_non_partial_material_does_not_receive_partial_scope_assignment():
    resources = {"sql": {"category": "technical", "resources": []}}

    assert get_partial_resource_assignment(
        "sql", _resource(content_review_status="reviewed"), resources
    ) is None


def test_six_transversal_skills_have_observable_practice_without_claiming_level_coverage():
    skills = ["giải quyết vấn đề", "tiếng anh chuyên ngành", "excel", "cẩn thận",
              "đọc bản vẽ kỹ thuật", "chăm sóc khách hàng"]
    resources = {skill: {"category": "technical", "resources": []} for skill in skills}
    routes = get_practice_routes(skills, resources)
    assert {route["skill"] for route in routes} == set(skills)
    assert all(len(route["observation_checklist"]) >= 3 for route in routes)
    english = next(route for route in routes if route["skill"] == "tiếng anh chuyên ngành")
    assert len(english["tracks"]) == 5
    assert all(track["reference_url"].startswith("https://") for track in english["tracks"])
    assert "không" in english["framing"].casefold()
