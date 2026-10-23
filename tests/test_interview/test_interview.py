"""Kiểm thử module phỏng vấn, không gọi mạng hay dịch vụ bên ngoài."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from modules import interview


def _question(
    question_id: str,
    kind: str,
    skill: str = "sql",
    reference_answer: str | None = None,
) -> dict:
    """Tạo câu hỏi mẫu tối thiểu theo cấu trúc dữ liệu dự án."""
    return {
        "id": question_id,
        "type": kind,
        "skill": skill,
        "level": 2,
        "weight": 2,
        "question": "Hãy mô tả cách bạn xử lý tình huống.",
        "good_answer_points": [
            "Nêu cơ chế hoặc cách áp dụng kỹ năng.",
            "Trình bày thiết kế và cách xử lý lỗi.",
            "Nêu cách kiểm chứng kết quả.",
        ],
        "red_flags": ["Không nêu được bằng chứng kiểm chứng."],
        "time_minutes": 4,
        "reference_answer": reference_answer or f"Đáp án tham khảo cho {question_id}.",
    }


def _write_data(path: Path, roles: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"version": 1, "roles": roles}, ensure_ascii=False), encoding="utf-8"
    )


@pytest.fixture
def question_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Tạo hai phần dữ liệu, gồm vị trí thứ hai và một khóa trùng."""
    data_dir = tmp_path / "interview_questions"
    _write_data(
        data_dir / "part_01.json",
        {
            "first_role": [
                _question("t1", "technical"),
                _question("s1", "scenario"),
                _question("t2", "technical"),
            ],
            "duplicate_role": [_question("first-copy", "technical")],
        },
    )
    _write_data(
        data_dir / "part_02.json",
        {
            "second_role": [_question("second-file", "scenario")],
            "duplicate_role": [_question("second-copy", "scenario")],
        },
    )
    monkeypatch.setattr(interview, "_DATA_DIR", data_dir)
    monkeypatch.setattr(interview, "_LEGACY_DATA_DIR", tmp_path / "missing-legacy")
    monkeypatch.setattr(interview, "_SINGLE_FILE", tmp_path / "missing-single.json")
    interview._clear_cache()
    yield data_dir
    interview._clear_cache()


def test_get_questions_merges_files_and_keeps_first_duplicate(
    question_data: Path,
) -> None:
    """Vị trí file sau được nạp và khóa trùng giữ nội dung file đầu."""
    assert interview.get_questions("second_role", 5)[0]["id"] == "second-file"
    duplicate = interview.get_questions("duplicate_role", 5)
    assert [item["id"] for item in duplicate] == ["first-copy"]
    assert duplicate[0]["role_id"] == "duplicate_role"


def test_get_questions_hides_reference_answer(question_data: Path) -> None:
    question = interview.get_questions("first_role", 1, seed=10)[0]
    assert "reference_answer" not in question
    assert interview.get_reference_answer(question["id"]).startswith("Đáp án tham khảo")


def test_get_questions_limits_count_and_returns_copies(question_data: Path) -> None:
    questions = interview.get_questions("first_role", 2, seed=10)
    assert len(questions) == 2
    assert len(interview.get_questions("first_role", 99)) == 3
    assert len({item["id"] for item in questions}) == len(questions)
    assert all(item["role_id"] == "first_role" for item in questions)
    questions[0]["question"] = "đã sửa"
    questions[0]["good_answer_points"].append("thay đổi sâu")
    assert interview.get_questions("first_role", 99)[0]["question"] != "đã sửa"
    assert "thay đổi sâu" not in interview.get_questions("first_role", 99)[0][
        "good_answer_points"
    ]


def test_get_questions_is_seeded_and_alternates_types(question_data: Path) -> None:
    first = interview.get_questions("first_role", 3, seed=42)
    second = interview.get_questions("first_role", 3, seed=42)
    assert first == second
    assert {item["type"] for item in first[:2]} == {"technical", "scenario"}


@pytest.mark.parametrize("n", [0, -1])
def test_get_questions_rejects_non_positive_n(question_data: Path, n: int) -> None:
    with pytest.raises(ValueError, match="lớn hơn 0"):
        interview.get_questions("first_role", n)


def test_get_questions_unknown_role_has_clear_error(question_data: Path) -> None:
    with pytest.raises(ValueError, match="Không tìm thấy câu hỏi"):
        interview.get_questions("missing_role")


def test_empty_and_invalid_json_are_logged_and_do_not_crash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setattr(interview, "_DATA_DIR", empty)
    monkeypatch.setattr(interview, "_LEGACY_DATA_DIR", tmp_path / "missing")
    monkeypatch.setattr(interview, "_SINGLE_FILE", tmp_path / "missing.json")
    interview._clear_cache()
    with pytest.raises(ValueError, match="Không có dữ liệu"):
        interview.get_questions("any")

    (empty / "broken.json").write_text("{not json", encoding="utf-8")
    interview._clear_cache()
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError, match="Không có dữ liệu"):
            interview.get_questions("any")
    assert "Không đọc được dữ liệu" in caplog.text
    interview._clear_cache()


def test_get_reference_answer_reads_questions_across_files(question_data: Path) -> None:
    assert interview.get_reference_answer("t1") == "Đáp án tham khảo cho t1."
    assert interview.get_reference_answer("second-file") == (
        "Đáp án tham khảo cho second-file."
    )


@pytest.mark.parametrize("question_id", ["", "   "])
def test_get_reference_answer_rejects_empty_id(
    question_data: Path, question_id: str
) -> None:
    with pytest.raises(ValueError, match="question_id phải là chuỗi không rỗng"):
        interview.get_reference_answer(question_id)


def test_get_reference_answer_unknown_id_has_clear_error(question_data: Path) -> None:
    with pytest.raises(ValueError, match="Không tìm thấy câu hỏi có ID"):
        interview.get_reference_answer("missing-id")


def test_get_reference_answer_rejects_missing_answer(
    question_data: Path,
) -> None:
    payload = {
        "roles": {"role": [_question("no-answer", "technical", reference_answer=" ")]}
    }
    (interview._DATA_DIR / "part_03.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )
    interview._clear_cache()
    with pytest.raises(ValueError, match="chưa có đáp án tham khảo"):
        interview.get_reference_answer("no-answer")


def test_get_reference_answer_rejects_duplicate_question_id(
    question_data: Path,
) -> None:
    duplicate = _question("t1", "scenario")
    _write_data(question_data / "part_03.json", {"third_role": [duplicate]})
    interview._clear_cache()
    with pytest.raises(ValueError, match="bị trùng trong ngân hàng dữ liệu"):
        interview.get_reference_answer("t1")


def test_real_question_data_has_reference_answers_and_unique_ids() -> None:
    data_dir = Path(interview._PROJECT_ROOT) / "data" / "interview_questions"
    if not data_dir.is_dir():
        data_dir = interview._LEGACY_DATA_DIR
    if not data_dir.is_dir():
        pytest.skip("Không có thư mục dữ liệu câu hỏi trong workspace.")
    interview._clear_cache()
    roles = interview._load_question_data()
    assert roles
    assert len(list(data_dir.glob("*.json"))) == 10

    ids = []
    for questions in roles.values():
        for question in questions:
            ids.append(question.get("id"))
            required = {
                "id",
                "type",
                "skill",
                "question",
                "good_answer_points",
                "reference_answer",
            }
            assert required <= question.keys()
            assert str(question["reference_answer"]).strip()
    assert len(ids) == len(set(ids))
    interview._clear_cache()
