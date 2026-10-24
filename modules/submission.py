"""Validate a form/CV submission before committing UI state."""

from __future__ import annotations

from .cv_parser import parse_document
from .matcher import match_cv_to_jd
from .profile import build_profile, build_profile_from_cv


def prepare_submission(form_data: dict, source=None, *, filename=None, jd_text: str = "") -> dict:
    """Return a candidate result; rejected submissions never replace saved state.

    Nonempty skill claims or a readable, nonempty CV permit a profile. Parser
    and JD comparison errors remain separate from profile eligibility: a bad CV
    cannot erase valid manual skills. No role is required to build a profile.
    """
    document = parse_document(source, filename)
    valid_cv = document["error_code"] is None
    try:
        profile = build_profile_from_cv(form_data, document["text"] if valid_cv else "")
    except (TypeError, ValueError) as exc:
        return {"accepted": False, "profile": None, "document": document,
                "cv_extraction": None, "cv_jd_result": None, "original_interests": [],
                "errors": [str(exc)]}
    errors = []
    if document["error_code"] not in (None, "NO_FILE") or source is not None and not valid_cv:
        errors.append(document["message"])
    if jd_text.strip() and not valid_cv:
        errors.append("Hãy tải lên CV có văn bản hợp lệ để đối chiếu với mô tả công việc.")
    accepted = bool(profile["skills"]) or valid_cv
    if not accepted and not errors:
        errors.append("Hãy nhập ít nhất một kỹ năng hoặc tải lên CV hợp lệ để tạo hồ sơ.")
    comparison = None
    if valid_cv and jd_text.strip():
        try:
            comparison = match_cv_to_jd(document["text"], jd_text)
        except ValueError as exc:
            errors.append(str(exc))
    return {
        "accepted": accepted,
        "profile": profile if accepted else None,
        "document": document,
        "cv_extraction": {"filename": filename or getattr(source, "name", "CV"), "text": document["text"]} if valid_cv else None,
        "cv_jd_result": comparison,
        "original_interests": build_profile({"interests": form_data.get("interests")})["interests"],
        "errors": errors,
    }
