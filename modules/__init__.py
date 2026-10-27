"""Application modules with lazy public imports.

Importing one module (for example ``modules.matcher``) should not eagerly load
unrelated PDF, interview, or recommender dependencies.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    "export_report": ("export", "export_report"),
    "extract_text_from_pdf": ("cv_parser", "extract_text_from_pdf"),
    "extract_text": ("cv_parser", "extract_text"),
    "parse_document": ("cv_parser", "parse_document"),
    "build_profile": ("profile", "build_profile"),
    "build_profile_from_cv": ("profile", "build_profile_from_cv"),
    "match_role": ("matcher", "match_role"),
    "match_cv_to_jd": ("matcher", "match_cv_to_jd"),
    "extract_jd_skills": ("matcher", "extract_jd_skills"),
    "extract_jd_skill_requirements": ("matcher", "extract_jd_skill_requirements"),
    "compare_confirmed_skills_to_jd": ("matcher", "compare_confirmed_skills_to_jd"),
    "compare_confirmed_jd_requirements": ("matcher", "compare_confirmed_jd_requirements"),
    "compute_gap": ("matcher", "compute_gap"),
    "suggest_roles": ("matcher", "suggest_roles"),
    "build_timed_roadmap": ("recommender", "build_timed_roadmap"),
    "build_roadmap": ("recommender", "build_roadmap"),
    "get_course_recommendations": ("recommender", "get_course_recommendations"),
    "generate_interview_questions": ("interview", "generate_interview_questions"),
    "get_questions": ("interview", "get_questions"),
    "get_reference_answer": ("interview", "get_reference_answer"),
    "get_question_feedback": ("interview", "get_question_feedback"),
    "review_answer": ("interview", "review_answer"),
    "question_bank_quality_summary": ("interview", "question_bank_quality_summary"),
    "count_reviewed_questions": ("interview", "count_reviewed_questions"),
    "question_quality_label": ("interview", "question_quality_label"),
    "POST_SUBMISSION_GUIDANCE_NOTICE": ("interview", "POST_SUBMISSION_GUIDANCE_NOTICE"),
    "STATIC_SELF_REVIEW_TITLE": ("interview", "STATIC_SELF_REVIEW_TITLE"),
    "STATIC_SELF_REVIEW_NOTICE": ("interview", "STATIC_SELF_REVIEW_NOTICE"),
    "interest_fit": ("matcher", "interest_fit"),
    "user_interest_vector": ("matcher", "user_interest_vector"),
    "load_interest_activities": ("matcher", "load_interest_activities"),
    "validate_submission_input": ("profile", "validate_submission_input"),
    "PROFILE_REVIEW_REQUIRED_SKILL_MESSAGE": ("profile", "PROFILE_REVIEW_REQUIRED_SKILL_MESSAGE"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    """Load a public API only when the caller requests it."""
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    module = import_module(f".{module_name}", __name__)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value
