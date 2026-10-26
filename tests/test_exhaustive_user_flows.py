"""Adversarial but deterministic end-user journeys across the local app.

The pure parser/matcher/export checks use synthetic data. AppTest covers the
Streamlit workflow without starting a separate server; browser-only behavior
such as real focus rings and resize/reload remains in the audit as a manual QA
boundary rather than being represented as an AppTest assertion.
"""

from __future__ import annotations

import csv
import io

import pytest
from streamlit.testing.v1 import AppTest

from document_fixtures import docx_bytes, pdf_bytes
from fixtures.cv_edge_cases import create_cv_edge_cases
from modules.catalog import load_roles
from modules.export import _cell, export_report
from modules.matcher import (
    compare_confirmed_jd_requirements,
    compute_gap,
    extract_jd_skill_requirements,
    match_role,
    role_recommendation_is_low_confidence,
    suggest_roles,
)
from modules.profile import build_profile, build_profile_from_cv
from modules.cv_parser import parse_document
from modules.recommender import build_roadmap
from modules.submission import PROFILE_REVIEW_REQUIRED_SKILL_MESSAGE
from test_app import _draft, _field, _metric, _start, _submit


def _click(app, label):
    return next(button for button in app.button if button.label == label).click().run()


@pytest.mark.parametrize(
    "raw",
    [
        "dữ liệu, Python",
        "du lieu; python",
        "DỮ LIỆU\nPYTHON",
        "kyx nawng; phana tichs",
        "• Python\n* SQL\n- Excel",
        "“Python”\u00a0and\u00a0SQL\n\n\nExcel",
        "C",
        "R",
        "a",
        "Python 3.12; SQL Server 2019; React.js / ReactJS; C# / .NET; vue3",
    ],
    ids=[
        "vietnamese-accents", "no-accents", "uppercase", "telex-noise",
        "bullets", "smart-quotes-and-nbsp", "single-c", "single-r",
        "single-a", "technology-versions",
    ],
)
def test_unpolished_human_text_is_safe_and_does_not_invent_skill_level(raw):
    profile = build_profile({"skills": raw})

    assert profile["skills"]
    assert set(profile["levels"].values()) == set()
    assert set(profile["unrecognized_skills"]) <= set(profile["skills"])


def test_long_pasted_cv_over_ten_thousand_words_is_parsed_in_app_without_upload():
    app = _start()
    long_cv = ("project experience teamwork delivery " * 10_001) + "Python SQL"
    _field(app, "Dán nội dung CV (nếu không tải tệp, không bắt buộc)").input(long_cv)
    _click(app, "Tiếp tục rà soát hồ sơ")

    assert not app.exception
    assert app.session_state["profile_step"] == 2
    assert {"python", "sql"} <= set(app.session_state["profile_draft"]["profile"]["skills"])
    assert app.session_state["profile_draft"]["cv_extraction"]["filename"] == "CV đã nhập tay"


def test_back_edit_preserves_form_flow_and_replaces_draft_skills():
    app = _draft(_start(), "Python")
    _click(app, "Quay lại chỉnh đầu vào")
    _field(app, "Kỹ năng bạn muốn đưa vào hồ sơ").input("Python, SQL")
    _click(app, "Tiếp tục rà soát hồ sơ")

    draft = app.session_state["profile_draft"]["profile"]
    assert not app.exception
    assert app.session_state["profile_step"] == 2
    assert {"python", "sql"} <= set(draft["skills"])


def test_demo_can_be_replaced_by_manual_profile_without_synthetic_label():
    app = _start()
    app = app.button(key="use_demo_backend-java").click().run()
    assert app.session_state["profile_draft"]["demo_id"] == "backend-java"

    _click(app, "Quay lại chỉnh đầu vào")
    _field(app, "Kỹ năng bạn muốn đưa vào hồ sơ").input("Python, SQL")
    _click(app, "Tiếp tục rà soát hồ sơ")
    _click(app, "Xác nhận hồ sơ và xem kết quả")

    assert not app.exception
    assert app.session_state["profile_result"]["skills"] == ["python", "sql"]
    assert app.session_state["active_demo_profile_id"] is None
    assert not any("Hồ sơ tổng hợp minh họa" in item.value for item in app.info)


