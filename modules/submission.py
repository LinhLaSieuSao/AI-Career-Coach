"""Validate a form/CV submission before committing UI state."""

from __future__ import annotations

from .cv_parser import parse_document
from .matcher import match_cv_to_jd
from .profile import build_profile, build_profile_from_cv


SUBMISSION_REQUIRED_INPUT_MESSAGE = (
    "Bắt buộc có ít nhất một kỹ năng hoặc một CV hợp lệ để tạo hồ sơ. "
    "Sở thích và kinh nghiệm là thông tin bổ trợ."
)
PROFILE_REVIEW_REQUIRED_SKILL_MESSAGE = (
    "Hãy giữ lại hoặc thêm ít nhất một kỹ năng trước khi xác nhận hồ sơ. "
    "Nếu CV chưa nhận diện được kỹ năng, hãy nhập kỹ năng thủ công để tiếp tục."
)


def validate_submission_input(skills: list[str], cv_present: bool) -> tuple[bool, str]:
    """Share the profile eligibility rule between form UI and submission logic."""
    if not isinstance(skills, list):
        raise TypeError("skills phải là list các chuỗi.")
    if any(not isinstance(skill, str) for skill in skills):
        raise TypeError("Mỗi kỹ năng phải là chuỗi.")
    if type(cv_present) is not bool:
        raise TypeError("cv_present phải là bool.")
    has_skill = any(skill.strip() for skill in skills)
    if has_skill or cv_present:
        return True, ""
    return False, SUBMISSION_REQUIRED_INPUT_MESSAGE


def prepare_submission(
    form_data: dict,
    source=None,
    *,
    filename=None,
    jd_text: str = "",
    pasted_cv_text: str = "",
) -> dict:
    """Return a candidate result; rejected submissions never replace saved state.

    Nonempty skill claims or a readable, nonempty CV permit a profile. Parser
    and JD comparison errors remain separate from profile eligibility: a bad CV
    cannot erase valid manual skills. No role is required to build a profile.
    """
    document = parse_document(source, filename)
    pasted_cv_text = pasted_cv_text if isinstance(pasted_cv_text, str) else ""
    valid_document = document["error_code"] is None
    valid_pasted_cv = bool(pasted_cv_text.strip())
    cv_text_parts = []
    if valid_document:
        cv_text_parts.append(document["text"])
    if valid_pasted_cv:
        cv_text_parts.append(pasted_cv_text.strip())
    cv_text = "\n".join(part for part in cv_text_parts if part)
    valid_cv = valid_document or valid_pasted_cv
    try:
        profile = build_profile_from_cv(form_data, cv_text, include_source_metadata=True)
    except (TypeError, ValueError) as exc:
        return {"accepted": False, "profile": None, "document": document,
                "cv_extraction": None, "cv_jd_result": None, "original_interests": [],
                "errors": [str(exc)]}
    errors = []
    if document["error_code"] not in (None, "NO_FILE"):
        errors.append(document["message"])
    if jd_text.strip() and not valid_cv:
        errors.append("Hãy tải lên CV có văn bản hợp lệ để đối chiếu với mô tả công việc.")
    accepted, eligibility_message = validate_submission_input(profile["skills"], valid_cv)
    if not accepted and eligibility_message not in errors:
        errors.append(eligibility_message)
    comparison = None
    if valid_cv and jd_text.strip():
        try:
            comparison = match_cv_to_jd(cv_text, jd_text)
        except ValueError as exc:
            errors.append(str(exc))
    return {
        "accepted": accepted,
        "profile": profile if accepted else None,
        "document": document,
        "cv_extraction": {
            "filename": filename or getattr(source, "name", None) or ("CV đã nhập tay" if valid_pasted_cv else "CV"),
            "text": cv_text,
        } if valid_cv else None,
        "cv_jd_result": comparison,
        "original_interests": build_profile({"interests": form_data.get("interests")})["interests"],
        "errors": errors,
    }
