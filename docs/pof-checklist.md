# Checklist Proof of Functionality (local)

Tài liệu yêu cầu ban đầu thiếu rubric PoF tham chiếu, nên checklist này là bằng chứng kỹ thuật local, không tự tuyên bố hoàn thành rubric bên ngoài.

| Tiêu chí kiểm tra | Bằng chứng trong repo | Trạng thái local | Còn cần |
| --- | --- | --- | --- |
| Cài và chạy app | README, `app.py`, AppTest | Đã qua AppTest | Cài sạch và browser UI |
| Luồng CV/kỹ năng đến Matcher | `tests/test_app.py`, `modules/submission.py` | Đã có regression | Kiểm thử browser upload trước/sau |
| Level/timed roadmap | `tests/test_assessment.py`, `tests/test_timed_roadmap.py` | Logic có fixture | Nguồn duration/level còn thiếu |
| Role suggestions | `tests/test_assessment.py` | Heuristic local, không mạng | Đánh giá chất lượng với người dùng |
| Interview | `tests/test_interview_assessment.py` | 6 rubric review nội bộ; phần còn lại unavailable | Review độc lập rộng hơn |
| Export | `tests/test_export.py` | Markdown/CSV, Unicode, formula escaping | Mở thử bằng spreadsheet GUI |
| Docker | Dockerfile và CI workflow | CI được cấu hình | Docker CLI chưa có trong máy local |
| Desktop/mobile layout | `assets/style.css` | Chưa kiểm tra trực quan | Browser có quyền origin và viewport thực |
| Accessibility | HTML/CSS và Streamlit controls | Chưa audit đầy đủ | Kiểm tra keyboard/screen reader |
| License/provenance | `LICENSES.md` | Một phần đã kiểm kê | Nhóm xác nhận quyền dữ liệu/brand/owner |
| Release | `CHANGELOG.md`, release notes local | Tài liệu đã chuẩn bị | Người dùng duyệt version, license, assets, CI và phát hành |

## Trước khi tạo release thật

- Xác nhận rubric PoF có thẩm quyền và owner dự án.
- Đóng các mục license/provenance còn mở trong `LICENSES.md`.
- Chạy GitHub Actions và Docker build/healthcheck.
- Chụp screenshot desktop/mobile và kiểm tra uploader trên browser được phép.
- Review release notes, chọn số phiên bản và thực hiện tag/publish theo quyết định riêng của maintainer.