def test_sequential_double_submit_reruns_keep_one_committed_revision():
    app = _start()
    _field(app, "Kỹ năng bạn muốn đưa vào hồ sơ").input("Python, SQL")
    _click(app, "Tiếp tục rà soát hồ sơ")
    assert app.session_state["profile_step"] == 2
    assert not app.exception

    _click(app, "Xác nhận hồ sơ và xem kết quả")
    assert app.session_state["profile_revision"] == 1
    app.run()
    assert not app.exception
    assert app.session_state["profile_revision"] == 1


def test_cancelled_upload_and_replacement_upload_are_both_safe():
    app = _start()
    app.file_uploader[0].set_value(("first.pdf", pdf_bytes("PostgreSQL"), "application/pdf"))
    app.file_uploader[0].set_value((
        "replacement.docx", docx_bytes("Python"),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ))
    _click(app, "Tiếp tục rà soát hồ sơ")
    assert app.session_state["profile_draft"]["cv_extraction"]["filename"] == "replacement.docx"
    assert "python" in app.session_state["profile_draft"]["profile"]["skills"]
    assert "postgresql" not in app.session_state["profile_draft"]["profile"]["skills"]

    cancelled = _start()
    cancelled.file_uploader[0].set_value(("cancelled.docx", docx_bytes("Python"), "application/docx"))
    cancelled.file_uploader[0].clear()
    _field(cancelled, "Kỹ năng bạn muốn đưa vào hồ sơ").input("SQL")
    _click(cancelled, "Tiếp tục rà soát hồ sơ")
    assert not cancelled.exception
    assert cancelled.session_state["profile_draft"]["cv_extraction"] is None
    assert cancelled.session_state["profile_draft"]["profile"]["skills"] == ["sql"]


@pytest.mark.parametrize(
    "filename,payload",
    [
        ("renamed.exe.pdf", b"MZ\x90\x00synthetic executable"),
        ("renamed.png.pdf", b"\x89PNG\r\n\x1a\nnot a PDF"),
        ("renamed.txt.docx", b"plain text, not a zip archive"),
    ],
    ids=["exe-as-pdf", "png-as-pdf", "text-as-docx"],
)
def test_tampered_extensions_return_safe_parser_errors_without_stack_trace(filename, payload):
    result = parse_document(io.BytesIO(payload), filename)

    assert result["error_code"] == "INVALID_SIGNATURE"
    assert "định dạng" in result["message"].casefold()
    assert "Traceback" not in result["message"]


def test_scanned_twenty_page_and_two_column_documents_are_explained(tmp_path):
    assert parse_document(io.BytesIO(pdf_bytes(image=True)), "scan.pdf")["error_code"] == "SCANNED_PDF"
    long_pdf = parse_document(io.BytesIO(pdf_bytes("Python SQL", pages=20)), "twenty-pages.pdf")
    assert long_pdf["pages_read"] == 10
    assert long_pdf["total_pages"] == 20
    assert long_pdf["page_truncated"] is True

    fixtures = create_cv_edge_cases(tmp_path)
    two_column = parse_document(fixtures["two_column_resume.pdf"])
    assert two_column["error_code"] is None
    assert "Python, SQL" in two_column["text"]
    assert "Báo cáo dữ liệu" in two_column["text"]


