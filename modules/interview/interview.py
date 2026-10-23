"""Chọn câu hỏi phỏng vấn và lấy đáp án tham khảo khi được yêu cầu."""

from __future__ import annotations

import json
import logging
import random
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Các đường dẫn tính từ thư mục gốc dự án, không phụ thuộc thư mục chạy.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _PROJECT_ROOT / "data" / "interview_questions"
_SINGLE_FILE = _PROJECT_ROOT / "data" / "interview_questions.json"
# Tương thích với bộ dữ liệu hiện có trong workspace (tên thư mục số ít).
_LEGACY_DATA_DIR = _PROJECT_ROOT / "data" / "interview_question"


@lru_cache(maxsize=1)
def _load_question_data() -> dict[str, list[dict[str, Any]]]:
    """Đọc và gộp dữ liệu câu hỏi; file lỗi được ghi log và bỏ qua."""
    if _DATA_DIR.is_dir():
        data_dir = _DATA_DIR
    elif _LEGACY_DATA_DIR.is_dir():
        data_dir = _LEGACY_DATA_DIR
    else:
        data_dir = None

    merged: dict[str, list[dict[str, Any]]] = {}
    if data_dir is not None:
        files = sorted(data_dir.glob("*.json"), key=lambda path: path.name)
        for path in files:
            try:
                with path.open("r", encoding="utf-8") as source:
                    payload = json.load(source)
                roles = payload.get("roles")
                if not isinstance(roles, dict):
                    raise ValueError("thiếu object 'roles'")
                for role_id, questions in roles.items():
                    if role_id in merged:
                        logger.warning(
                            "role_id %s bị trùng trong %s; giữ dữ liệu đã đọc trước",
                            role_id,
                            path.name,
                        )
                        continue
                    if isinstance(questions, list):
                        merged[role_id] = questions
                    else:
                        logger.warning(
                            "Danh sách câu hỏi của %s không hợp lệ trong %s",
                            role_id,
                            path.name,
                        )
            except (OSError, json.JSONDecodeError, ValueError, AttributeError) as exc:
                logger.error("Không đọc được dữ liệu câu hỏi %s: %s", path, exc)
    elif _SINGLE_FILE.is_file():
        try:
            with _SINGLE_FILE.open("r", encoding="utf-8") as source:
                payload = json.load(source)
            roles = payload.get("roles")
            if isinstance(roles, dict):
                merged.update(
                    {
                        key: value
                        for key, value in roles.items()
                        if isinstance(value, list)
                    }
                )
            else:
                logger.error("File %s thiếu object 'roles'", _SINGLE_FILE)
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            logger.error("Không đọc được dữ liệu câu hỏi %s: %s", _SINGLE_FILE, exc)
    else:
        logger.error("Không tìm thấy thư mục hoặc file dữ liệu câu hỏi")
    return merged


def _clear_cache() -> None:
    """Xóa cache dữ liệu, chủ yếu phục vụ kiểm thử và nạp lại dữ liệu."""
    _load_question_data.cache_clear()


def get_questions(role_id: str, n: int = 5, seed: int | None = None) -> list[dict]:
    """Lấy tối đa n câu hỏi của vị trí và ẩn đáp án tham khảo khỏi kết quả."""
    if n <= 0:
        raise ValueError("Số câu hỏi phải lớn hơn 0.")

    roles = _load_question_data()
    if role_id not in roles:
        if not roles:
            raise ValueError(
                "Không có dữ liệu câu hỏi; hãy kiểm tra thư mục "
                "data/interview_questions/."
            )
        raise ValueError(f"Không tìm thấy câu hỏi cho vị trí '{role_id}'.")

    questions = roles[role_id]
    rng = random.Random(seed)
    by_type: dict[str, list[dict[str, Any]]] = {"technical": [], "scenario": []}
    for question in questions:
        kind = question.get("type")
        if kind in by_type:
            by_type[kind].append(question)
    for group in by_type.values():
        rng.shuffle(group)

    # Bắt đầu bằng loại có mặt đầu tiên trong dữ liệu; sau đó luân phiên.
    first_type = next(
        (q.get("type") for q in questions if q.get("type") in by_type), "technical"
    )
    order = [first_type, "scenario" if first_type == "technical" else "technical"]
    selected: list[dict[str, Any]] = []
    seen_ids: set[Any] = set()
    while len(selected) < min(n, len(questions)):
        progressed = False
        for kind in order:
            while by_type[kind]:
                question = by_type[kind].pop()
                question_id = question.get("id")
                if question_id in seen_ids:
                    continue
                seen_ids.add(question_id)
                public_question = deepcopy(question)
                public_question.pop("reference_answer", None)
                selected.append({**public_question, "role_id": role_id})
                progressed = True
                break
            if len(selected) >= n:
                break
        if not progressed:
            break
    return selected


def get_reference_answer(question_id: str) -> str:
    """Lấy đáp án mẫu theo ID để backend trả sau khi user đã trả lời."""
    if not isinstance(question_id, str) or not question_id.strip():
        raise ValueError("question_id phải là chuỗi không rỗng.")

    matches = [
        question
        for questions in _load_question_data().values()
        for question in questions
        if question.get("id") == question_id
    ]
    if not matches:
        raise ValueError(f"Không tìm thấy câu hỏi có ID '{question_id}'.")
    if len(matches) > 1:
        raise ValueError(f"ID câu hỏi '{question_id}' bị trùng trong ngân hàng dữ liệu.")

    reference_answer = matches[0].get("reference_answer")
    if not isinstance(reference_answer, str) or not reference_answer.strip():
        raise ValueError(f"Câu hỏi '{question_id}' chưa có đáp án tham khảo.")
    return reference_answer.strip()
