from modules.interview import generate_interview_questions


def test_questions_are_loaded_for_role_in_updated_data_format():
    questions = generate_interview_questions([], role="Data Analyst")
    assert len(questions) == 2
    assert all(isinstance(question, str) and question for question in questions)


def test_questions_can_be_matched_by_missing_skill_keywords():
    questions = generate_interview_questions(["SQL"])
    assert questions
    assert any("JOIN" in question for question in questions)
