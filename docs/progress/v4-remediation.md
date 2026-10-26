# Kết quả kiểm thử và khắc phục web local — 2026-10-25

## Phạm vi làm việc

- Làm trên working tree hiện có của nhánh Nhanh-Linh; không đổi nhánh, reset, commit hoặc push.
- Ứng dụng được kiểm tra như website desktop chạy local. Không kiểm thử hoặc tối ưu luồng app mobile.
- Giữ các thay đổi dữ liệu/code đã có trong working tree; chỉ cập nhật phần cần cho yêu cầu này.

## Đã khắc phục

### Phỏng vấn

- Đã bỏ hoàn toàn khớp cụm từ và điểm số tự động. Ngân hàng chưa đủ câu đã review để chấm tin cậy; phần tự rà soát hiện là checklist cho người dùng, không cộng thành điểm.
- Sau khi gửi câu trả lời, giao diện mới hiện đáp án/khung tham khảo. Câu review nội bộ có nguồn được hiển thị; câu template/chưa review có cảnh báo riêng. Tình huống mềm chấp nhận nhiều cách giải quyết và đề nghị dùng trải nghiệm thật.
- Bộ câu hỏi ưu tiên kỹ năng đang thiếu, giữ ID không lặp và giới hạn số lượng ở min(10, số câu có thật của role).
- Audit hiện có 752 câu trên 131 role: 6 câu review nội bộ kèm nguồn/ngày/ghi chú, 16 câu AI hỗ trợ rà soát trong ba role demo, 3 template, 727 câu chưa review. AI hỗ trợ và review nội bộ không phải thẩm định độc lập.

### Kỹ năng mềm và sales

- Lộ trình weekly/timed có tuyến luyện qua tình huống, công việc có giám sát, role-play, phản hồi và bằng chứng đã ẩn danh.
- Sales tập trung vào xác định nhu cầu, hỏi làm rõ, phản hồi bằng thông tin kiểm chứng, chốt bước tiếp theo và xem lại kết quả; không đánh đồng kỹ năng với tỷ lệ chốt.
- Khóa học vẫn hỗ trợ kiến thức sản phẩm/công cụ, nhưng không bắt buộc để được thực hành kỹ năng mềm hoặc trait.

### Học liệu và nguồn dữ liệu

- Catalog hiện có 471 record trên 165 URL. Trạng thái: 55 reviewed, 200 partial, 175 unsuitable, 41 blocked, 0 unreviewed.
- Có 255 mapping trên 150 URL đủ điều kiện gợi ý: URL đã xác minh, nội dung reviewed/partial và có ghi chú phạm vi. Partial luôn phải hiện hạn chế.
- Đợt cuối mở và đối chiếu 80 trang cho đủ 187 mapping cũ: 126 partial, 49 unsuitable, 12 blocked. Record bị loại vẫn được giữ để truy vết; không dựa riêng vào tên/domain hoặc HTTP.
- Bổ sung/đối chiếu thêm nguồn chính thức cho Java (Dev.java), Tableau, SEO (Google Search Central), thống kê nhập môn, tồn kho, phân tích tài chính (OpenStax), phân tích yêu cầu (IIBA), quantity takeoff (Autodesk), kiến trúc phần mềm (SEI) và sổ tay an toàn lao động nhập môn PAOT (ILO). Đây đều là nguồn partial do giới hạn cấp độ, nền tảng hoặc bối cảnh.
- Các kỹ năng cứng khác đã có nguồn cụ thể như JavaScript, React, TypeScript, ML, Kubernetes, PyTorch, C#, networking basics, data warehouse/ETL, Power BI, budgeting; các nguồn partial vẫn hiện phạm vi và điều kiện.
- Không lấy văn bản pháp luật làm khóa học an toàn lao động. Sổ tay PAOT ILO chỉ hỗ trợ phương pháp thực hành nhập môn, không thay yêu cầu pháp lý/khóa huấn luyện đủ điều kiện. Thuế và kế toán Việt Nam cần nguồn hiện hành, còn văn bản lao động hợp nhất mới chỉ xác minh metadata.
- Thuế và luật lao động vẫn `blocked` do cần đối chiếu nguồn pháp lý hiện hành và phạm vi áp dụng; chưa bật gợi ý tư vấn. Luật VAT hợp nhất tháng 02/2026 đã có sửa đổi tháng 04/2026; metadata văn bản lao động chưa thay cho review toàn văn.
- Kiểm kê và từng quyết định: [resource-review-2026-10-25.md](../reports/resource-review-2026-10-25.md) và [JSON](../reports/resource-review-2026-10-25.json).

## Kết quả kiểm thử

### Full test suite

Lệnh chạy trên venv sạch CPython 3.12.15: `python -m pytest --basetemp=D:\Linh\.pytesttmp-clean-install --cov=app --cov=modules --cov-report=term-missing`

Kết quả cuối sau khi sửa các assertion cũ để khớp hợp đồng xác thực CV và checklist phỏng vấn: **429 passed trong 156,59 giây, coverage tổng 91%**. Bao gồm logic, kiểm tra dữ liệu, parser/upload PDF/DOCX, export và Streamlit AppTest cho hồ sơ, CV/JD, kỹ năng nhập sai/alias, role, roadmap, học liệu, phỏng vấn, giới hạn số câu và reset state.

