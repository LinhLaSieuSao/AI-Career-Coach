"""Kiểm thử trích xuất kỹ năng và tính nhất quán của dữ liệu."""

import json
from pathlib import Path

from modules.skill_extractor import (
    build_vocabulary,
    extract_skills,
    load_aliases,
    merge_skills,
    normalize_skill,
)


ROOT = Path(__file__).resolve().parents[1]


def _roles() -> list[dict]:
    """Đọc dữ liệu vai trò thực của dự án."""
    return json.loads((ROOT / "data/roles.json").read_text(encoding="utf-8"))


def test_tc01_exact_match_case_insensitive() -> None:
    """Nhận diện kỹ năng chính xác không phân biệt hoa thường."""
    assert extract_skills("PYTHON, git, REST API", {"python", "git", "rest api"}) == ["python", "git", "rest api"]


def test_tc02_empty_text_returns_empty_list() -> None:
    """Văn bản rỗng không có kỹ năng."""
    assert extract_skills("", {"python"}) == []
    assert extract_skills(None, {"python"}) == []


def test_tc03_merge_deduplicates_in_input_order() -> None:
    """Gộp CV trước form và loại tên trùng không phân biệt hoa thường."""
    assert merge_skills(["python", "docker"], ["Python", "SQL"]) == ["python", "docker", "sql"]


def test_tc04_line_break_inside_phrase() -> None:
    """Khoảng xuống dòng trong PDF được xem như dấu cách."""
    assert extract_skills("REST\nAPI", {"rest api"}) == ["rest api"]


def test_tc05_longer_phrase_masks_shorter_phrase() -> None:
    """Tên cụm dài được ưu tiên thay cho kỹ năng con."""
    assert extract_skills("SQL Server", {"sql", "sql server"}) == ["sql server"]


def test_tc06_word_boundary_avoids_java_inside_javascript() -> None:
    """Ranh giới từ ngăn Java khớp bên trong JavaScript."""
    assert extract_skills("JavaScript", {"java", "javascript"}) == ["javascript"]


def test_long_phrase_masks_communication_inside_english_phrase() -> None:
    """Kỹ năng cụm dài che kỹ năng ngắn nằm bên trong."""
    assert extract_skills("tiếng anh giao tiếp", {"giao tiếp", "tiếng anh giao tiếp"}) == ["tiếng anh giao tiếp"]


def test_aliases_map_to_canonical_names() -> None:
    """Các cách viết phổ biến được trả về tên chuẩn."""
    vocabulary = {"reactjs", "nodejs", "power bi", "git", "làm việc nhóm"}
    aliases = {"react": "reactjs", "node.js": "nodejs", "powerbi": "power bi", "github": "git", "teamwork": "làm việc nhóm"}
    assert extract_skills("React, Node.js, PowerBI, GitHub, Teamwork", vocabulary, aliases) == [
        "reactjs", "nodejs", "power bi", "git", "làm việc nhóm"
    ]


def test_normalize_skill_collapses_whitespace_and_is_idempotent() -> None:
    """Chuẩn hóa khoảng trắng lặp và có tính lặp ổn định."""
    normalized = normalize_skill("  TIẾNG   Anh  chuyên ngành  ")
    assert normalized == "tiếng anh chuyên ngành"
    assert normalize_skill(normalized) == normalized


def test_special_character_skills() -> None:
    """Nhận diện kỹ năng có dấu câu và ký tự đặc biệt."""
    vocabulary = {"c#", "c++", "ci/cd", "agile/scrum", "routing & switching"}
    assert extract_skills("c#, c++, CI/CD, Agile/Scrum, Routing & Switching", vocabulary) == [
        "c#", "c++", "ci/cd", "agile/scrum", "routing & switching"
    ]


def test_fuzzy_is_disabled_by_default_and_does_not_confuse_csharp_css() -> None:
    """Mặc định không fuzzy và kỹ năng ngắn không bị nhận nhầm."""
    assert extract_skills("pythno css", {"python", "c#"}) == []
    assert extract_skills("css", {"c#", "css"}, fuzzy=True) == ["css"]


def test_roles_skills_have_resource_keys_after_normalization() -> None:
    """Mọi kỹ năng vai trò đều có tài nguyên tương ứng sau chuẩn hóa."""
    resources = json.loads((ROOT / "data/resources.json").read_text(encoding="utf-8"))
    resource_keys = {normalize_skill(key) for key in resources}
    assert build_vocabulary(_roles()) <= resource_keys


def test_alias_targets_are_in_roles_vocabulary() -> None:
    """Mọi tên chuẩn của alias có trong từ điển vai trò."""
    aliases = load_aliases(ROOT / "data/skill_aliases.json")
    assert set(aliases.values()) <= build_vocabulary(_roles())


def test_roles_have_no_excess_skill_whitespace() -> None:
    """Tên kỹ năng trong roles không còn khoảng trắng thừa."""
    for role in _roles():
        for skill in role.get("skills", []):
            name = skill["name"]
            assert name == name.strip()
            assert "  " not in name
