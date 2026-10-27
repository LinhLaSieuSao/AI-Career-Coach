# License và provenance

`LICENSE` áp dụng MIT cho mã nguồn và ghi copyright `LinhLaSieuSao`. Maintainer cần xác nhận chủ thể này trước khi phát hành. MIT của mã nguồn không tự mở rộng sang dữ liệu, câu hỏi hoặc tài liệu được liên kết.

## Dependencies trực tiếp

`requirements.lock` khóa runtime và công cụ test trên Python 3.12. Bảng pin dưới đây được đọc từ lockfile ngày 27-10-2026; trước khi phát hành bản nhị phân, cần tạo SBOM và rà license của cả dependencies bắc cầu theo đúng image thực tế.

| Package | Pin | Phạm vi |
| --- | ---: | --- |
| streamlit | 1.66.1 | Web |
| pydantic | 2.14.1 | Schema |
| rapidfuzz | 3.14.6 | So khớp chuỗi |
| pdfplumber | 0.11.10 | PDF |
| python-docx | 1.2.0 | DOCX |
| requests | 2.34.2 | Kiểm tra link theo lệnh |
| pytest | 9.1.1 | Test |
| ruff | 0.17.3 | Lint |

## Dữ liệu và tài sản

| Thành phần | Trạng thái cần xác nhận |
| --- | --- |
| `data/roles.json`, `skill_catalog.json`, `skill_aliases.json` | Nguồn và quyền phân phối từng nhóm dữ liệu chưa được chứng minh đầy đủ. |
| `data/resources.json` | Repo chứa metadata và URL; quyền đối với nội dung tại các trang học liệu thuộc publisher tương ứng. Link công khai không cấp quyền sao chép. |
| `data/interview_questions/` | 766 câu, hiện đều gắn `unreviewed`; một số rubric có hỗ trợ AI và cần người có chuyên môn kiểm tra. |
| `data/demo_profiles.json` | Hồ sơ tổng hợp do dự án biên soạn, không đại diện cá nhân thật. |
| `assets/style.css`, `assets/site.js` | Tài sản giao diện trong repo; CSS dùng system font stack. |
| Logo/brand | `brand_assets/` không có trong clone; app dùng SVG fallback. Quyền đối với tên/brand cần được xác nhận riêng. |

Schema provenance trong catalog có các trường `source_url`, `author_origin`, `curated_by`, `review_tier`, `reviewed_at`, `rights_basis`, `license_notes`. Giá trị `null` biểu thị thiếu chứng cứ. Maintainer cần chốt provenance, review chuyên môn và giấy phép dữ liệu trước khi phân phối lại catalog hoặc quảng bá độ tin cậy của nội dung.
