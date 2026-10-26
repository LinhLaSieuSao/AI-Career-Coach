# Trạng thái ma trận P01–P27

Trạng thái dưới đây theo code, test và kiểm chứng local hiện có. “Đã xử lý” chỉ mô tả phạm vi có bằng chứng; không hàm ý mọi dữ liệu/kiểm thử bên ngoài đã hoàn tất.

**Lưu ý lịch sử:** Ma trận P01–P27 dưới đây chụp trạng thái Đợt 5 trước các đợt nghiệm thu ngày 25–26/10; số 385 test, tình trạng GitHub/CI và câu hỏi trong từng dòng không còn là số liệu mới nhất. Xem [rà soát người dùng](verification/comprehensive_user_audit.md), [inventory dữ liệu 26/10](verification/data-readiness-2026-10-26.md) và [đối chiếu B3/PoF](verification/b3-pof-gap-matrix.md) để quyết định trên bản hiện tại. Bản public `main` đã có CI Python/Docker xanh, nhưng bản local chưa có CI đúng SHA.

| ID | Trạng thái | Bằng chứng code/test/doc | Việc còn lại |
| --- | --- | --- | --- |
| P01 | Một phần | `modules/data_quality.py`; `tests/test_data_integrity.py`; `docs/data_quality.md` | Integrity có warning recognition-only; maintainer xác nhận provenance và hướng xử lý. |
| P02 | Một phần | `Data/skill_aliases.json`, `Data/skill_catalog.json`; `tests/test_profile.py`, `tests/test_skill_extractor.py`; `docs/interface.md` | Ví dụ yêu cầu đã xử lý; vocabulary hữu hạn, không bao phủ mọi biến thể. |
| P03 | Đã xử lý | `modules/skill_extractor.py`, `modules/profile.py`; `tests/test_profile.py`; `docs/interface.md` | Có thể mở rộng display labels; canonical đã chốt. |
| P04 | Đã xử lý | `modules/matcher.py::compute_gap`, `modules/levels.py`; `tests/test_assessment.py`; `docs/assessment_contract.md` | Level tự khai báo chưa là xác minh năng lực thực. |
| P05 | Một phần | `modules/timed_planner.py`; `tests/test_timed_roadmap.py`; `docs/reports/dot04_demo_assessments.json`; 385 test local qua | Thiếu review/level coverage/duration; tổng tuần role demo chưa xác định. |
| P06 | Một phần | `Data/resources.json`; `docs/data_quality.md`; `docs/reports/` | Chưa review toàn catalog và provenance từng mapping. |
| P07 | Đã xử lý | `modules/submission.py`, `modules/matcher.py`, `app.py`; `tests/test_app.py` | Nhận diện giới hạn ở catalog hiện hành. |
| P08 | Đã xử lý | `modules/matcher.py::suggest_roles`; `tests/test_assessment.py`; `docs/assessment_contract.md` | Chưa đánh giá heuristic với người dùng; không phải xác suất tuyển dụng. |
| P09 | Một phần | `modules/interview.py`; `tests/test_interview_assessment.py`, `tests/test_app_assessment.py`; `docs/assessment_contract.md` | Chỉ 6/752 câu có hướng dẫn review nội bộ; 12 template, 734 unreviewed. Tự động chấm đã gỡ; cần review thêm và độc lập. |
| P10 | Đã xử lý | `modules/cv_parser.py`; `tests/test_cv_parser.py`, `tests/test_submission.py` | Chưa OCR PDF scan. |
| P11 | Đã xử lý | `modules/submission.py`, `app.py`; `tests/test_app.py` | Upload browser chưa kiểm tra trực quan. |
| P12 | Một phần | `Data/`, `modules/catalog.py`, `tests/test_catalog.py`, `.gitattributes`; full suite Windows/Python 3.15 local | CI Ubuntu và Python 3.11 chưa có kết quả. |
| P13 | Một phần | `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `docs/pof-checklist.md` | Rubric PoF nguồn không có; chưa tạo channel, version, tag hay release. |
| P14 | Một phần | `Dockerfile`, `.github/workflows/ci.yml` | CI đã cấu hình; GitHub workflow chưa chạy và Docker CLI thiếu local. |
| P15 | Đã xử lý | `requirements.txt`, `requirements-dev.txt`; cài sạch Python 3.12 và `pip check`; `LICENSES.md` | SBOM cần rà cả dependency bắc cầu trước phân phối nhị phân. |
| P16 | Một phần | `.gitattributes`, `.vscode/settings.json`, `.gitignore` | Quy tắc EOL và setting đa nền tảng đã thêm; không migration hàng loạt. |
| P17 | Một phần | `docs/interface.md`, `docs/architecture.md`, `assets/style.css`, `docs/demo.md`; 385 test và browser local qua | Chưa có screenshot/layout review, bàn phím/screen reader hoặc nghiệm thu độc lập. |
| P18 | Một phần | `LICENSES.md`, `LICENSE`, `Data/` | Owner xác nhận quyền dữ liệu/brand và bản quyền trước khi release. |
| P19 | Đã xử lý | `modules/submission.py`, `app.py`; `tests/test_app.py` | Không có phần còn thiếu đã biết trong phạm vi form. |
| P20 | Một phần | `assets/style.css`, `tests/test_app.py`; parser/upload qua AppTest | Chưa upload CV từ browser trong đợt này; cần screenshot và kiểm tra trạng thái UI trước/sau upload. |
| P21 | Một phần | `assets/style.css`, `app.py`; `tests/test_app_assessment.py` | Khoảng title/form và khung tab đã chỉnh; cần screenshot xác nhận. |
| P22 | Một phần | `assets/style.css` media queries | Mobile CSS đã chỉnh; viewport thật chưa kiểm tra. |
| P23 | Một phần | `app.py::RESULT_TABS`; `tests/test_app_assessment.py`; full suite 385 passed; browser desktop local | Tabs và luồng phỏng vấn được thao tác; cần screenshot/layout review. |
| P24 | Đã xử lý | `app.py`, `modules/profile.py`; `tests/test_app.py` | AppTest phủ undo nhiều mục, revision và state. |
| P25 | Một phần | `app.py` labels; `Data/demo_profiles.json`; `docs/demo.md` | Không dùng cộng đồng giả; maintainer cung cấp Issues/Discussions thật nếu muốn link. |
| P26 | Một phần | `modules/export.py`, demo JSON/docs; `tests/test_export.py`; `docs/release-notes/dot_05.md` | Kịch bản/outline/lời dẫn có; slide, video, screenshot chưa tạo. |
| P27 | Đã xử lý code/test | `app.py` gọi core; `tests/test_app.py`, `tests/test_app_assessment.py`, `tests/test_export.py`; full suite 385 passed | Chưa có kết quả CI/Docker; không có semantic scorer vì phần lớn câu hỏi chưa đủ dữ liệu review. |

AppTest không thay thế kiểm tra pixel/layout. Test không phụ thuộc link Internet. Xem [tiến độ xử lý v4.0](progress/v4-remediation.md) và [tiến độ Đợt 5](progress/dot_05.md) để có kết quả theo môi trường.
