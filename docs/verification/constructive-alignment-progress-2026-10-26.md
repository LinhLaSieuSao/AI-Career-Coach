# Tiến độ căn chỉnh Role–Resource–Question theo bằng chứng

> **Snapshot lịch sử trước đợt sửa câu hỏi/học liệu ngày 26-10-2026.** Các số 752 câu, 14 cặp thiếu câu và 165 URL dưới đây đã thay đổi. Xem [bàn giao sau sửa](remediation-handoff-2026-10-26.md) và [inventory hiện hành](data-readiness-2026-10-26.json) trước khi dùng số liệu để đánh giá hoặc sửa giao diện.

Ngày chốt snapshot: **26-10-2026**. Đối chiếu với `data-readiness-2026-10-26.json`, `evidence-schema-v2-2026-10-26.json` và dữ liệu trong `Data/`. Đây là đánh giá nội bộ để điều hành việc sửa web local; không phải xác nhận độc lập của chuyên gia nghề, cơ quan quản lý hay hội đồng chấm.

## Cách đọc số liệu

- `reviewed` ở học liệu là **review mapping nội bộ**; `verified=true` cũ chủ yếu liên quan link. Người dùng đã báo mở được **165 URL** trong tập URL hiện tại. Điều đó không tự xác nhận nội dung, đúng Level, quyền tái sử dụng hay tính cập nhật của quy định.
- **674/1.192** yêu cầu role–skill có *mapping đủ điều kiện theo policy cũ ở Level được gán*. Đây không phải 674 yêu cầu đã đạt chuẩn evidence v2. Chỉ **4/471** mapping toàn catalog có `scope_granularity` ở cấp lesson/module/chapter/spec **và** `evidence_locator` khác rỗng; vị trí dẫn chứng ghi trong dữ liệu cũng chưa được chuyên gia xác nhận độc lập.
- **442** là số cặp **role–skill** chưa có câu hỏi, không phải số câu mới bắt buộc duy nhất hoặc 442 ô skill × level toàn catalog. **175 unsuitable + 41 blocked** là trạng thái chính sách mapping; không được gọi thành 216 URL chết.
- Bài thực hành tự biên soạn cho sáu kỹ năng ngang là một đường học có thể dùng ngay để luyện tập. Nó không biến 197 khoảng trống học liệu thành 197 học liệu verified và không chứng minh người học đã đạt Level.

## Tiến độ theo năm giai đoạn của khung thực hành

| Giai đoạn | Việc đã thực hiện trong snapshot này | Điều kiện chuyển giai đoạn |
| --- | --- | --- |
| 1. Rubric & schema | Ban hành `schema-contract-v2.md`; di trú 1.354 record có trường provenance theo mẫu pending; bổ sung scope/trục bằng chứng độc lập cho resource và scenario/rubric cho question; validator kiểm đủ khóa Role–Skill–Level. | **Đạt về cấu trúc**: validator PASS, 0 lỗi. **Chưa đạt về nội dung**: strict evidence gate vẫn PENDING. |
| 2. Sáu kỹ năng ngang & bốn nghề demo | Có route thực hành với checklist quan sát cho sáu kỹ năng và năm bộ bài tập đọc tiếng Anh theo nhóm nghề; giao diện hiển thị bài tập và trạng thái. | **Chưa đạt**: route chưa có phản hồi thực tế của mentor; bốn nghề demo chưa 100% verified & aligned; không tuyên bố giải quyết 38% bằng chứng học liệu. |
| 3. Ngân hàng câu hỏi | Giữ nguyên nhãn review hiện có, đưa chỗ thiếu vào inventory theo từng role–skill. | **Chưa đạt**: 727 unreviewed, 3 template, 67 câu dùng lối hỏi chung; 442 cặp role–skill thiếu câu. Không đổi nhãn hàng loạt bằng script. |
| 4. Học liệu, risk & provenance | Policy hiện tại đã loại `unsuitable`/`blocked` khỏi đề xuất; schema cho phép ghi rõ scope và quyền. | **Chưa đạt**: 464 mapping chưa có scope cấp đơn vị được xác định; 0/1.354 record đủ bảy trường bằng chứng; nguồn pháp lý/y tế/an toàn cần review chuyên ngành. |
| 5. Gate & UI | CI có gate schema cấu trúc. Giao diện phân biệt mapping nội bộ, link do chủ dự án báo kiểm tra, scope Level còn pending, bài tập tự biên soạn; timed roadmap giữ unresolved khi tài liệu thiếu scope. | **Chưa đạt** strict evidence gate; không được báo PASS 100% hay điểm 10/10. |

## Bốn nghề demo: hàng đợi cụ thể

| Role | Có học liệu ở Level gán / kỹ năng | Có câu hỏi / kỹ năng | Khoảng trống cần xử lý |
| --- | ---: | ---: | --- |
| `sales_executive` | 4/8 | 5/8 | Học liệu/đường thực hành cần căn chỉnh cho bán hàng L3, thuyết phục L2, CSKH L2, giải quyết vấn đề L2; thêm câu cho làm việc nhóm, giải quyết vấn đề, quản lý thời gian; viết lại 3 template. |
| `frontend_developer_react` | 11/11 | 7/11 | Thêm câu cho Git L2, REST API L2, TypeScript L1, thiết kế UI/UX L1; rà cấp bài học của 11 mapping, nhất là các trang catalog. |
| `data_analyst` | 8/10 | 6/10 | Excel L3 và giải quyết vấn đề L2 thiếu học liệu đúng Level; thêm câu cho thống kê, giao tiếp, làm việc nhóm, Tableau. |
| `backend_developer_java` | 8/10 | 7/10 | Java L3 và giải quyết vấn đề L2 thiếu học liệu đúng Level; thêm câu cho Docker, làm việc nhóm, Linux. |

