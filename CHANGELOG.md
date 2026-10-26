# Changelog

Thay đổi quan trọng của dự án được ghi theo mốc. `pyproject.toml` khai báo 0.4.0 để chuẩn bị gói ứng viên local; chưa có tag/release công khai.

## 26-10-2026 — hoàn thiện bản nháp dữ liệu demo và nhãn bằng chứng

- Thay 3 template Sales và thêm 14 câu đúng Role×Skill; 39/39 cặp ở bốn nghề demo có câu với bối cảnh, rubric L1–L3 và đáp án tham khảo. 22 câu có review metadata cũ được hạ về `unreviewed` sau khi bổ sung rubric AI, giữ metadata cũ trong lịch sử; toàn ngân hàng 766 câu, 0 template, 766 chờ duyệt nội dung hiện hành.
- Đối chiếu độc lập 29 trang nguồn học liệu, ghi bài/chương và locator đúng phạm vi; thay 7 URL sang trang cụ thể hoặc bản ngôn ngữ đọc được, thu hẹp Level khi nguồn không hỗ trợ mức cao. 216 mapping unsuitable/blocked được xuất thành hàng đợi có lý do và tiếp tục bị loại khỏi đề xuất.
- Thêm nhãn bằng chứng theo trục yếu nhất, cảnh báo nghề rủi ro cao và cổng schema theo bốn nghề demo. Attestation thủ công cũ trở thành stale sau thay URL; không tự gia hạn thay cho người dùng.

## 26-10-2026 — nghiệm thu lại B3/PoF và sửa ca dùng thực tế

- Kiểm tra GitHub công khai: `main` có CI Python/Docker thành công, Issues/Discussions bật; chưa có tag/release. Báo cáo cũ coi thiếu website/kênh công khai và ước lượng 125 PoF đã được thay bằng [ma trận có nguồn](docs/verification/b3-pof-gap-matrix.md).
- Bước rà soát kỹ năng cho phép nhập skill mới rồi chọn Level trước khi xác nhận; gộp tên/alias trùng để không phát sinh `StreamlitDuplicateElementKey`. Trích xuất loại một số khẳng định phủ định rõ như “chưa sử dụng Docker”; ca ngôn ngữ mơ hồ vẫn cần người dùng xác nhận.
- Tab Tài liệu và Markdown export gọi lộ trình presence là giai đoạn, không nhầm thành cam kết tuần. Thông báo riêng tư nói rõ kết quả phiên không tự khôi phục, có nút xóa hồ sơ phiên.
- Docker cài runtime từ lock có hash. CI thêm browser Chromium/axe và inventory cấu trúc; browser job không được skip khi thiếu Chromium. Chuẩn bị script gói nguồn ZIP/tar.gz có manifest/checksum, không xuất bản.
- Inventory dữ liệu tái lập: 471 mapping (255 đủ điều kiện); 752 câu hỏi (6 review nội bộ, 16 AI hỗ trợ, 3 template, 727 unreviewed); sau khi rà chín mapping Level quá rộng, 760/1.248 ô skill×level chưa có học liệu đủ điều kiện. Metadata provenance/quyền theo record còn thiếu và cần owner xác minh.
- Inventory nay đo thêm 1.192 cặp nghề–kỹ năng: 750 có câu hỏi, 674 có học liệu đúng Level yêu cầu. Xác nhận mở 165 URL do người dùng báo được lưu riêng và gắn fingerprint; CI phát hiện khi tập URL đổi. 131/131 nghề đã đi qua matcher, gap, hai lộ trình và phỏng vấn bằng hồ sơ tổng hợp.
- Kiểm tra 165 URL học liệu: 91 reachable, 47 redirect, 20 bị chặn bot/HTTP và 7 timeout. Không tự thay đổi cờ verified hay mức review chỉ từ HTTP.
- Cổng kiểm thử local sau vòng review dữ liệu: 470/470 core/AppTest, 5/5 Chromium browser; smoke, validator và golden benchmark qua ở lượt trước. Axe không còn critical/serious, còn 2 minor trong dropzone file uploader của Streamlit. Gói ZIP candidate được đóng gói lại và chạy smoke, validator, inventory từ source giải nén bằng venv runtime đã cài sạch ở lượt trước.

