"""Application modules with lazy public imports.

Importing one module (for example ``modules.matcher``) should not eagerly load
unrelated PDF, interview, or recommender dependencies.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    "extract_text_from_pdf": ("cv_parser", "extract_text_from_pdf"),
    "extract_text": ("cv_parser", "extract_text"),
    "build_profile": ("profile", "build_profile"),
    "match_role": ("matcher", "match_role"),
    "match_cv_to_jd": ("matcher", "match_cv_to_jd"),
    "build_roadmap": ("recommender", "build_roadmap"),
    "get_course_recommendations": ("recommender", "get_course_recommendations"),
    "generate_interview_questions": ("interview", "generate_interview_questions"),
    "get_questions": ("interview", "get_questions"),
    "get_reference_answer": ("interview", "get_reference_answer"),
    "get_question_feedback": ("interview", "get_question_feedback"),
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
