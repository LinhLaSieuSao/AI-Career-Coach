# Bàn giao sửa dữ liệu và logic trước khi hoàn thiện giao diện — 26-10-2026

Tài liệu này là snapshot **sau** các bước sửa, đối chiếu với [baseline Bước 1](demo-role-quality-gate-2026-10-26.md). Các báo cáo baseline khác giữ nguyên để có thể so sánh theo thời gian. Đây là nghiệm thu kỹ thuật local và biên tập bản nháp; không phải thẩm định chuyên gia nghề nghiệp, xác nhận pháp lý hay điểm chấm chính thức.

## Phần đã xử lý

| Hạng mục | Baseline | Trạng thái hiện tại |
| --- | ---: | ---: |
| Cặp role–skill demo thiếu câu hỏi | 14/39 | **0/39**; đã thêm 14 câu, tổng ngân hàng 766 |
| Câu demo có prompt chung chung | 12/25 | **0/39** |
| Câu demo thiếu bối cảnh hoặc rubric đủ ba Level | 25/25 | **0/39**; bản nháp AI phải được duyệt |
| Sales template/chưa rà nội dung | 3/5 | **0 template**; 8/8 câu Sales là bản nháp chưa duyệt |
| ID học liệu demo thiếu bài/chương và locator | 52/53 ID tại baseline | **24/53 ID** còn thiếu sau khi mở và ghi phạm vi 29 ID |
| Mapping không được đề xuất | 216 | **216 được giữ để audit và loại khỏi đề xuất**: 175 unsuitable, 41 blocked |

Script biên tập câu hỏi có dry-run, backup theo hash và chạy lại cho kết quả 0 thay đổi: `scripts/complete_demo_questions.py`. Metadata review cũ của 22 câu bị sửa được giữ trong `prior_review_metadata`, còn trạng thái hiện hành hạ xuống `unreviewed`. Không dùng nhãn `reviewed` hoặc `ai_reviewed_internal` để thay cho người kiểm nội dung. Cổng câu hỏi và rubric của bốn nghề demo kiểm được 39/39 cặp Role–Skill–Level; [báo cáo audit hiện hành](demo-role-quality-current-2026-10-26.json) ghi từng ID.

Đã mở và đối chiếu nội dung công khai của 29 nguồn demo, ghi URL, bài/chương và giới hạn Level quan sát được trong [manifest nguồn](../reviews/demo-resource-page-checks-2026-10-26.json). Bảy link được thay bằng trang cụ thể hoặc bản ngôn ngữ có thể đọc được. Ví dụ tutorial Docker công bố 15 phút nên duration được ghi 0,25 giờ kèm nguồn; tài liệu không công bố thời lượng vẫn để `null`. Kiểm tra mở trang không tương đương xác nhận đúng Level, quyền tái sử dụng hay review chuyên gia. [Hàng đợi 76 lượt mapping demo](needs-human-resource.md) nêu việc còn thiếu theo từng nghề và kỹ năng.

Riêng ID cũ `css_dot03_vi` được giữ để không làm đứt tham chiếu, nhưng URL và `language` hiện là bản tiếng Anh chính thức của cùng module Microsoft Learn. Nguồn thời lượng vẫn là catalog publisher theo UID module; test chỉ cho phép URL khác locale khi hostname và đường dẫn module trùng chính xác. Không tính nguồn tiếng Anh này là học liệu tiếng Việt.

[Hàng đợi 216 mapping bị loại](excluded-resources-2026-10-26.md) phân loại theo ghi chú hiện có và giữ nguyên trạng thái chính sách. UI hiện phân biệt mức bằng chứng, thời lượng không rõ, câu phỏng vấn chưa duyệt và hiển thị cảnh báo với nghề pháp lý/y tế/kế toán/an toàn. Không tính nguồn bị loại thành học liệu đã phủ kỹ năng.

## Cổng kỹ thuật và cổng nội dung

| Cổng | Trạng thái | Cách hiểu |
| --- | --- | --- |
| Schema Role–Skill–Level v2 | PASS, 0 lỗi cấu trúc | Hợp lệ về kiểu dữ liệu, quan hệ và khóa bắt buộc |
| Câu hỏi demo đúng cặp, có context/rubric | PASS về hình thức, 39/39 | Chưa chứng minh độ đúng nghiệp vụ của rubric |
| Module paths toàn catalog | PASS, 131/131 role | Đường gọi lõi không lỗi trên dữ liệu catalog |
| Loại mapping unsuitable/blocked khỏi đề xuất | PASS trong test policy | 216 record còn nằm trong backlog audit |
| Evidence hoàn chỉnh cho demo | PENDING | 39 câu chưa được duyệt; 24/53 nguồn còn thiếu scope/locator và kiểm tra mở trang độc lập; 8/39 yêu cầu kỹ năng chưa có học liệu đủ điều kiện ở Level đích |
| Provenance và quyền dữ liệu | PENDING | 0 record trong inventory có đủ bảy trường bằng chứng; owner cần chọn license và căn cứ quyền |
| Xác nhận link của chủ dự án | STALE | 166 URL hiện tại; xác nhận trước đây gắn với tập 165 URL, trước khi thay bảy trang |