### Thao tác trên browser desktop local

- Trang home và health endpoint trả HTTP 200.
- Gửi hồ sơ trống hiển thị cảnh báo cần kỹ năng hoặc CV hợp lệ; không nhảy sang kết quả rỗng.
- Nhập `postgress` hiện gợi ý `postgresql`; chỉ chuyển canonical sau khi người dùng chọn. Kỹ năng lạ `CustomSkill` vẫn có thể giữ lại nhưng không được tính vào role fit hay học liệu.
- Chỉ nhập phần kinh nghiệm có Python/SQL vẫn tạo được bước review; kết quả hiện nguồn kỹ năng và yêu cầu người dùng xác nhận. Hệ thống không suy thâm niên hoặc level.
- Dán CV giả lập kèm kỹ năng, sở thích, kinh nghiệm và JD 4 kỹ năng cho kết quả trùng 50.0%; matched là Python/SQL, missing là Tableau/Excel.
- Sở thích Data Analyst xuất hiện ở lý do gợi ý role. Interest chỉ tác động điểm gợi ý khám phá, không làm tăng phần trăm đối chiếu kỹ năng riêng.
- Hồ sơ mẫu tổng hợp Kinh doanh đi qua bước rà soát và tạo kết quả cho Sales Executive.
- Data Analyst tạo được sơ đồ bốn tuần dạng thẻ nối mũi tên; Sales tạo route thực hành cho tìm kiếm khách hàng, teamwork, problem solving và time management.
- Data Analyst tạo đúng sáu câu khi role có sáu câu trong ngân hàng; UI báo không chấm điểm tự động. Các bài test khác xác nhận cận số câu và trạng thái gửi/trả lời.
- Browser test ngày 2026-10-25: DOM đặt `lang="vi"`; Tab đi qua Về công cụ → Cách hoạt động → Bắt đầu ngay, Enter mở phần hồ sơ và Space kích hoạt hồ sơ mẫu Backend Java. Mẫu đi hết bước xác nhận và hiển thị kết quả/lộ trình/học liệu/câu hỏi. Gửi câu trả lời giả lập cho thấy khung tham khảo và checklist, không có điểm; giao diện nói rõ checklist tĩnh không được suy ra từ câu trả lời.
- Dùng dữ liệu tổng hợp/giả lập, không tải CV cá nhân lên browser.

### Các cổng đo nhanh

- `scripts/smoke.py`: PASS trong 0,864 giây ở lượt xác minh cuối; role `data_analyst`, 1 phase, 3 câu hỏi.
- `tests/test_recommendation_quality.py`: 23 hồ sơ; Hit@3 100%, MRR 0,949, Forbidden@3 0%.
- `scripts/validate_question_bank.py`: 752 câu / 131 role, 0 lỗi toàn vẹn.
- `scripts/generate_resource_matrix.py`: 416 kỹ năng × 3 level, 1.248 dòng; 89 reviewed, 408 partial, 751 none.
- Streamlit loopback `127.0.0.1:8501/_stcore/health`: HTTP 200 / `ok`; log startup chỉ có URL và `Uvicorn server started`.
- Kích thước mã nguồn + dữ liệu (bỏ `.git`, venv, cache): 18,6 MB / 417 file. `site-packages` của venv test: 311,0 MB; bảy thư mục runtime lớn nhất đã đo chiếm 240,0 MB, nên mục tiêu strict <150 MB cho môi trường cài chưa đạt.

## Kiểm tra integrity hiện tại

Audit offline: 0 lỗi; 5 warning thuộc vocabulary nhận diện độc lập chưa có tài liệu: .net core, english, google tag manager, mysql, pandas. Đây không phải skill bắt buộc của 410 role. Question data có câu cho 131/131 role, mỗi role có 5–7 câu.

## Việc còn lại trước khi gọi là hoàn thiện dữ liệu

- 0 mapping resource còn `unreviewed`; 12 nguồn bị `blocked` có thể xem lại khi có trang/khóa cụ thể truy cập được. Các mapping partial cần phản hồi của chuyên gia/người dùng và thực hành theo bối cảnh nghề.
- 727 câu phỏng vấn chưa được review; 3 template cũng không phải đáp án đã thẩm định. Muốn mở rộng đáp án tham khảo cần review nội dung theo từng role/skill và lưu nguồn.
- Quantity takeoff, quản lý tồn kho, phân tích yêu cầu, phân tích tài chính và PAOT an toàn lao động đã có nguồn nền tảng partial. Kiến trúc hệ thống rộng hơn phần mềm, kế toán thuế/lao động và huấn luyện an toàn đủ điều kiện tại Việt Nam còn cần review nguồn chuyên biệt; các nguồn partial vẫn cần thực hành theo bối cảnh nghề.
- Chưa có review độc lập từ chuyên gia nghề nghiệp; chưa nghiệm thu CI remote, Docker, quyền phân phối toàn bộ dataset/brand, hỗ trợ bàn phím/screen reader hoặc kiểm thử screenshot hồi quy.
- Bản này xác nhận web chạy và các luồng đã thử trong local; không phải tuyên bố release/production ready.

Chi tiết học liệu và nguồn: docs/reports/resource-audit-2026-10-25.md cùng snapshot JSON kế bên. Hợp đồng phỏng vấn: docs/assessment_contract.md.
