# Nghiệm thu Bước 2 — ba câu Sales template

Ngày kiểm tra: 2026-10-26. Phạm vi: `sales_executive_q02`, `q04`, `q05` trong `Data/interview_question/part_06_sales_customer_ecommerce.json`.

Ba câu đã có bối cảnh giả lập cụ thể, câu hỏi, rubric L1–L3, red flags và đáp án tham khảo. Chúng được gắn `quality=unreviewed`, `review_tier=ai_assisted_draft`; người và ngày duyệt vẫn `null`. Không có xác nhận của chuyên gia.

| Chỉ số | Trước | Sau |
| --- | ---: | ---: |
| Tổng số câu | 752 | 752 |
| Template | 3 | 0 |
| Chưa review | 727 | 730 |
| Câu demo thiếu bối cảnh/rubric | 25 | 22 |
| Câu demo có prompt chung chung | 12 | 10 |
| Cặp nghề–kỹ năng demo thiếu câu | 14 | 14 |

Script `scripts/rewrite_sales_templates.py` mặc định dry run, đã ghi bản sao của file gốc vào `dist/data-backups/step2-sales/df4d7d3de818aaecc11bc18e6fb0c66d7ae3f4d5fbbe7dcc08c1407d61f0c154/part_06_sales_customer_ecommerce.json`. Dry run báo 3 bản ghi; apply báo 3; chạy apply lại báo 0. `validate_question_bank.py` pass: 752 câu, không có lỗi cấu trúc. Nhóm test liên quan: 55 passed, 4 xfailed. Cổng strict demo vẫn chưa đạt vì còn việc biên tập câu hỏi và học liệu.

Các tình huống và con số là giả lập để luyện trả lời, không phải dữ kiện tuyển dụng hay cam kết dịch vụ thật.
