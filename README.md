# AI Career Coach

AI Career Coach là ứng dụng Streamlit mã nguồn mở giúp tạo hồ sơ kỹ năng, đối chiếu với role trong catalog, xem khoảng cách kỹ năng, tìm tài liệu và luyện phỏng vấn. Các phép tính trong bản hiện tại dùng quy tắc tường minh; không gọi LLM, embedding hoặc dịch vụ trả phí.

Ứng dụng phân biệt điểm presence theo kỹ năng nhận diện, gap theo level do người dùng tự khai báo và điểm heuristic gợi ý role. Không điểm nào là xác suất tuyển dụng. Luồng hồ sơ có hai bước để rà soát kỹ năng và Level trước khi xem kết quả. PDF scan chưa được OCR; CV bị giới hạn 10 MiB và PDF chỉ đọc 10 trang đầu. Phỏng vấn không tự chấm điểm hoặc phân tích câu trả lời: sau khi người dùng gửi, app hiển thị hướng dẫn tham khảo và checklist tĩnh để người dùng tự đối chiếu. Ngân hàng hiện có 766 câu: 0 template, 766 câu đang chờ duyệt lại sau khi bổ sung 14 câu và rubric cho bốn nghề demo. Metadata review trước được lưu trong lịch sử từng câu bị sửa; rubric mới do AI biên soạn chưa qua duyệt chuyên môn. Kỹ năng mềm có thể luyện qua tình huống thực tế/role-play và phản hồi, không bắt buộc phải có khóa học cho mọi kỹ năng.

## Chạy local

Cần Python 3.12. Tạo môi trường ảo và cài runtime:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.lock
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Trên macOS/Linux:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
.venv/bin/python -m streamlit run app.py
```

Mở địa chỉ local do Streamlit in ra, thường là `http://localhost:8501`. Dữ liệu được nạp từ thư mục `Data/` cạnh mã nguồn; app không gửi CV tới API bên ngoài. Hồ sơ và nội dung CV ở trong phiên Streamlit hiện tại, không có tính năng lưu/khôi phục: tải lại trang có thể làm mất kết quả. Trên máy dùng chung, hãy đóng tab và dừng tiến trình sau khi sử dụng. Bản cloud cần đánh giá lại privacy trước khi bật upload.

## Chạy test

Cài bộ phát triển riêng (nó bao gồm runtime):

```powershell
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pytest --cov=app --cov=modules --cov-report=term-missing
```

`tests/` dùng fixture PDF/DOCX tổng hợp. Bài kiểm tra không cần truy cập link tài liệu; script kiểm tra liên kết là công cụ dev riêng.

Kiểm thử giao diện bằng Chromium, gồm luồng bàn phím, bố cục, liên kết và axe:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m pytest -q browser_tests
```

CI cài Chromium và chạy bộ browser riêng; nếu Chromium không khởi động được, CI báo lỗi thay vì bỏ qua bài test.

Chạy kiểm tra nhanh các hàm lõi không cần mở giao diện:

```powershell
.\.venv\Scripts\python.exe scripts\smoke.py
.\.venv\Scripts\python.exe tests\test_recommendation_quality.py
.\.venv\Scripts\python.exe scripts\validate_question_bank.py
```

`requirements.lock` là bộ phiên bản runtime được phân giải có hash cho Python 3.12. CI/test dùng `requirements-dev.lock` gồm cả runtime và công cụ kiểm thử. [Hướng dẫn cài sạch](docs/verification/clean-install.md) ghi các lệnh cài đặt tái lập.

Schema bằng chứng 2.0 được mô tả trong [hợp đồng dữ liệu](docs/verification/schema-contract-v2.md). Chạy `python scripts/validate_evidence_schema.py` để kiểm tra cấu trúc Role–Skill–Level; cổng đầy đủ `--require-complete-evidence` hiện còn pending vì thiếu dẫn chứng nội dung, provenance và review độc lập. Xem [tiến độ căn chỉnh và các khoảng trống theo bốn nghề demo](docs/verification/constructive-alignment-progress-2026-10-26.md) trước khi diễn giải các tỷ lệ coverage như bằng chứng đã xác minh.

Cổng biên tập riêng cho bốn nghề demo: `python scripts/audit_demo_role_quality.py --strict` hoặc `python -m pytest tests/test_demo_role_quality.py --runxfail`. Các lệnh nghiêm ngặt hiện trả lỗi đúng những thiếu hụt đã ghi; test thường hiển thị bốn `xfail`, không phải bốn role đã đạt. [Báo cáo Bước 1](docs/verification/demo-role-quality-gate-2026-10-26.md) liệt kê từng nhóm lỗi và cách so sánh trước/sau khi sửa.

[Bàn giao sửa dữ liệu và logic trước giai đoạn giao diện](docs/verification/remediation-handoff-2026-10-26.md) là snapshot hiện hành sau Bước 1; báo cáo Bước 1 giữ vai trò baseline lịch sử.

Kiểm kê cấu trúc và backlog theo từng record bằng `python scripts/audit_data_readiness.py --require-current-link-attestation --json-output data-readiness.json`. Cờ này so tập URL hiện tại với [lời kiểm tra thủ công đã ghi](Data/link_review_attestation.json); nó không mở lại URL hoặc duyệt nội dung. Chạy `python scripts/generate_priority_review.py` để tạo lại hàng đợi nghề/kỹ năng và `python scripts/audit_module_paths.py` để thử toàn bộ 131 nghề qua các module lõi. Gói nguồn **ứng viên local** được tạo bằng `python scripts/build_release.py` (ZIP, tar.gz, `SHA256SUMS` trong `dist/`); [ghi chú ứng viên 0.4.0](docs/release-notes/v0.4.0-candidate.md) nêu các cổng còn cần đóng trước khi công bố.

## Docker

```bash
docker build -t ai-career-coach:local .
docker run --rm -p 8501:8501 ai-career-coach:local
```

Health endpoint: `http://localhost:8501/_stcore/health`. Image dùng Python 3.12, chạy bằng user không phải root và cài `requirements.lock` runtime có kiểm tra hash.

