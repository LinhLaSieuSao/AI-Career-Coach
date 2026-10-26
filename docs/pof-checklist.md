# Checklist Proof of Functionality (local)

Đây là bằng chứng kiểm tra trong workspace local; không thay thế rubric chấm điểm chính thức hoặc xác nhận chất lượng nghề nghiệp độc lập.

| Tiêu chí | Bằng chứng tái lập | Trạng thái | Phạm vi còn lại |
| --- | --- | --- | --- |
| Môi trường Python 3.12 và cài sạch | [`requirements.lock`](../requirements.lock), [`requirements-dev.lock`](../requirements-dev.lock), [`clean-install.md`](verification/clean-install.md) | Venv sạch CPython 3.12.15; 429/429 test pass, coverage 91% | Máy khác/CI cần chạy lại; dependencies đã cài vượt mục tiêu 150 MB |
| Khởi động app local | [`README.md`](../README.md), [`app.py`](../app.py), [`test_app.py`](../tests/test_app.py) | Streamlit khởi động không exception/warning trong log thu được; health `200 ok`; browser mở được form và kết quả | Không tuyên bố tương thích mọi máy Windows/Linux; log chỉ thuộc lượt local |
| Luồng CV/kỹ năng đến Matcher | [`submission.py`](../modules/submission.py), [`test_app.py`](../tests/test_app.py), [`test_cv_parser.py`](../tests/test_cv_parser.py) | Covered: input tối thiểu, CV hợp lệ/sai định dạng, profile | OCR scan không có |
| Gợi ý role | [`matcher.py`](../modules/matcher.py), [`golden_profiles.json`](../tests/fixtures/golden_profiles.json), [`test_recommendation_quality.py`](../tests/test_recommendation_quality.py) | Golden benchmark 23 hồ sơ, có metrics Hit@3/MRR/forbidden | Benchmark tổng hợp không chứng minh validity ngoài đời |
| Lộ trình/tài liệu | [`recommender.py`](../modules/recommender.py), [`timed_planner.py`](../modules/timed_planner.py), [`resource-coverage-matrix.md`](resource-coverage-matrix.md) | Chặn blocked/unsuitable; reviewed được ưu tiên; partial/thiếu nguồn hiện rõ | Ma trận không phải expert review độc lập |
| Ngân hàng phỏng vấn | [`interview.py`](../modules/interview.py), [`validate_question_bank.py`](../scripts/validate_question_bank.py), [`test_question_bank_integrity.py`](../tests/test_question_bank_integrity.py) | 752 câu được kiểm tra cấu trúc; 20/20 câu ở 3 role demo có hướng dẫn; 16 câu AI-assisted QA được gắn nhãn riêng | AI review không thay thế owner/chuyên gia xác nhận; 727 câu chưa review và 3 template ở role khác còn backlog |
| Xuất báo cáo | [`test_export.py`](../tests/test_export.py) | Test định dạng, Unicode và nội dung | Chưa xác minh mở trong Microsoft Excel/Word GUI |
| Accessibility | [`app.py`](../app.py), [`test_app.py`](../tests/test_app.py), [`clean-install.md`](verification/clean-install.md) | Browser xác nhận DOM `lang="vi"`; Tab qua ba link đầu, Enter kích hoạt CTA, Space kích hoạt hồ sơ mẫu; form có nhãn truy cập | Chưa audit mọi widget, screen reader, độ tương phản hay WCAG |
| Giới hạn footprint | [`clean-install.md`](verification/clean-install.md), [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) | Mã nguồn + dữ liệu 18.6 MB; không có torch/spaCy/embedding nặng | Runtime dependencies trong venv 311 MB; ngưỡng <150 MB chưa đạt |
| Docker/CI và license | [CI workflow](../.github/workflows/ci.yml), [`LICENSES.md`](../LICENSES.md), [snapshot GitHub](verification/github-public-audit-2026-10-25.json) | `main` SHA `8827a81` có CI Python/Docker thành công; workspace đã bổ sung browser job, inventory và Docker lock | Bản local cải tiến chưa có CI đúng SHA; Docker Desktop local chưa có daemon; owner cần chốt license/provenance |

Số **429/429** ở dòng cài sạch là lịch sử của snapshot đó. [Rà soát người dùng](verification/comprehensive_user_audit.md) ghi lượt 25-10 có **460** test core và **4** browser; lượt 26-10 trên bản cải tiến có **466** core/AppTest và **5** Chromium browser pass. GitHub hiện là repo công khai có Issues và Discussions. [Ma trận B3/PoF](verification/b3-pof-gap-matrix.md) thay thế ước lượng PoF 125 trước đây bằng các khoản có bằng chứng và khoản còn phụ thuộc diễn giải rubric.

Ngày 26-10, gói ZIP ứng viên cũng đã được giải nén, cài `requirements.lock` có hash vào venv Python 3.12 mới, chạy smoke/validator/inventory từ gói và khởi động Streamlit health 200. [Bằng chứng và giới hạn](verification/clean-install.md) ghi rõ đây là Windows local, chưa phải CI trên đúng commit công bố hay Docker local.

Kiểm kê sâu cùng ngày đã tách **khả năng mở URL** (người dùng báo 165/165, gắn fingerprint), **nội dung đúng Level** (674/1.192 cặp nghề–skill), **câu hỏi liên quan** (750/1.192) và **quyền/provenance** (vẫn pending). [Báo cáo module](verification/module-paths-2026-10-26.md) ghi 131/131 role không exception trong luồng lõi; [nguồn chín sửa Level](reviews/resource-level-scope-2026-10-26.md) giải thích vì sao số ô thiếu tăng lên 760/1.248. Đây là bằng chứng về tính nhất quán dữ liệu, không nâng điểm review chuyên môn hoặc chứng minh 10/10.

## Trước khi tạo release thật

- Có người phụ trách xác nhận rubric PoF chính thức và nội dung đã AI hỗ trợ rà soát.
- Đóng các mục license/provenance còn mở trong [`LICENSES.md`](../LICENSES.md).
- Chạy GitHub Actions và Docker build/healthcheck trên môi trường phát hành.
- Thực hiện audit keyboard, screen reader, `lang="vi"` và kiểm tra giao diện trên các kích thước desktop cần hỗ trợ.
- Review release notes, version, license và tài sản trước khi tag/publish.
