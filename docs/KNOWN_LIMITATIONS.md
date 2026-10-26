# Giới hạn đã biết

Tài liệu này mô tả giới hạn kỹ thuật và phạm vi xác minh hiện tại. Các kết quả của ứng dụng là công cụ định hướng; chúng không phải dự đoán tuyển dụng hay đánh giá chuyên môn của cá nhân.

## Hồ sơ, CV và gợi ý nghề

- PDF scan thuần ảnh chưa có OCR. Người dùng cần dán nội dung hoặc nhập kỹ năng; giới hạn PDF và hướng xử lý xem trong [`cv_parser.py`](../modules/cv_parser.py).
- Trích xuất kỹ năng dựa trên catalog/alias tĩnh. Một số câu phủ định rõ như “chưa sử dụng Docker” được loại khỏi bằng chứng, nhưng câu mơ hồ, phủ định phức tạp, thuật ngữ mới và viết tắt chưa có alias vẫn có thể nhận diện thiếu hoặc sai; người dùng cần rà soát trước khi xác nhận.
- Role-IDF, skill-gate và RIASEC là luật/heuristic có thể giải thích. Vector RIASEC tĩnh không phải trắc nghiệm Holland đã chuẩn hóa độc lập, không được kiểm định psychometric và không nên dùng để loại ứng viên.
- Golden benchmark dùng 23 hồ sơ tổng hợp do dự án xây dựng. Hit@3/MRR chỉ là regression cho các ví dụ này; không chứng minh độ chính xác, công bằng hay giá trị dự báo trong tuyển dụng thực tế.
- Kỹ năng profile là khai báo/được trích xuất rồi người dùng xác nhận; hệ thống không xác minh kinh nghiệm, trình độ hoặc năng lực thực hành.

## Học liệu và lộ trình

- [`resource-coverage-matrix.md`](resource-coverage-matrix.md) phản ánh mapping theo catalog × level, trạng thái review và link hiện có. Đây không phải đánh giá độc lập của chuyên gia.
- `partial` chỉ biểu thị phạm vi đã rà soát một phần; nó không bao phủ các level/outcome còn lại. Mục không có nguồn đủ điều kiện được hiển thị là chưa có tài liệu xác minh.
- Tập URL hiện có 166 đường dẫn sau khi 7 nguồn được thay bằng trang cụ thể hoặc bản ngôn ngữ đọc được. Lời xác nhận thủ công trước đó gắn với tập 165 URL cũ nên cổng `current_link_attestation` hiện là `stale_or_invalid`; chỉ người dùng có thể xác nhận lại tập mới. 29 nguồn demo đã được mở độc lập bằng trình đọc web, nhưng không đủ thay cho review nội dung và quyền sử dụng.
- Kỹ năng giao tiếp, bán hàng, làm việc nhóm và xử lý vấn đề cần role-play, nhiệm vụ thực tế có người giám sát và phản hồi; khóa học chỉ hỗ trợ. Thiếu khóa học không đồng nghĩa không thể luyện kỹ năng.
- Thuế, luật lao động, huấn luyện/chứng nhận an toàn tại Việt Nam và một số kỹ năng nghề rộng cần nguồn đúng thẩm quyền, phạm vi và chuyên gia phù hợp trước khi hệ thống tăng mức khẳng định.
- Thời lượng học chỉ được coi là xuất bản/xác minh khi có nguồn; ước tính có căn cứ và số giờ đã xác minh được báo cáo riêng.

## Phỏng vấn

- Ngân hàng có 766 câu thuộc 131 role: 0 template và 766 câu chờ duyệt nội dung hoàn chỉnh. Khi bổ sung bối cảnh/rubric AI cho bốn nghề demo, 22 câu có metadata review cũ được hạ về `unreviewed`; metadata cũ vẫn nằm trong `prior_review_metadata` để đối chiếu. Tính toàn vẹn máy không chứng minh tính đúng chuyên môn.
- Nhóm demo hiện tại dùng `data_analyst`, `frontend_developer_react` và `backend_developer_java`, vì catalog không có ID chung `frontend_developer` hoặc `software_engineer`.
- Phần được AI hỗ trợ rà soát có nhãn riêng và ghi rõ chưa được chuyên gia độc lập/owner xác nhận. Không có chấm điểm tự động câu trả lời; câu trả lời mẫu là gợi ý, không phải đáp án duy nhất.
- Câu hỏi tình huống/behavioral cần được gắn với phân tích công việc và rubric nhất quán của bên tuyển dụng trước khi dùng để ra quyết định tuyển chọn.

## Giao diện và triển khai

- App chỉ được thiết kế và kiểm tra cho chạy local bằng Streamlit. Chưa có cam kết về ứng dụng mobile-native, cloud, nhiều người dùng đồng thời hay lưu hồ sơ lâu dài.
- Mã nguồn và dữ liệu hiện khoảng 18.6 MB, nhưng môi trường Python cài dependencies kiểm chứng có `site-packages` 311 MB. Riêng các thư mục runtime `pyarrow`, `pandas`, `streamlit`, `pydeck`, `numpy`, `numpy.libs`, `PIL` đã chiếm khoảng 240 MB. Do đó ràng buộc <150 MB cho môi trường đã cài **chưa đạt**; muốn đạt cần thay đổi/giảm stack phụ thuộc và kiểm chứng lại. App không cài torch, sentence-transformers hoặc spaCy.
- Form dùng nhãn hiển thị/ARIA của Streamlit; `run_app()` đặt `document.documentElement.lang="vi"` bằng script tĩnh do mã nguồn kiểm soát. Local browser smoke đã kiểm tra bàn phím tới demo/kết quả; axe trên landing/kết quả từng ghi 0 critical/serious và 2 minor `presentation-role-conflict`. Screen reader, toàn bộ thứ tự focus, zoom trình duyệt thật và WCAG chưa được audit; không nên tuyên bố đạt chuẩn accessibility.
- Bằng chứng hiện tại là test automated/AppTest và thao tác browser local ở phạm vi nêu trong [`pof-checklist.md`](pof-checklist.md). Hành vi trên mọi browser, máy và dữ liệu ngoài mẫu cần được kiểm tra riêng.
- License/provenance của một số dữ liệu, tài liệu và tài sản thương hiệu vẫn cần chủ dự án xác nhận; xem [`LICENSES.md`](../LICENSES.md).
