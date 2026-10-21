from typing import Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_match_score(cv_text: str, job_description: str) -> float:
    """Calculate similarity between a CV and a job description.

    The function builds TF‑IDF vectors for the two input strings and returns
    the cosine similarity as a percentage (0 – 100).
    """
    # Create TF‑IDF representation for both texts.
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([cv_text, job_description])

    # Compute cosine similarity between the first (CV) and second (job) vectors.
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    # Convert to a percentage and round to two decimal places.
    return round(similarity * 100, 2)

