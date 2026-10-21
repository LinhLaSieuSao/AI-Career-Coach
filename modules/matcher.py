"""Text similarity helpers for matching a CV with a job description."""

from __future__ import annotations

import sys

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ModuleNotFoundError as exc:
    if exc.name != "sklearn" and not (exc.name or "").startswith("sklearn."):
        raise
    raise ImportError(
        "scikit-learn is not installed for the active Python interpreter "
        f"({sys.executable}). Install this project's dependencies with "
        f'"{sys.executable}" -m pip install -r requirements.txt.'
    ) from exc


# Keep single-letter skills and names such as R, C#, and C++ as tokens.
_TOKEN_PATTERN = r"(?u)[\w#+]+"


def calculate_match_score(cv_text: str, job_description: str) -> float:
    """Return lexical similarity between CV and job text on a 0–100 scale.

    Raises:
        ValueError: if either text is empty or contains no tokens accepted by
            the vectorizer. This avoids presenting missing input as a real 0%.
    """
    cv_text = (cv_text or "").strip()
    job_description = (job_description or "").strip()

    if not cv_text:
        raise ValueError("CV không có nội dung văn bản. Có thể file là PDF scan.")
    if not job_description:
        raise ValueError("Mô tả công việc đang trống.")

    vectorizer = TfidfVectorizer(token_pattern=_TOKEN_PATTERN)
    analyzer = vectorizer.build_analyzer()
    if not analyzer(cv_text):
        raise ValueError("CV không có từ hoặc kỹ năng hợp lệ để so khớp.")
    if not analyzer(job_description):
        raise ValueError("Mô tả công việc không có từ hợp lệ để so khớp.")

    try:
        tfidf_matrix = vectorizer.fit_transform([cv_text, job_description])
    except ValueError as exc:
        raise ValueError(f"Không tạo được vector TF-IDF: {exc}") from exc

    # Ask sklearn to compare all rows at once; the returned dense ndarray is
    # also understood by Pylance, unlike sparse-matrix slicing in some stubs.
    similarity_matrix = cosine_similarity(tfidf_matrix)
    similarity = similarity_matrix[0, 1]
    return round(float(similarity) * 100, 2)