## Demo

Màn hình “Dùng hồ sơ mẫu tổng hợp” có ba hồ sơ minh họa gắn với role thật trong catalog. Mỗi hồ sơ được đánh dấu synthetic; không mô tả người thật, kinh nghiệm thật hay kết quả tuyển dụng. Xem [docs/demo.md](docs/demo.md) để có kịch bản và lời dẫn.

## Tài liệu và dữ liệu

- [Hợp đồng API](docs/interface.md)
- [Sơ đồ kiến trúc](docs/architecture.md)
- [Chất lượng và giới hạn dữ liệu](docs/data_quality.md)
- [Kiểm kê giấy phép và provenance](LICENSES.md)
- [Checklist PoF local](docs/pof-checklist.md)
- [Kiểm kê mức sẵn sàng dữ liệu](docs/verification/data-readiness-2026-10-26.md)
- [Danh sách ưu tiên review theo 131 nghề và kỹ năng](docs/verification/priority-review-2026-10-26.md)
- [Kiểm tra đường đi của 131 nghề qua các module](docs/verification/module-paths-2026-10-26.md)
- [Rà lại Level học liệu và nguồn gốc quyết định](docs/reviews/resource-level-scope-2026-10-26.md)
- [Kiểm tra tình trạng URL học liệu](docs/reports/links-live-2026-10-26.md)
- [Đối chiếu rubric B3/PoF và điểm nghẽn](docs/verification/b3-pof-gap-matrix.md)
- [Bàn giao sau sửa dữ liệu và logic](docs/verification/remediation-handoff-2026-10-26.md)

## Đóng góp

Xem [CONTRIBUTING.md](CONTRIBUTING.md). Hãy dùng fixture tổng hợp, giữ metadata nguồn và không đánh dấu resource/câu hỏi là reviewed nếu chưa có căn cứ.

## License và cộng đồng

Mã nguồn được phân phối theo [MIT License](LICENSE), giữ nguyên tên chủ bản quyền đang có trong tệp license. Trạng thái license của dữ liệu role, câu hỏi và tài liệu nguồn chưa được xác nhận đầy đủ; xem [LICENSES.md](LICENSES.md) trước khi phân phối lại bộ dữ liệu.

Repository [GitHub công khai](https://github.com/LinhLaSieuSao/AI-Career-Coach) có [Issues](https://github.com/LinhLaSieuSao/AI-Career-Coach/issues) để báo lỗi và [Discussions](https://github.com/LinhLaSieuSao/AI-Career-Coach/discussions) để trao đổi. Bản `main` đã có [CI thành công](https://github.com/LinhLaSieuSao/AI-Career-Coach/actions/runs/40157639170) ở commit `8827a81`; kết quả đó không kiểm chứng những thay đổi chưa công bố trong workspace. Kiểm tra ngày 25-10-2026 chưa thấy tag hoặc release công khai. [Snapshot bằng chứng](docs/verification/github-public-audit-2026-10-25.json) ghi rõ phạm vi kiểm tra.