Bốn role có **39** yêu cầu skill: **31** có mapping ở Level được gán theo policy, **25** có câu hỏi, chỉ **1** có resource ghi được scope cấp đơn vị cùng locator tại Level yêu cầu. Số 1 chỉ là **đủ hình thức dẫn chứng tối thiểu**, không phải review chuyên gia. Tiêu chí 100% verified & aligned của giai đoạn 2 chưa đạt.

## Thứ tự khắc phục có thể kiểm chứng

1. Rà từng resource của bốn nghề demo: mở đúng mục/chương, ghi URL đến phần con, `evidence_locator`, phạm vi nội dung, Level thực hỗ trợ, ngày kiểm tra, tác giả và cơ sở dẫn link/tái sử dụng. Giảm `level_to` nếu nội dung chỉ nhập môn; giữ `pending` khi chưa đọc được nội dung. Ưu tiên Java L3, Excel L3, bán hàng L3 và các skill weight ≥ 2.
2. Hoàn thiện **14 cặp role–skill thiếu câu** của bốn role bằng câu tình huống có bối cảnh, ràng buộc, sản phẩm bàn giao, rubric đúng Level và red flags. Với câu do AI soạn, ghi `ai_reviewed_internal`, nguồn kỹ thuật đúng phần, và chờ owner/chuyên gia xác nhận. Chỉnh 3 sales template trước khi tuyên bố role demo sẵn sàng.
3. Thu sản phẩm thực hành ẩn danh và phản hồi có vai trò người quan sát cho sáu kỹ năng ngang. Năm bài tiếng Anh là bản nháp thực hành; người am hiểu ngành cần xác nhận thuật ngữ, bài đọc cụ thể và Level. Không chặn thực hành kỹ năng mềm chỉ vì thiếu khóa học.
4. Sau khi đạt demo mới mở rộng 67 câu hỏi chung, 442 cặp thiếu, 760 ô skill × level không có material theo policy; chia theo risk và weight. Role thuế/luật/y tế/an toàn đi qua nguồn chính thức còn hiệu lực và người rà soát đúng chuyên môn.
5. Chỉ bật strict gate làm điều kiện phát hành khi metadata quyền, scope và chuyên gia thật đã được ghi. CI hiện chỉ chặn schema sai cấu trúc; báo cáo phải tiếp tục hiển thị pending.

## Góc nhìn người chấm giả định

Các luồng web local có thể trình diễn và kiểm thử; mô hình dữ liệu hiện nhất quán, có đường thực hành cho kỹ năng mềm và đã tránh tự chấm điểm câu trả lời phỏng vấn. Tuy nhiên một giám khảo xem kỹ bằng chứng sẽ hỏi “phần nào của tài liệu dạy đúng Level?” và “ai xác nhận câu hỏi/nguồn/quyền?”; snapshot này chưa trả lời được cho phần lớn catalog. Nếu **buộc ước lượng riêng cho mức sẵn sàng của web local** theo bốn trục chức năng, trải nghiệm, căn chỉnh dữ liệu và độ tin cậy nguồn, mức hợp lý hiện là **khoảng 5–6/10**: chức năng chạy được kéo lên, còn bằng chứng dữ liệu và quyền kéo xuống. Đây không phải điểm B3/PoF chính thức và **chưa có căn cứ đánh giá tổng thể 10/10**. Điểm chính thức phụ thuộc đề bài và hội đồng; mọi điểm số tự gán ở đây không thay được kiểm thử với người dùng và thẩm định chuyên môn.

## Kết quả kiểm chứng local

- **474/474** test Python/AppTest; **6/6** test Chromium sau khi test thực sự đi qua bước chọn role; **131/131** role qua bộ kiểm module.
- `validate_question_bank.py`: 752 câu/131 role, 0 lỗi toàn vẹn. `validate_evidence_schema.py`: 0 lỗi cấu trúc, strict evidence **PENDING**; `migrate_evidence_schema_v2.py --check`: 0 file cần đổi. `git diff --check`: 0 lỗi khoảng trắng.
- Gói ứng viên ZIP và tar.gz có cùng 141 file với source allowlist và checksum khớp. Đây là kiểm tra đóng gói local, không phải xác nhận bản phát hành GitHub hoặc quyền phân phối dữ liệu.

## Lệnh tái lập

```powershell
python scripts/migrate_evidence_schema_v2.py --check
python scripts/validate_evidence_schema.py --as-of 2026-10-26 --json-output docs/verification/evidence-schema-v2-2026-10-26.json
python scripts/audit_data_readiness.py --as-of 2026-10-26 --json-output docs/verification/data-readiness-2026-10-26.json --markdown-output docs/verification/data-readiness-2026-10-26.md --require-current-link-attestation
python scripts/audit_module_paths.py --as-of 2026-10-26
```

Lệnh thứ hai trả PASS cho **schema**; `--require-complete-evidence` phải báo fail/pending trên snapshot hiện tại. Không sửa metadata giả chỉ để làm gate xanh.
