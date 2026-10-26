# Kịch bản demo local

Ba hồ sơ trong `Data/demo_profiles.json` là dữ liệu tổng hợp. Chúng dùng ba role thật `backend_developer_java`, `data_analyst`, `sales_executive` và skill thật từ catalog. Experience ghi rõ là ví dụ, không tạo danh tính hay lịch sử tuyển dụng.

## Kịch bản khoảng 7 phút

1. **Mở app (30 giây):** giới thiệu đây là công cụ rule-based chạy local; chỉ rõ nhãn “Minh họa tổng hợp” trên thẻ landing.
2. **Backend Java (2 phút):** chọn “Dùng hồ sơ mẫu · Backend Java”; xem level khai báo, đổi giữa presence và level. Nói rõ CV không suy ra level; xác nhận `current=0` cho skill chưa khai báo chỉ là quy ước phép tính.
3. **Khoảng cách/lộ trình (1 phút):** chỉ ra match/gap, ngân sách 8 giờ/tuần và những phần thời lượng hoặc review chưa đủ để xác định tổng tuần. Không gọi giờ resource là thời gian đạt nghề.
4. **Tài liệu/export (1 phút):** mở nguồn duration/provenance, tải Markdown hoặc CSV; nhắc CSV escape chuỗi có dạng công thức.
5. **Data Analyst (1 phút):** dùng hồ sơ mẫu Data Analyst, cho thấy kỹ năng chung như SQL được đối chiếu với role catalog và tài liệu dùng chung không bị cộng lặp.
6. **Sales (1 phút):** dùng hồ sơ Sales, nêu gợi ý role là điểm heuristic có lý do, không phải xác suất tuyển dụng.
7. **Phỏng vấn (1 phút):** tạo câu hỏi theo gap, quan sát giới hạn đúng số câu của role, gửi câu trả lời tổng hợp; xem khung tham khảo sau khi gửi và chỉ ra cảnh báo với câu chưa review. App không tự chấm câu trả lời.

## Outline slide

1. Vấn đề: kỹ năng, yêu cầu role và nguồn học bị rời rạc.
2. Luồng local: CV/form → Profile → Matcher/Recommender.
3. Phân biệt presence, level gap và gợi ý heuristic.
4. Chất lượng dữ liệu: resource duration/review và mức review đáp án phỏng vấn còn hạn chế.
5. Demo ba hồ sơ tổng hợp và export.
6. Giới hạn, license/provenance cần xác nhận và bước tiếp theo.

## Lời dẫn video (bản đọc, chưa ghi hình)

“Đây là AI Career Coach chạy local. Tôi bắt đầu bằng một hồ sơ tổng hợp Backend Java, không phải người thật. Điểm presence cho biết các kỹ năng được nhận diện trong hồ sơ khớp với trọng số role như thế nào. Khi chuyển sang level, app chỉ dùng những mức người dùng đã khai báo và yêu cầu xác nhận trước khi coi level còn thiếu là 0. Lộ trình tách giờ nhà xuất bản khỏi ước lượng và giữ tổng tuần chưa xác định khi dữ liệu chưa đủ. Tài liệu có thể được mở cùng nguồn căn cứ, còn kỹ năng mềm có tuyến luyện qua tình huống và phản hồi. Bộ câu hỏi ưu tiên gap và chỉ hiện hướng dẫn sau khi gửi. App không tự chấm vì phần lớn câu hỏi chưa được review. Điểm gợi ý role không phải xác suất tuyển dụng. Có thể tải báo cáo Markdown hoặc CSV mà không xuất toàn văn CV.”

Slide deck, video và screenshot chưa được tạo trong đợt này. Đã chạy 385 test local và thao tác các luồng hồ sơ Kinh doanh/phỏng vấn trên browser desktop local. Chưa thực hiện kiểm tra pixel/layout bằng screenshot hoặc nghiệm thu accessibility độc lập.
