# License và provenance

Kiểm kê này phản ánh file thực sự trong clone và metadata phân phối đã cài local. Nó chưa phải ý kiến pháp lý và không xác nhận quyền phân phối lại dữ liệu nguồn.

## Mã nguồn dự án

`LICENSE` chứa MIT License và hiện ghi copyright `LinhLaSieuSao`. Tên này được giữ nguyên; maintainer cần xác nhận đây là chủ bản quyền phù hợp trước khi phát hành. Không có thông tin pháp nhân/nhóm nào được tự thêm.

## Dependencies đã pin

License dưới đây đọc từ metadata của các distribution trong môi trường sạch Python 3.12.14; `pdfplumber` dùng classifier MIT do trường License-Expression không có.

| Phạm vi | Package | Pin | License metadata |
| --- | --- | ---: | --- |
| Runtime | Streamlit | 1.66.0 | Apache-2.0 |
| Runtime | pdfplumber | 0.11.10 | MIT classifier |
| Runtime | python-docx | 1.2.0 | MIT |
| Dev | pytest | 9.1.1 | MIT |
| Dev | pytest-cov | 6.2.1 | MIT |
| Dev | coverage | 7.17.0 | Apache-2.0 |
| Dev | requests | 2.34.2 | Apache-2.0 |

Các dependency bắc cầu được pip tải theo metadata của package; bảng trên liệt kê dependency trực tiếp. Trước phân phối nhị phân cần tạo SBOM và rà license cả dependency bắc cầu theo đúng artifact build.

## Dữ liệu và assets

| Thành phần | Bằng chứng hiện có | Trạng thái quyền/provenance |
| --- | --- | --- |
| Role catalog | `Data/roles.json` | Không có metadata license/provenance per-record; cần maintainer truy lại nguồn và xác nhận quyền phân phối. |
| Skill aliases/catalog | `Data/skill_aliases.json`, `Data/skill_catalog.json` | Dữ liệu cấu trúc trong repo; tác giả/nguồn lịch sử chưa ghi đủ. |
| Resource catalog | `Data/resources.json`, `docs/data_quality.md`, `docs/reports/` | App giữ tiêu đề, metadata và link; nội dung liên kết thuộc publisher/site tương ứng. Link công khai không cấp quyền sao chép hay phân phối lại nội dung. |
| Interview questions/answers | `Data/interview_question/` | Một phần nguồn có URL trong rubric; toàn bộ câu hỏi/đáp án chưa có provenance và license theo từng record. Cần kiểm kê trước khi phát hành dữ liệu. |
| Rubrics | `Data/interview_rubrics.json` | Sáu rubric được review nội bộ; không dùng tên chuyên gia. Nguồn chuyên môn được liên kết trong metadata; quyền tái sử dụng nguồn vẫn theo chủ nguồn. |
| Hồ sơ demo | `Data/demo_profiles.json` | Ví dụ tổng hợp do dự án ghi; role/skill lấy từ catalog. Không đại diện cá nhân hay kết quả tuyển dụng. |
| Logo/brand | `brand_assets/` không tồn tại trong clone. `app.py` tạo fallback SVG tối giản chứa “AI”. | Không có file logo bên thứ ba được phân phối. Tên/brand ownership chưa được xác nhận riêng. |
| Font | `assets/style.css` dùng system font stack | Không tải Google Fonts hoặc font binary bên ngoài. Font hệ điều hành thuộc license của nền tảng tương ứng. |

Không gộp license code MIT sang catalog/dữ liệu chưa rõ quyền. Maintainer cần cung cấp provenance role, question/answer và chủ thể brand trước khi công bố gói dữ liệu hoặc tuyên bố tương thích license.
