import pytest

from modules.matcher import calculate_match_score


@pytest.mark.parametrize("skill", ["R", "C#", "C++"])
def test_keeps_short_and_symbolic_skill_tokens(skill):
    assert calculate_match_score(f"Experienced in {skill}", f"Need {skill}") > 0


def test_empty_cv_raises_instead_of_returning_zero():
    with pytest.raises(ValueError, match="CV không có nội dung"):
        calculate_match_score("", "Need Python developer")


def test_empty_job_description_raises():
    with pytest.raises(ValueError, match="Mô tả công việc đang trống"):
        calculate_match_score("Python developer", "")


def test_text_without_valid_tokens_raises():
    with pytest.raises(ValueError, match="CV không có từ hoặc kỹ năng hợp lệ"):
        calculate_match_score("!!!", "Python developer")
