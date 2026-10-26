# Kiểm kê mức sẵn sàng dữ liệu

Ngày đối chiếu: **2026-10-26**. Dấu vân tay dữ liệu: `01dba94c2991f18af28a6163e019e0ef54a734dc4c4fff6b55b7c19d731a9bae`.

Báo cáo đọc dữ liệu hiện có, không sửa record và không truy cập mạng. Review nội dung, khả năng truy cập link và quyền phân phối là ba loại bằng chứng riêng. Thiếu metadata không chứng minh vi phạm quyền hoặc chưa từng có review ở nơi khác.

| Nhóm | Kết quả |
| --- | --- |
| Catalog | 131 role; 410 skill của role; 416 skill nhận diện |
| Resource mapping | 471 record; 166 URL; 255 mapping đủ điều kiện qua chính sách hiện hành trên 214 skill |
| Trạng thái học liệu | reviewed: 54; partial: 201; unsuitable: 175; blocked: 41; unreviewed: 0 |
| Ngân hàng phỏng vấn | 766 câu; reviewed_internal: 0; ai_reviewed_internal: 0; template: 0; unreviewed: 766 |
| Role có ít nhất một câu review nội bộ/AI hỗ trợ | 0/131 |
| Skill × level | 1248 ô: 76 reviewed; 408 partial; 764 chưa có tài liệu đủ điều kiện |
| Thực hành cho ô chưa có tài liệu | 76 ô có lộ trình thực hành; không coi đây là chứng nhận bao phủ chuyên môn |
| Nghề × kỹ năng yêu cầu | 1192 cặp; 764 có ít nhất một câu hỏi; 666 có học liệu đúng Level yêu cầu |
| Cặp ưu tiên (weight ≥ 2) | 950 cặp; 720 có câu hỏi; 497 có học liệu đúng Level |
| Cần biên tập thêm | 59 câu dùng mẫu lời hỏi chung; 2 mapping reviewed phủ cả Level 1–3 cần đối chiếu phạm vi |
| Xác nhận link do người dùng báo | stale_or_invalid: 166 URL; ngày 2026-10-26 |

Xác nhận link chỉ ghi nhận lời kiểm tra thủ công của người dùng trên đúng tập URL hiện tại; không nâng mức review nội dung, Level hay quyền sử dụng. Bất cứ URL nào đổi sẽ làm dấu vân tay xác nhận này hết hiệu lực.

## Cổng kiểm tra

| Cổng | Trạng thái | Phạm vi |
| --- | --- | --- |
| Nhất quán của inventory | PASS | 0 lỗi; cần chạy thêm bộ test/validator dự án |
| Dấu vân tay xác nhận link | PENDING | So khớp 166 URL với lời kiểm tra thủ công của người dùng; không phải tái kiểm tra mạng |
| Metadata review toàn ngân hàng | PENDING | 766 câu unreviewed/template; không thay thế chuyên gia |
| Metadata provenance theo record | PENDING | 1368 record chưa đủ trường bằng chứng; không phải kết luận pháp lý |

## Khung khắc phục

1. **Review câu hỏi theo role và mức độ rủi ro:** ưu tiên các role trình diễn và role dùng thực tế, rồi chia backlog theo chuyên ngành. Mỗi câu cần tình huống riêng, hướng dẫn có bối cảnh, nguồn phù hợp, ngày và người review; AI hỗ trợ vẫn giữ nhãn riêng. Chỉ người có chuyên môn/owner mới có thể cung cấp xác nhận độc lập.
2. **Bổ sung học liệu theo ô skill–level đang thiếu:** không tăng level_from/level_to chỉ để làm đầy ma trận. Partial phải có bài tập phù hợp và ghi phạm vi. Kỹ năng mềm dùng thực hành, người quan sát và phản hồi; các ô thực hành không tự biến thành tài liệu chuyên môn đã review.
3. **Đối chiếu nguồn gốc trước phát hành dữ liệu:** owner ghi tác giả/nguồn gốc, cơ sở sử dụng, giấy phép/điều khoản và người xác nhận. quality_sources, verified=true và HTTP 200 không phải quyền sao chép. Có thể dẫn chứng manifest cấp tệp khi cùng nguồn/phạm vi, nhưng cần ánh xạ rõ tới record.
4. **Catalog nghề:** ghi cơ sở của skill/level/weight và review của người hiểu nghề; regression synthetic không chứng minh độ phù hợp tuyển dụng ngoài đời.
5. **Không nâng điểm bằng đổi nhãn:** report cho phép CI chặn claim review thiếu bằng chứng, giữ pending ngoài phạm vi đã xác minh. Website cần nói rõ câu hỏi tham khảo và metadata nội bộ.

