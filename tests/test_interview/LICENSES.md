# LICENSES — Module phỏng vấn

Cập nhật ngày 2026-10-23. Tệp này kiểm kê các dependency trực tiếp của `modules/interview.py` và `tests/test_interview.py`, cùng tình trạng giấy phép của ngân hàng `data/interview_question/*.json`. Đây không phải giấy phép của toàn bộ dự án.

## Thành phần liên quan

| Thành phần | Giấy phép | Dùng ở đâu | Ghi chú |
|---|---|---|---|
| Python 3.10+ và thư viện chuẩn | Python Software Foundation License Version 2 (PSF-2.0) | Runtime của `modules/interview.py`; module dùng `json`, `logging`, `random`, `copy`, `functools`, `pathlib` và `typing` | Không cần cài thư viện bên thứ ba để chạy module. Một số thành phần được phân phối kèm Python có thể có giấy phép riêng; xem tài liệu Python chính thức. |
| pytest | MIT | Chạy `tests/test_interview.py` | Chỉ là dependency phát triển/kiểm thử, không được import bởi module lúc chạy. Repo hiện chưa có file manifest dependency ở gốc. |
| Ngân hàng câu hỏi và `reference_answer` | Chưa được khai báo | 10 tệp JSON trong `data/interview_question/` | Cần nhóm xác nhận ai tạo/đóng góp nội dung và chọn/ghi rõ giấy phép dữ liệu trước khi phân phối ra ngoài. Không tự suy ra license từ việc các tệp nằm trong repo. |
| Mã nguồn AI Career Coach | Chưa thấy file `LICENSE` ở gốc repo | `modules/interview.py`, `tests/test_interview.py` và các tệp dự án khác | Nhóm cần chọn và thêm license cho dự án; bảng này không cấp license cho mã nguồn. |

## Phạm vi kiểm kê

- `modules/interview.py` hiện chỉ dùng thư viện chuẩn Python để nạp/chọn câu hỏi và trả đáp án tham khảo theo ID.
- PhoGPT và Ollama không được module hiện tại gọi hoặc đóng gói; chúng không phải dependency runtime của hướng triển khai này.
- `pytest` là dependency trực tiếp của test. Các dependency bắc cầu của pytest chưa được liệt kê riêng; cần kiểm kê lại môi trường phát hành nếu cần danh sách đầy đủ.
- Dữ liệu hiện có 10 tệp JSON, 752 câu hỏi và đáp án tham khảo. Bảng này chưa xác định nguồn gốc, quyền sở hữu hoặc license cho phần nội dung đó.

## Nguồn chính thức

- Python Software Foundation License Version 2: <https://docs.python.org/3/license.html>
- pytest (MIT): <https://github.com/pytest-dev/pytest>
