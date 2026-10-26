# License và provenance

Kiểm kê này phản ánh file thực sự trong clone và metadata phân phối đã cài local. Nó chưa phải ý kiến pháp lý và không xác nhận quyền phân phối lại dữ liệu nguồn.

## Mã nguồn dự án

`LICENSE` chứa MIT License và hiện ghi copyright `LinhLaSieuSao`. Tên này được giữ nguyên; maintainer cần xác nhận đây là chủ bản quyền phù hợp trước khi phát hành. Không có thông tin pháp nhân/nhóm nào được tự thêm.

## Dependencies đã pin

Pin dưới đây đối chiếu `requirements.lock` và `requirements-dev.lock` ngày 26-10-2026; license đọc từ metadata distribution trong môi trường kiểm thử Python 3.12.15. `pdfplumber` dùng classifier MIT vì không có `License-Expression`; metadata của `axe-playwright-python` không nêu license nên cần kiểm tra nguồn phân phối trước release.

| Phạm vi | Package | Pin | License metadata |
| --- | --- | ---: | --- |
| Runtime | Streamlit | 1.66.1 | Apache-2.0 |
| Runtime | pdfplumber | 0.11.10 | MIT classifier |
| Runtime | python-docx | 1.2.0 | MIT |
| Dev | pytest | 9.1.1 | MIT |
| Dev | pytest-cov | 6.3.0 | MIT |
| Dev | coverage | 7.17.0 | Apache-2.0 |
| Dev | requests | 2.34.2 | Apache-2.0 |
| Dev | playwright | 1.64.1 | Apache-2.0 |
| Dev | axe-playwright-python | 0.1.8 | Chưa thấy license trong metadata đã cài; cần đối chiếu tệp nguồn |

Các dependency bắc cầu được pip tải theo metadata của package; bảng trên liệt kê dependency trực tiếp. Trước phân phối nhị phân cần tạo SBOM và rà license cả dependency bắc cầu theo đúng artifact build. Bộ Playwright/axe là công cụ test, không nằm trong Docker runtime, nhưng có trong gói nguồn để kiểm chứng dự án.

## Dữ liệu và assets

| Thành phần | Bằng chứng hiện có | Trạng thái quyền/provenance |
| --- | --- | --- |
| Role catalog | `Data/roles.json` | Không có metadata license/provenance per-record; cần maintainer truy lại nguồn và xác nhận quyền phân phối. |
| Skill aliases/catalog | `Data/skill_aliases.json`, `Data/skill_catalog.json` | Dữ liệu cấu trúc trong repo; tác giả/nguồn lịch sử chưa ghi đủ. |
| Resource catalog | `Data/resources.json`, `docs/data_quality.md`, `docs/reports/` | App giữ tiêu đề, metadata và link; nội dung liên kết thuộc publisher/site tương ứng. Link công khai không cấp quyền sao chép hay phân phối lại nội dung. |
| Interview questions/answers | `Data/interview_question/` | Có 766 câu, 0 template. 39 câu của bốn nghề demo có bối cảnh/rubric bản nháp AI; 22 câu từng có metadata review được lưu lại ở `prior_review_metadata` nhưng bản hiện hành đã hạ về `unreviewed` để chờ duyệt phần bổ sung. Cả 766 câu hiện gắn `unreviewed`. `quality_sources` cũ không cấp quyền sao chép từ publisher. Cần owner kiểm kê trước khi phát hành dữ liệu. |
| Hồ sơ demo | `Data/demo_profiles.json` | Ví dụ tổng hợp do dự án ghi; role/skill lấy từ catalog. Không đại diện cá nhân hay kết quả tuyển dụng. |
| Logo/brand | `brand_assets/` không tồn tại trong clone. `app.py` tạo fallback SVG tối giản chứa “AI”. | Không có file logo bên thứ ba được phân phối. Tên/brand ownership chưa được xác nhận riêng. |
| Font | `assets/style.css` dùng system font stack | Không tải Google Fonts hoặc font binary bên ngoài. Font hệ điều hành thuộc license của nền tảng tương ứng. |

Không gộp license code MIT sang catalog/dữ liệu chưa rõ quyền. Maintainer cần cung cấp provenance role, question/answer và chủ thể brand trước khi công bố gói dữ liệu hoặc tuyên bố tương thích license.

Schema provenance hiện có đúng bảy trường: `source_url`, `author_origin`, `curated_by`, `review_tier`, `reviewed_at`, `rights_basis`, `license_notes`. Giá trị `null` là chờ chứng cứ, không phải xác nhận nguồn hoặc quyền. Dữ liệu catalog chưa được chủ dự án chọn giấy phép riêng; quyết định này cần người có quyền sở hữu dữ liệu thực hiện. Các trang học liệu được app dẫn bằng liên kết ngoài, không nhập nguyên khóa học vào repo; quyền dùng nội dung từ từng publisher vẫn cần kiểm tra nếu dự án muốn sao chép hoặc phân phối lại.
