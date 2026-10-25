import csv
import io

import pytest

from modules.export import CSV_FIELDS, export_report


def test_markdown_exports_profile_level_gap_sources_and_unknowns_without_cv_text():
    profile = {
        "role_id": "data_analyst", "skills": ["phân tích dữ liệu"],
        "interests": ["dữ liệu"], "experience": "mô tả nhập tay",
        "levels": {"sql": 1}, "cv_text": "PRIVATE FULL CV TEXT",
    }
    gap = {"role_id": "data_analyst", "match_percent": 25.0, "items": [
        {"skill": "sql", "required": 3, "current": 1, "gap": 2, "priority": 4, "status": "below_required"}
    ]}
    roadmap = {
        "total_weeks": None, "total_known_hours": 2.0, "total_estimated_hours": 1.0,
        "phases": [{"week": 1, "segments": [{"resource_key": "id:shared", "hours": 2, "duration_kind": "published"}]}],
        "resources": {"id:shared": {"title": "Bài | SQL", "url": "https://example.org/sql",
                                      "skills": ["sql", "phân tích dữ liệu"], "planned_hours": None,
                                      "duration_evidence": {"source": "https://publisher.example/duration", "basis": "catalog"}}},
        "unresolved": [{"skill": "sql", "reason": "level_mismatch"}],
        "unknown_duration": [{"resource_key": "id:unknown"}],
    }
    roadmap["resources"]["id:unknown"] = {"title": "Tài liệu chưa có giờ", "url": "https://example.org/unknown", "skills": ["sql"]}
    report = export_report(profile, gap, roadmap)
    assert "phân tích dữ liệu" in report and "below_required" in report
    assert "https://publisher.example/duration" in report
    assert "chưa xác định" in report and "Tài liệu chưa có giờ" in report
    assert "PRIVATE FULL CV TEXT" not in report
    assert r"Bài \| SQL" in report


def test_csv_is_unicode_quoted_formula_safe_and_keeps_shared_resource_once():
    profile = {"role_id": "例", "skills": ["=HYPERLINK(\"https://bad\")", "技能, kỹ năng"],
               "interests": ["+formula"], "experience": "@command", "levels": {"sql": 1}}
    week_plan = [
        {"week": 1, "resources": [{"key": "url:https://example.org/shared", "title": "Bài, học",
                                     "url": "https://example.org/shared", "skills": ["sql", "python"]}],
         "resource_keys": {"sql": ["url:https://example.org/shared"]}, "skills_without_resources": []},
        {"week": 2, "resources": [], "resource_keys": {"python": ["url:https://example.org/shared"]},
         "skills_without_resources": []},
    ]
    output = export_report(profile, {"role_id": "例", "percent": 50, "matched": ["sql"], "missing": ["python"]}, week_plan, "csv")
    rows = list(csv.DictReader(io.StringIO(output)))
    assert list(rows[0]) == list(CSV_FIELDS)
    assert "例" in output and "技能, kỹ năng" in output
    assert "'=HYPERLINK" in output and "'+formula" in output and "'@command" in output
    resources = [row for row in rows if row["section"] == "roadmap"]
    assert len(resources) == 1
    assert resources[0]["url"] == "https://example.org/shared"
    assert any(row["section"] == "presence" and row["score"] == "50" for row in rows)


def test_empty_exports_keep_headers_and_reject_unknown_format():
    assert export_report({}, None, []).startswith("# Báo cáo hồ sơ")
    parsed = list(csv.reader(io.StringIO(export_report({}, None, [], "csv"))))
    assert parsed == [list(CSV_FIELDS)]
    with pytest.raises(ValueError, match="format"):
        export_report({}, None, [], "pdf")


def test_role_roadmap_shared_keys_are_not_exported_as_missing_material():
    roadmap = [
        {"week": 1, "resources": [{"key": "id:one", "title": "Dùng chung", "url": "https://example.org/one", "skills": ["python", "sql"]}],
         "resource_keys": {"python": ["id:one"]}, "skills_without_resources": []},
        {"week": 2, "resources": [], "resource_keys": {"sql": ["id:one"]}, "skills_without_resources": []},
    ]
    content = export_report({"role_id": "demo", "skills": []}, None, roadmap)
    assert content.count("Dùng chung") == 1
    assert "no_resources" not in content