`--strict`, `--require-complete-evidence`, `--require-provenance` và `--require-current-link-attestation` cần tiếp tục trả mã lỗi cho đến khi từng thiếu hụt được xử lý bằng chứng thật. Test thường có bốn `xfail` cho bốn nghề demo về **review nội dung**; đó không phải bốn PASS. Các chỉ số và thiếu hụt chi tiết ở [audit demo](demo-role-quality-current-2026-10-26.json), [schema demo](demo-evidence-current-2026-10-26.json) và [inventory toàn catalog](data-readiness-2026-10-26.json).

## Việc còn cần owner và người rà chuyên môn

1. Duyệt 39 câu demo theo từng role–skill–Level, kiểm tình huống, đáp án tham khảo, rubric và red flags; ghi người/ngày/căn cứ. Chỉ đổi nhãn sau khi đã đọc và sửa nội dung cụ thể.
2. Xử lý 24 ID nguồn demo còn thiếu scope/locator hoặc kiểm tra truy cập độc lập; thay nguồn không đúng phạm vi. Bổ sung học liệu Level đích cho 8 yêu cầu còn thiếu, hoặc ghi rõ đường thực hành có quan sát/phản hồi đối với kỹ năng mềm. Không suy Level 3 từ bài nhập môn.
3. Chủ dự án xác nhận lại tập 166 URL **sau** thay đổi và chọn quyền/license cho dữ liệu tự biên soạn, nguồn thứ ba và tài sản. Link mở được chỉ là trục truy cập, không xác nhận quyền hay nội dung.
4. Sau khi bốn nghề demo đạt cổng nội dung, mở backlog ngoài demo theo độ rủi ro: 428 cặp role–skill chưa có câu hỏi, 59 câu hỏi chung chung, 727 câu ngoài demo thiếu bối cảnh/rubric theo snapshot hiện hành. Các nghề thuế, lao động, an toàn, y tế cần nguồn đúng phạm vi Việt Nam và người rà đúng chuyên môn.

Phần giao diện có thể tiếp tục trên trạng thái hiện tại vì luồng local và cổng kỹ thuật đã kiểm thử. Các badge/cảnh báo trên giao diện phải giữ nguyên ý nghĩa evidence pending; không diễn đạt bản nháp là học liệu hoặc câu hỏi đã được chứng thực.

## Kết quả chạy local cuối đợt

- `pytest -q --no-cov tests browser_tests`: **492 passed, 4 xfailed**; trong đó có 6 bài Chromium local. Bốn `xfail` là bốn nghề demo chưa đạt cổng review nội dung; không phải lỗi runtime bị che.
- `scripts/smoke.py` PASS với role `data_analyst`; validator ngân hàng: 766 câu, 0 lỗi toàn vẹn.
- Kiểm thử đường đi lõi: **131/131 role** qua presence match, gap, hai loại lộ trình, chọn câu và hướng dẫn trả lời. Migration `--check`: 0 file cần đổi; `git diff --check`: exit 0.
- Ba cổng nghiêm ngặt về chất lượng demo, evidence hoàn chỉnh và attestation link đều trả **exit 1 đúng backlog**. Cổng schema cấu trúc riêng vẫn PASS.
- Gói nguồn ứng viên `0.4.0-candidate` được tạo local với **166 file** trong ZIP và tar.gz; test manifest/checksum và loại dữ liệu riêng tư đạt. Giải nén ZIP sang thư mục tạm rồi chạy `scripts/smoke.py` từ đúng gói cũng PASS. Đây không phải bản phát hành được chấp thuận.

GitHub được đối chiếu chỉ đọc: remote `main` ở `8827a81f`, remote `Nhanh-Linh` ở `79e08217` tại thời điểm kiểm tra; checkout local `Nhanh-Linh` ở `b67cb26` và có nhiều thay đổi chưa commit, gồm cả phần việc trước đợt này. Chưa push hoặc đổi nhánh; muốn phản ánh sửa đổi lên GitHub phải rà phạm vi diff, commit và chạy CI trên commit đó.

## Tái lập

```powershell
$py = 'D:\Linh\.venvs\ai-career-coach-py312\Scripts\python.exe'
& $py -m pytest -q
& $py scripts\validate_question_bank.py
& $py scripts\audit_demo_role_quality.py --as-of 2026-10-26 --strict
& $py scripts\validate_evidence_schema.py --as-of 2026-10-26 --target-roles sales_executive,frontend_developer_react,data_analyst,backend_developer_java --require-complete-evidence
& $py scripts\audit_data_readiness.py --as-of 2026-10-26 --require-current-link-attestation
& $py scripts\audit_module_paths.py --as-of 2026-10-26
```

Các lệnh strict ở giữa dự kiến trả mã lỗi do backlog đã ghi, nên chạy riêng từng lệnh khi nghiệm thu. `dist/` chỉ chứa backup và gói nguồn ứng viên local, không phải bản phát hành công khai.
