# Đóng góp

## Thiết lập

Tạo Python 3.12 virtual environment và cài dev requirements theo README. Chạy toàn bộ pytest trước khi gửi thay đổi:

```bash
python -m pytest --cov=app --cov=modules --cov-report=term-missing
```

## Quy tắc dữ liệu

- Giữ `Data/` đúng casing và dùng loader chung.
- Không ánh xạ alias giữa hai công nghệ khác nhau chỉ để tăng số lần match.
- Không suy level ứng viên từ CV; không tạo duration hoặc nguồn giả.
- Chỉ đánh dấu nội dung `reviewed` khi đã đọc phần liên quan và ghi căn cứ.
- Dùng CV/profile tổng hợp trong test. Không thêm dữ liệu cá nhân.
- Không đưa câu trả lời, rubric riêng hoặc review note private vào payload câu hỏi công khai.

## Thay đổi hợp đồng

Giữ API cũ trong `docs/interface.md`; cập nhật tài liệu và regression test khi bổ sung API. Test không được dựa vào Internet hoặc liên kết đang sống. Không giảm assertion để biến lỗi dữ liệu thành pass.

## Pull request

Mô tả hành vi trước/sau, lệnh test và giới hạn kiểm chứng. Báo rõ nếu UI chưa được kiểm tra trên browser hoặc dữ liệu chưa có provenance/license xác nhận.