def test_career_switcher_low_signal_and_opposed_interests_are_bounded():
    roles = {role["id"]: role for role in load_roles()}
    switcher = build_profile({"skills": "Kế toán, Excel, Phân tích tài chính"})
    data_gap = match_role(switcher["skills"], roles["data_engineer"])
    ml_gap = match_role(switcher["skills"], roles["machine_learning_engineer"])
    assert {"sql", "python"} <= set(data_gap["missing"])
    assert "python" in ml_gap["missing"]

    one_skill = build_profile({"skills": "Python"})
    assert role_recommendation_is_low_confidence(one_skill)

    design = {"skills": ["figma", "ui design", "photoshop"],
              "interest_activity_ids": ["operate_equipment", "solve_technical"]}
    ranked = suggest_roles(design, top_k=len(roles))
    security = next(item for item in ranked if item["role_id"] == "security_engineer")
    assert security["score"] <= 5
    assert security["interest_percent"] > security["skill_percent"]


def test_realistic_jd_sections_are_classified_and_weighted_only_after_confirmation():
    jd = (
        "Yêu cầu bắt buộc:\nPython, SQL, Excel\n"
        "Điểm cộng:\nTableau\nMô tả công việc:\nPower BI"
    )
    parsed = extract_jd_skill_requirements(jd)
    assert set(parsed["must_have"]) >= {"python", "sql", "excel"}
    assert parsed["nice_to_have"] == ["tableau"]
    assert "power bi" in parsed["unclassified"]

    comparison = compare_confirmed_jd_requirements(
        ["python", "sql"], parsed["must_have"], parsed["nice_to_have"], parsed["unclassified"]
    )
    assert comparison["must_have"]["matched"] == ["python", "sql"]
    assert comparison["must_have"]["missing"] == ["excel"]
    assert comparison["overall_percent"] is not None
    without_must = compare_confirmed_jd_requirements(["python"], [], ["tableau"], ["python"])
    assert without_must["overall_percent"] is None


def test_step_two_custom_skills_and_all_levels_are_persisted_explicitly():
    app = _draft(_start(), "Python, SQL")
    _field(app, "Thêm hoặc sửa tên kỹ năng khác (không bắt buộc)").input("Docker; Tableau; Stakeholder communication")
    _click(app, "Xác nhận hồ sơ và xem kết quả")

    assert not app.exception
    assert {"python", "sql", "docker", "tableau", "stakeholder communication"} <= set(
        app.session_state["profile_result"]["skills"]
    )

    app = _submit(_start(), "Python, SQL, Excel, Power BI", levels={"python": 0, "sql": 1, "excel": 3})
    levels = app.session_state["profile_result"]["levels"]
    assert levels["python"] == 0
    assert levels["sql"] == 1
    assert levels["excel"] == 3
    assert "power bi" not in levels  # Chưa khai báo remains unknown.
    gap = compute_gap(levels, next(role for role in load_roles() if role["id"] == "data_analyst"))
    assert all(item["gap"] == max(0, item["required"] - item["current"]) for item in gap["items"])


def test_deselecting_all_recognized_skills_keeps_user_in_review_with_actionable_error():
    app = _draft(_start(), "Python")
    next(item for item in app.multiselect if item.label.startswith("Kỹ năng nhận diện")).set_value([])
    _click(app, "Xác nhận hồ sơ và xem kết quả")

    assert not app.exception
    assert app.session_state["profile_step"] == 2
    assert any(PROFILE_REVIEW_REQUIRED_SKILL_MESSAGE in item.value for item in app.error)
    assert app.session_state.get("profile_result") is None


def test_results_show_all_five_tabs_heuristic_disclosure_gaps_and_diagram_data():
    app = _submit(_start(), "Python", role_id="data_analyst")
    import app as app_module

    assert app_module.RESULT_TABS == ("Tóm tắt", "Khoảng cách", "Lộ trình", "Tài liệu", "Phỏng vấn")
    assert len(app.tabs) == 5
    all_copy = "\n".join(item.value for item in app.caption) + "\n" + "\n".join(
        item.value for item in app.markdown
    )
    assert "heuristic" in all_copy.casefold()
    assert "không phải" in all_copy.casefold()
    assert "Kỹ năng còn thiếu" in all_copy
    assert any(item.label.startswith("Giai đoạn ") for item in app.expander)
    assert "Sơ đồ lộ trình" in "\n".join(item.value for item in app.markdown)


