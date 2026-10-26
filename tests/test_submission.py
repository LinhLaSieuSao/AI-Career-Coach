"""Controller validation without Streamlit and without personal CVs."""

from io import BytesIO

import pytest

from document_fixtures import docx_bytes, pdf_bytes
from modules.submission import SUBMISSION_REQUIRED_INPUT_MESSAGE, prepare_submission


@pytest.mark.parametrize("form", [{}, {"skills": " , ; \n "}, {"skills": "interest: games"}, {"interests": "AI", "experience": "Developer"}])
def test_no_skill_or_document_rejects_empty_profile(form):
    result = prepare_submission(form)
    assert not result["accepted"]
    assert result["profile"] is None
    assert result["document"]["error_code"] == "NO_FILE"
    assert "ít nhất một kỹ năng" in result["errors"][0]


def test_jd_only_requests_cv_without_creating_profile():
    result = prepare_submission({}, jd_text="SQL")
    assert not result["accepted"]
    assert result["profile"] is None
    assert result["cv_jd_result"] is None
    assert len(result["errors"]) == 2
    assert "Hãy tải lên CV" in result["errors"][0]
    assert "ít nhất một kỹ năng hoặc một CV hợp lệ" in result["errors"][1]


@pytest.mark.parametrize("filename,content,code", [
    ("cv.pdf", b"broken", "INVALID_SIGNATURE"),
    ("cv.pdf", pdf_bytes(), "EMPTY"),
    ("cv.pdf", pdf_bytes(image=True), "SCANNED_PDF"),
    ("cv.docx", docx_bytes(), "EMPTY"),
    ("cv.txt", b"Python", "UNSUPPORTED_FORMAT"),
], ids=["broken", "blank-pdf", "image-pdf", "empty-docx", "unsupported"])
def test_invalid_upload_cannot_create_profile_but_manual_claims_remain_usable(filename, content, code):
    for form, accepted in [({}, False), ({"skills": "Python; Custom"}, True)]:
        result = prepare_submission(form, BytesIO(content), filename=filename)
        assert result["accepted"] is accepted
        assert result["document"]["error_code"] == code
        assert result["cv_extraction"] is None
        if accepted:
            assert result["errors"] == [result["document"]["message"]]
        else:
            assert result["errors"] == [
                result["document"]["message"],
                SUBMISSION_REQUIRED_INPUT_MESSAGE,
            ]
        if accepted:
            assert result["profile"]["skills"] == ["custom", "python"]
            assert result["profile"]["unrecognized_skills"] == ["custom"]


def test_valid_cv_and_jd_are_independent_of_manual_claims_and_role():
    result = prepare_submission({"skills": "SQL; Custom"}, BytesIO(docx_bytes("Python")), filename="cv.docx", jd_text="Python SQL")
    assert result["accepted"]
    assert result["errors"] == []
    assert result["profile"]["skills"] == ["custom", "python", "sql"]
    assert result["cv_jd_result"]["percent"] == 50.0
    assert result["cv_jd_result"]["missing"] == ["sql"]


def test_valid_document_without_catalog_skills_can_be_saved_without_fabricating_skills():
    result = prepare_submission({}, BytesIO(docx_bytes("No catalog terms here")), filename="cv.docx")
    assert result["accepted"]
    assert result["profile"]["skills"] == []
    assert result["profile"]["unrecognized_skills"] == []
