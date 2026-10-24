# Kịch bản demo local

Ba hồ sơ trong `Data/demo_profiles.json` là dữ liệu tổng hợp. Chúng dùng ba role thật `backend_developer_java`, `data_analyst`, `sales_executive` và skill thật từ catalog. Experience ghi rõ là ví dụ, không tạo danh tính hay lịch sử tuyển dụng.

## Kịch bản khoảng 7 phút

1. **Mở app (30 giây):** giới thiệu đây là công cụ rule-based chạy local; chỉ rõ nhãn “Minh họa tổng hợp” trên thẻ landing.
2. **Backend Java (2 phút):** chọn “Dùng hồ sơ mẫu · Backend Java”; xem level khai báo, đổi giữa presence và level. Nói rõ CV không suy ra level; xác nhận `current=0` cho skill chưa khai báo chỉ là quy ước phép tính.
3. **Khoảng cách/lộ trình (1 phút):** chỉ ra match/gap, ngân sách 8 giờ/tuần và những phần thời lượng hoặc review chưa đủ để xác định tổng tuần. Không gọi giờ resource là thời gian đạt nghề.
4. **Tài liệu/export (1 phút):** mở nguồn duration/provenance, tải Markdown hoặc CSV; nhắc CSV escape chuỗi có dạng công thức.
5. **Data Analyst (1 phút):** dùng hồ sơ mẫu Data Analyst, cho thấy kỹ năng chung như SQL được đối chiếu với role catalog và tài liệu dùng chung không bị cộng lặp.
6. **Sales (1 phút):** dùng hồ sơ Sales, nêu gợi ý role là điểm heuristic có lý do, không phải xác suất tuyển dụng.
7. **Phỏng vấn (1 phút):** tạo câu hỏi theo gap, gửi câu trả lời tổng hợp, phân biệt câu có rubric đã review với câu chưa chấm.

## Outline slide

1. Vấn đề: kỹ năng, yêu cầu role và nguồn học bị rời rạc.
2. Luồng local: CV/form → Profile → Matcher/Recommender.
3. Phân biệt presence, level gap và gợi ý heuristic.
4. Chất lượng dữ liệu: resource duration/review và rubric chưa đầy đủ.
5. Demo ba hồ sơ tổng hợp và export.
6. Giới hạn, license/provenance cần xác nhận và bước tiếp theo.

## Lời dẫn video (bản đọc, chưa ghi hình)

“Đây là AI Career Coach chạy local. Tôi bắt đầu bằng một hồ sơ tổng hợp Backend Java, không phải người thật. Điểm presence cho biết các kỹ năng được nhận diện trong hồ sơ khớp với trọng số role như thế nào. Khi chuyển sang level, app chỉ dùng những mức người dùng đã khai báo và yêu cầu xác nhận trước khi coi level còn thiếu là 0. Lộ trình tách giờ nhà xuất bản khỏi ước lượng và giữ tổng tuần chưa xác định khi dữ liệu chưa đủ. Tài liệu có thể được mở cùng nguồn căn cứ. Bộ câu hỏi ưu tiên gap; rubric chỉ chấm một tập nhỏ đã review, còn câu khác hiển thị chưa có điểm. Điểm gợi ý role và điểm rubric không phải dự đoán tuyển dụng. Có thể tải báo cáo Markdown hoặc CSV mà không xuất toàn văn CV.”

Slide deck, video và screenshot chưa được tạo trong đợt này. Trình duyệt local bị origin approval gate từ chối trong phiên hiện tại; AppTest vẫn chạy được nhưng không thay thế kiểm tra trực quan.