def test_exports_are_utf8_formula_safe_and_do_not_include_source_cv_text():
    profile = {"role_id": "data_analyst", "skills": ["=SUM(1,1)", "+cmd", "-2", "@HYPERLINK"],
               "interests": ["dữ liệu"], "experience": "Kinh nghiệm do người dùng nhập", "cv_text": "PRIVATE FULL CV BODY"}
    markdown = export_report(profile, None, [])
    csv_text = export_report(profile, None, [], "csv")
    rows = list(csv.DictReader(io.StringIO(csv_text, newline="")))

    assert "PRIVATE FULL CV BODY" not in markdown and "PRIVATE FULL CV BODY" not in csv_text
    assert "Kinh nghiệm do người dùng nhập" in csv_text
    assert "dữ liệu" in csv_text
    profile_skills = next(row for row in rows if row["section"] == "profile" and row["skill"] == "skills")
    assert profile_skills["note"].startswith("'=")
    for prefix in "=+-@":
        assert _cell(prefix + "malicious") == "'" + prefix + "malicious"
    assert csv_text.encode("utf-8").decode("utf-8") == csv_text
    assert csv_text.startswith("section,role_id,")


def test_results_and_interview_copy_explain_local_privacy_and_no_answer_scoring():
    app = _submit(_start(), "Python")
    assert any("không ghi CV thành tệp dự án" in item.value and "không gửi tới API" in item.value for item in app.caption)
    assert any("không được lưu để khôi phục" in item.value for item in app.caption)
    assert any("không là xác suất tuyển dụng" in item.value or "không phải" in item.value for item in app.caption)

    app.button(key="start_interview_data_analyst").click().run()
    question = app.session_state["interview_session"]["questions"][0]
    answer_field = _field(app, "Câu trả lời của bạn")
    _click(app, "Gửi câu trả lời")
    assert not app.exception
    assert app.session_state["interview_session"]["answered_ids"] == []
    assert any("nhập câu trả lời trước" in item.value for item in app.warning)

    answer_field = _field(app, "Câu trả lời của bạn")
    answer_field.input("Synthetic answer for QA")
    _click(app, "Gửi câu trả lời")
    assert question["id"] in app.session_state["interview_session"]["answered_ids"]
    copy = "\n".join(item.value for item in [*app.markdown, *app.caption])
    assert "Hệ thống không phân tích nội dung" in copy
    assert "không chấm điểm câu trả lời" in copy
    assert "Điểm phủ khái niệm" not in copy


def test_partial_or_missing_learning_material_is_explicitly_reported():
    profile = build_profile_from_cv({}, "Python, SQL")
    assert profile["skills"]
    # A role match with missing skills should resolve into a roadmap object;
    # unresolved/partial coverage is represented explicitly rather than an
    # empty success state. Resource data remains local and source attributed.
    role = next(role for role in load_roles() if role["id"] == "data_analyst")
    presence = match_role(["python"], role)
    import app as app_module

    roadmap = build_roadmap(presence["missing"], app_module.load_resources(),
                            missing_details=presence["missing_details"])
    assert roadmap
    assert all("skills_without_resources" in week for week in roadmap)


def test_keyboard_facing_widget_names_exist_but_real_browser_a11y_is_not_claimed():
    app = _start()
    labels = {item.label for item in app.text_area} | {item.label for item in app.selectbox} | {
        item.label for item in app.button
    }
    assert "Kỹ năng bạn muốn đưa vào hồ sơ (*)" in labels
    assert "Tiếp tục rà soát hồ sơ" in labels
    assert "Vị trí công việc bạn quan tâm" in labels
