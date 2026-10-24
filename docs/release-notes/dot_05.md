# Release notes chuẩn bị review — Đợt 5

**Trạng thái:** bản nháp local, chưa phát hành, chưa có version/tag.

AI Career Coach bổ sung giao diện năm tab cho tóm tắt, khoảng cách kỹ năng, lộ trình, tài liệu và phỏng vấn. Người dùng có thể tải báo cáo Markdown hoặc CSV; xuất CSV đã escape dữ liệu đầu vào có khả năng bị bảng tính hiểu là công thức và không bao gồm toàn văn CV.

Ba hồ sơ demo là ví dụ tổng hợp cho Backend Java, Data Analyst và Sales Executive. Các điểm presence, level gap và gợi ý role được đặt tên riêng; gợi ý role không phải xác suất tuyển dụng. Rubric máy chấm chỉ có cho nhóm câu hỏi đã review, các câu khác trả unavailable.

### Giới hạn trước phát hành

- UI browser desktop/mobile và trạng thái uploader chưa được xác nhận trực quan trong phiên này.
- Tổng tuần lộ trình còn chưa xác định ở các role demo do thiếu duration, review hoặc level coverage trong catalog.
- Docker build/healthcheck chưa chạy local vì Docker CLI không có; GitHub Actions mới được cấu hình, chưa có kết quả workflow.
- Quyền phân phối lại dữ liệu role/question/resource và provenance brand cần maintainer xác nhận.
- Video, slide deck và screenshot chưa được tạo.
