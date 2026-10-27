# Hợp đồng giao diện

## Luồng người dùng

1. Nhập kỹ năng hoặc tải CV PDF/DOCX; có thể chọn hồ sơ demo tổng hợp, sở thích và role.
2. Rà soát kỹ năng trích từ CV, thêm hoặc bỏ mục nhận diện sai, khai báo level 0–3 rồi xác nhận hồ sơ.
3. Xem năm tab **Tóm tắt**, **Khoảng cách**, **Lộ trình**, **Tài liệu**, **Phỏng vấn**; tải báo cáo Markdown/CSV/JSON khi cần.

Hồ sơ không bắt buộc chọn role ngay. CV không tự suy ra level. Khi người dùng quay lại sửa, bản nháp lỗi không ghi đè kết quả đã xác nhận. Nội dung CV không được đưa vào báo cáo tải xuống.

## API lõi

| Hàm | Input | Output |
| --- | --- | --- |
| `parse_document` | PDF/DOCX hoặc luồng upload | text, metadata, `error_code`/message |
| `build_profile`, `prepare_submission` | form, CV text | profile và trạng thái hợp lệ |
| `match_role`, `compute_gap`, `suggest_roles` | profile, role catalog | presence, gap, gợi ý |
| `match_cv_to_jd` | CV text, JD text | kỹ năng khớp/thiếu |
| `build_roadmap`, `build_timed_roadmap` | gap, học liệu, giờ/tuần | roadmap và phần chưa giải quyết |
| `get_questions`, `get_question_feedback` | role, câu hỏi | câu hỏi và khung tự rà soát |
| `export_report` | profile, gap, roadmap | Markdown, CSV hoặc JSON |

`modules/schemas.py` có `UserProfile`, `RoleRequirement`, `GapAnalysisResult`, `InterviewFeedback`. Các model cho phép metadata bổ sung nhưng kiểm tra những trường cốt lõi; API hiện tại vẫn trả dictionary để tương thích UI.

## Giới hạn giao diện

Điểm presence, gap theo level và điểm gợi ý role là ba phép tính khác nhau. JD chỉ được tự phân nhóm khi có tiêu đề rõ; người dùng xác nhận lại. Tài liệu và câu hỏi có nhãn review/bằng chứng; URL còn hoạt động không chứng nhận nội dung hoặc quyền sử dụng. Không có điểm tự động cho câu trả lời phỏng vấn.
