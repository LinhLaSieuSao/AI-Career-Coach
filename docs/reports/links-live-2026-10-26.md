# Kiểm tra khả dụng URL học liệu — 26-10-2026

Bài kiểm tra GET công khai, timeout 3 giây, 8 luồng, tối đa 5 redirect; chỉ đọc mẫu HTML tối đa 8 KiB. Đây là tình trạng truy cập của máy kiểm tra tại một thời điểm, **không** là review nội dung, quyền sử dụng hoặc độ phù hợp học liệu.

**Bổ sung sau kiểm tra thủ công:** Ngày 26-10, người dùng dự án cho biết đã mở toàn bộ link học liệu trong catalog, kể cả nhóm không hiện trong bảng dưới, và thấy các link tới nguồn gốc có nội dung. [Bản ghi xác nhận tập 165 URL](../../Data/link_review_attestation.json) giữ lời báo đó cùng dấu vân tay tập URL. Vì vậy các dòng `blocked`/`timeout` dưới đây là **kết quả HTTP của máy kiểm tra/bot**, không là kết luận rằng người dùng không mở được. Lời báo không xác minh mapping skill–Level, tính cập nhật chuyên ngành hoặc quyền tái sử dụng.

| Kết quả | Số URL |
| --- | ---: |
| blocked | 20 |
| reachable | 91 |
| redirect | 47 |
| timeout | 7 |

Tổng 165 URL; 42 mapping đang đủ điều kiện gợi ý trên 40 kỹ năng dùng 27 URL `blocked`/`timeout`. Nhóm `blocked` thường là HTTP 403 hoặc chặn bot; không tự gắn là link chết. Nhóm `timeout` cần thử lại bằng trình duyệt/ngày khác. Danh sách máy đọc đầy đủ: [JSON](links-live-2026-10-26.json).

| URL cần kiểm tra tay | Trạng thái | HTTP | Mapping đủ điều kiện | Kỹ năng bị ảnh hưởng |
| --- | --- | ---: | ---: | --- |
| [arena.fpt.edu.vn](https://arena.fpt.edu.vn/nguyen-tac-thiet-ke-ui-ux-ban-nen-biet/) | timeout | — | 1 | thiết kế ui ux |
| [asq.org](https://asq.org/quality-resources/continuous-improvement) | blocked | 403 | 1 | kaizen |
| [asq.org](https://asq.org/quality-resources/eight-disciplines-8d) | blocked | 403 | 1 | quy trình 8d |
| [asq.org](https://asq.org/quality-resources/five-s-tutorial) | blocked | 403 | 1 | 5s |
| [asq.org](https://asq.org/quality-resources/flowchart) | blocked | 403 | 1 | vẽ quy trình |
| [asq.org](https://asq.org/quality-resources/fmea) | blocked | 403 | 1 | fmea |
| [asq.org](https://asq.org/quality-resources/iso-9001) | blocked | 403 | 1 | iso 9001 |
| [asq.org](https://asq.org/quality-resources/lean) | blocked | 403 | 1 | lean manufacturing |
| [asq.org](https://asq.org/quality-resources/quality-assurance-vs-control) | blocked | 403 | 1 | kiểm soát chất lượng |
| [asq.org](https://asq.org/quality-resources/seven-basic-quality-tools) | blocked | 403 | 1 | 7 công cụ qc |
| [creativecloud.adobe.com](https://creativecloud.adobe.com/learn) | blocked | 403 | 6 | adobe after effects, adobe illustrator, adobe photoshop, adobe premiere, adobe premiere pro, biên tập video |
| [docs.opencv.org](https://docs.opencv.org/4.x/d9/df8/tutorial_root.html) | blocked | 403 | 2 | computer vision, opencv |
| [huggingface.co](https://huggingface.co/learn/llm-course/chapter1/1) | blocked | 200 | 1 | transformer |
| [learnenglish.britishcouncil.org](https://learnenglish.britishcouncil.org/) | timeout | — | 3 | ielts preparation, tiếng anh cơ bản, tiếng anh giao tiếp |
| [vbpl.vn](https://vbpl.vn/) | timeout | — | 0 | — |
| [www.autodesk.com](https://www.autodesk.com/learn/catalog/start) | blocked | 403 | 0 | — |
| [www.autodesk.com](https://www.autodesk.com/learning.autodesk) | blocked | 403 | 3 | autocad, revit architecture, revit mep |
| [www.britishcouncil.vn](https://www.britishcouncil.vn/hoc-tieng-anh/tieng-anh-nguoi-lon/kinh-nghiem/5-quy-tac-viet-thu-tin) | timeout | — | 2 | cẩn thận, tiếng anh chuyên ngành |
| [www.britishcouncil.vn](https://www.britishcouncil.vn/hoc-tieng-anh/tieng-anh-nguoi-lon/kinh-nghiem/muoi-cach-chao-hoi-bang-tieng-anh-how-are-you) | timeout | — | 1 | tiếng anh giao tiếp |
| [www.canva.com](https://www.canva.com/design-school/) | blocked | 403 | 1 | canva |
| [www.canva.com](https://www.canva.com/designschool/) | blocked | 403 | 3 | canva, layout design, thiết kế cơ bản |
| [www.capcut.com](https://www.capcut.com/resource/capcut-tutorial-for-beginners) | timeout | — | 2 | capcut, quay dựng video |
| [www.kaggle.com](https://www.kaggle.com/learn) | blocked | 200 | 2 | phân tích dữ liệu, thuật toán học máy |
| [www.pace.edu.vn](https://www.pace.edu.vn/tin-kho-tri-thuc/ky-nang-giai-quyet-van-de) | blocked | 200 | 1 | giải quyết vấn đề |
| [www.pace.edu.vn](https://www.pace.edu.vn/tin-kho-tri-thuc/ky-nang-phan-tich) | blocked | 200 | 1 | tư duy phân tích |
| [www.tableau.com](https://www.tableau.com/learn/training) | blocked | 403 | 1 | tableau |
| [www.teachingenglish.org.uk](https://www.teachingenglish.org.uk/teaching-resources) | timeout | — | 3 | kỹ năng giảng dạy, quản lý lớp học, soạn giáo án |

Ưu tiên kiểm tra tay các URL có mapping đủ điều kiện. Nếu nội dung không mở được cho người dùng local hoặc nội dung/phạm vi thay đổi, thay URL hoặc hạ trạng thái mapping với ghi chú và ngày kiểm tra. Không sửa `verified` chỉ từ phản hồi bot và không nâng `partial` chỉ vì HTTP 200.