## Ghi metadata provenance

Schema 2.0 ghi `provenance` với bảy trường: `source_url`, `author_origin`, `curated_by`, `review_tier`, `reviewed_at`, `rights_basis`, `license_notes`. `null`/`pending` không được tính là bằng chứng. URL nguồn của học liệu không tự xác nhận tác giả mapping, quyền sao chép hoặc license dữ liệu; không mặc định MIT cho dữ liệu. Cổng đầy đủ vẫn pending cho đến khi owner/chuyên gia cung cấp căn cứ thật.

| Nhóm record | Tổng | Có metadata | Đủ trường bằng chứng |
| --- | ---: | ---: | ---: |
| roles | 131 | 0 | 0 |
| questions | 766 | 39 | 0 |
| resource_mappings | 471 | 471 | 0 |

## Role có review nội bộ hoặc AI hỗ trợ

| Role | Tổng câu | Review nội bộ | AI hỗ trợ | Template | Chưa review |
| --- | ---: | ---: | ---: | ---: | ---: |

## Những nghề cần ưu tiên bổ sung theo Level và câu hỏi

Bảng xếp theo số kỹ năng weight ≥ 2 chưa có tài liệu đúng Level và số kỹ năng chưa có câu hỏi. Một URL nhập môn ở Level 1 không được tính là bao phủ yêu cầu Level 3.

| Role | Học liệu đúng Level / skill | Skill có câu hỏi / skill | Thiếu học liệu ưu tiên | Thiếu câu hỏi ưu tiên |
| --- | ---: | ---: | ---: | ---: |
| `legal_executive` | 1/9 | 6/9 | 8 | 3 |
| `tax_accountant` | 2/10 | 7/10 | 7 | 2 |
| `fullstack_developer_net_angular` | 5/11 | 7/11 | 6 | 4 |
| `customs_declaration_specialist` | 2/8 | 5/8 | 6 | 3 |
| `ecommerce_executive` | 3/10 | 5/10 | 6 | 3 |
| `import_export_executive` | 2/9 | 5/9 | 6 | 3 |
| `retail_store_manager` | 3/9 | 5/9 | 6 | 3 |
| `cb_specialist` | 3/9 | 6/9 | 6 | 2 |
| `financial_controller` | 4/10 | 7/10 | 6 | 2 |
| `investment_analyst` | 4/10 | 7/10 | 6 | 2 |
| `electrical_engineer` | 2/8 | 6/8 | 6 | 0 |
| `safety_engineer` | 2/8 | 6/8 | 6 | 0 |
| `admin_executive` | 4/9 | 5/9 | 5 | 3 |
| `brand_executive` | 4/9 | 5/9 | 5 | 3 |
| `customer_success_manager` | 4/9 | 5/9 | 5 | 3 |
| `ecommerce_manager` | 4/10 | 5/10 | 5 | 3 |
| `employer_branding_executive` | 3/9 | 5/9 | 5 | 3 |
| `pr_executive` | 4/9 | 5/9 | 5 | 3 |
| `project_manager` | 4/9 | 6/9 | 5 | 3 |
| `real_estate_sales_executive` | 3/9 | 5/9 | 5 | 3 |
| `risk_management_officer` | 4/10 | 6/10 | 5 | 3 |
| `hr_executive` | 3/9 | 5/9 | 5 | 2 |
| `logistics_coordinator` | 3/9 | 5/9 | 5 | 2 |
| `sales_admin` | 4/9 | 5/9 | 5 | 2 |
| `compliance_officer` | 2/8 | 5/8 | 5 | 1 |

## Tái lập

```powershell
python scripts/audit_data_readiness.py --as-of 2026-10-26 --json-output docs/verification/data-readiness-2026-10-26.json --markdown-output docs/verification/data-readiness-2026-10-26.md
```

CLI mặc định trả lỗi khi inventory không nhất quán. Thêm `--require-current-link-attestation` để CI phát hiện tập URL đã đổi sau lời kiểm tra của người dùng; tùy chọn `--require-complete-review` hoặc `--require-provenance` dành cho cổng phát hành. Không bật rồi đổi nhãn giả để làm test xanh. JSON chứa locator, trạng thái và thiếu hụt của từng record để chia việc review.
