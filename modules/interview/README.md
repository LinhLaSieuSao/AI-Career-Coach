# AI Career Coach — Module phỏng vấn

README này mô tả phạm vi module phỏng vấn, file kiểm thử và dữ liệu câu hỏi tại `data/interview_question/`; không mô tả các chức năng khác của dự án.

## Module làm gì?

`modules/interview.py` cung cấp hai hàm để backend gọi:

```python
get_questions(role_id, n=5, seed=None) -> list[dict]
get_reference_answer(question_id) -> str
```

Luồng dự kiến:

1. User chọn vị trí. Backend truyền `role_id` tương ứng vào `get_questions()`.
2. Module nạp câu hỏi của vị trí đó và trả tối đa `n` câu. Mỗi câu trả về đã được bỏ trường `reference_answer`.
3. User tự nhập câu trả lời. Backend nhận nội dung trả lời cùng ID câu hỏi.
4. Sau khi nhận câu trả lời, backend gọi `get_reference_answer(question_id)` và gửi đáp án tham khảo về frontend để hiển thị.

Module **không** so sánh câu trả lời của user với đáp án mẫu, tính điểm, viết nhận xét, hoặc gọi PhoGPT/Ollama. Module cũng không tự xác minh user đã gửi câu trả lời; backend chịu trách nhiệm chỉ gọi `get_reference_answer()` sau khi nhận bài gửi.

`get_questions()` ném `ValueError` nếu `n` không dương hoặc không tìm thấy role. `get_reference_answer()` trả về chuỗi đáp án tham khảo và ném `ValueError` nếu ID rỗng, không tồn tại, bị trùng, hoặc chưa có đáp án mẫu hợp lệ.

## Dữ liệu câu hỏi

Ngân hàng hiện có 10 tệp JSON, 752 câu hỏi và 131 mã vị trí. Mỗi câu giữ các trường sẵn có và có thêm `reference_answer`, ví dụ:

```json
{
  "id": "backend_java_001",
  "type": "technical",
  "skill": "java",
  "question": "Bạn sẽ xử lý lỗi API như thế nào?",
  "good_answer_points": ["..."],
  "reference_answer": "Một câu trả lời mẫu cho câu hỏi này."
}
```

Module ưu tiên đọc `data/interview_questions/`; nếu thư mục đó không tồn tại, nó hỗ trợ tên thư mục hiện có `data/interview_question/`. Module quét mọi tệp `*.json` theo thứ tự tên. Nếu một `role_id` xuất hiện ở nhiều tệp, module ghi log và giữ dữ liệu được đọc trước. ID câu hỏi cần duy nhất trong toàn bộ ngân hàng vì `get_reference_answer()` tra cứu theo ID.

Đáp án mẫu là gợi ý, không phải câu trả lời duy nhất được chấp nhận. Nhóm nên nhờ người có chuyên môn kiểm tra độ chính xác và phù hợp trước khi dùng với người dùng.

## Chạy kiểm thử

Cần Python 3.10 trở lên. Module chỉ dùng thư viện chuẩn Python. Khi phát triển, cài pytest để chạy test:

```powershell
python -m pip install pytest
python -m pytest tests/test_interview.py -v
```

Lần chạy gần nhất tại workspace ngày 2026-10-23 có **15 test pass**. Test kiểm tra việc nạp dữ liệu, chọn câu hỏi, ẩn/lấy đáp án, các trường hợp lỗi và ngân hàng câu hỏi thật. Test không gọi web server hay model bên ngoài.

## Tự chạy thử với dữ liệu thật

Mở PowerShell tại thư mục gốc dự án rồi chạy đoạn sau. Lệnh chọn một câu thật, nhận câu trả lời nhập tay, sau đó hiển thị đáp án mẫu. Nó không chấm điểm và không so sánh câu trả lời.

```powershell
$env:PYTHONIOENCODING = "utf-8"
@'
from modules.interview import get_questions, get_reference_answer

role_id = "backend_developer_java"
questions = get_questions(role_id, n=5, seed=42)
question = questions[0]

print("Câu hỏi:", question["question"])
assert "reference_answer" not in question
user_answer = input("Nhập câu trả lời rồi nhấn Enter: ")
print(f"Đã nhận {len(user_answer)} ký tự.")

# Chỉ gọi sau khi backend đã nhận câu trả lời của user.
print()
print("Đáp án tham khảo:")
print(get_reference_answer(question["id"]))
'@ | python -
```

Có thể đổi `role_id` thành một mã khác trong `data/roles.json` để thử vị trí khác.

## Phần tích hợp của nhóm

Ứng dụng backend/frontend nằm ngoài phạm vi module này. Backend nên chỉ gửi các trường câu hỏi cần thiết cho frontend, nhận câu trả lời của user, rồi mới gọi `get_reference_answer()`. Không gửi đáp án mẫu kèm response lấy câu hỏi ban đầu. Frontend hiển thị đáp án mẫu sau khi backend trả về.

## Giấy phép

Xem [LICENSES.md](LICENSES.md) để biết dependency runtime/test trực tiếp và trạng thái giấy phép của dữ liệu câu hỏi cùng mã nguồn dự án.