Các số 385 test, 470 mapping và 12 template ở những mốc dưới là **snapshot lịch sử**, xem inventory ngày 26-10 để quyết định trên bản hiện tại.

## Đang làm — xử lý kế hoạch v4.0

- Thêm chính sách học liệu dùng chung cho weekly/timed roadmap: chỉ mapping có trạng thái review phù hợp, ghi chú phạm vi và link đã xác minh mới được khuyến nghị; unresolved nêu lý do.
- Giới hạn upload CV ở 10 MiB và trích tối đa 10 trang PDF; trả metadata cắt trang để giao diện cảnh báo.
- Thay nhập Level JSON bằng wizard hai bước để rà soát kỹ năng, xác nhận kỹ năng từ JD và tự khai báo Level theo control native.
- Bỏ hoàn toàn bộ chấm phỏng vấn theo cụm từ; chỉ hiện gợi ý sau khi gửi câu trả lời, cảnh báo nội dung chưa review và checklist tự phản tư không tính điểm.
- Cập nhật hợp đồng giao diện, parser, matcher, recommender và giới hạn bảo mật để phản ánh hành vi mới.
- Sửa lỗi thiếu import trong timed planner và giữ cảnh báo CV/JD sau xác nhận hồ sơ; báo rõ khi bản gửi mới bị từ chối nhưng hồ sơ cũ còn hiển thị.
- Bổ sung thông báo khi JD không còn kỹ năng được xác nhận, giữ cảnh báo PDF bị cắt trang sau khi xác nhận, và báo số câu phỏng vấn có sẵn nếu ngân hàng không đủ số lượng yêu cầu.
- Full suite local gần nhất qua 385/385, gồm AppTest; trang và health endpoint local trả HTTP 200, các luồng hồ sơ Kinh doanh/phỏng vấn đã được thao tác trên browser desktop. Chạy lại toàn bộ sau đợt bổ sung nguồn hiện tại.
- Screenshot/layout, CI remote, Docker, quyền/provenance dữ liệu và release gate chưa được nghiệm thu.

## Cập nhật xử lý dữ liệu phỏng vấn và lộ trình

- Giới hạn lựa chọn câu phỏng vấn theo số bản ghi hợp lệ của role (tối đa 10); không cho yêu cầu vượt số dữ liệu có sẵn.
- Chuyển ngày, ghi chú và nguồn review của 6 câu đã được review nội bộ vào từng câu hỏi; xóa bộ rubric khớp cụm và API chấm điểm.
- Đánh dấu trạng thái review trong báo cáo chất lượng: 6 đã review nội bộ, 12 template, 734 chưa review.
- Thêm 8 học liệu có nguồn chính thức cho JavaScript, React, TypeScript, machine learning, Kubernetes, CRM, CI/CD và PyTorch; review thêm Scrum Guide và Google Skillshop.
- Bổ sung nguồn chính thức cho C#, Tableau, Canva, Figma, networking basics, Fabric data warehouse, Azure Data Factory, AWS Well-Architected, Java, SEO, thống kê, tồn kho, phân tích yêu cầu, phân tích tài chính, quantity takeoff, kiến trúc phần mềm và sổ tay PAOT cho OSH nhập môn; ghi rõ `partial` khi giới hạn ở nền tảng hoặc kiến thức nhập môn.
- Thêm lộ trình luyện giao tiếp, bán hàng, xử lý tình huống và traits qua nhiệm vụ thực tế, quan sát/mentor và phản hồi; khóa học không còn là điều kiện để lập kế hoạch kỹ năng mềm.
- Ghi snapshot mới: 470 resource record, 128 record đủ điều kiện đề xuất; 187 mapping chưa review vẫn bị loại khỏi gợi ý.

## Đợt 5 — chưa phát hành

- Tổ chức kết quả Streamlit thành năm tab và thêm notice khi hồ sơ được cập nhật.
- Thêm export Markdown/CSV có bảo vệ CSV formula injection và không xuất toàn văn CV.
- Thêm ba hồ sơ demo tổng hợp gắn với role/skill catalog.
- Tách runtime/dev dependencies; thêm coverage và Docker healthcheck vào CI.
- Bổ sung hướng dẫn chạy, kiến trúc, demo, đóng góp, checklist PoF và kiểm kê license.
- Gỡ nội dung cộng đồng không có kênh đã xác minh và số minh họa có thể bị hiểu là kết quả.
