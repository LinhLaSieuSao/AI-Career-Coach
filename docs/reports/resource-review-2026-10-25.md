# Rà soát 187 mapping học liệu chưa được review — 2026-10-25

## Kết quả

Đã mở và đối chiếu nội dung của 80 trang nguồn, rồi quyết định riêng cho từng mapping kỹ năng–học liệu. Tất cả **187/187 record `unreviewed` ban đầu đã được xử lý**:

| Quyết định | Số mapping | Xử lý trong ứng dụng |
| --- | ---: | --- |
| `partial` | 126 | Được gợi ý nếu URL đã xác minh và ghi rõ phần được hỗ trợ; UI phải hiển thị giới hạn. |
| `unsuitable` | 49 | Giữ record để truy vết, nhưng loại khỏi gợi ý vì trang không dạy kỹ năng được gắn. |
| `blocked` | 12 | Tạm loại khỏi gợi ý vì nội dung chưa truy cập/đối chiếu an toàn được. |
| **Còn `unreviewed` trong nhóm này** | **0** | — |

`Data/resources.json` lưu quyết định cho từng ID cùng `content_review_status`, ngày, ghi chú và locator bằng chứng. Danh sách đầy đủ, 80 trang đã kiểm tra, URL được thay và từng quyết định nằm trong [resource-review-2026-10-25.json](resource-review-2026-10-25.json). Một số trích dẫn/locator là mô tả tóm tắt bằng tiếng Việt, không phải trích nguyên văn toàn trang.

## Cách áp dụng vào gợi ý

- Chỉ record có trạng thái `reviewed`/`partial`, ghi chú phạm vi, URL hợp lệ và cờ URL đã xác minh mới vào danh sách roadmap. `partial` không có nghĩa đã đạt kỹ năng hay đủ cho vị trí.
- Đợt review cuối bổ sung 126 mapping partial. Sau khi hợp nhất các đợt trước, catalog hiện có 471 record trên 165 URL: 55 `reviewed`, 200 `partial`, 175 `unsuitable`, 41 `blocked`, 0 `unreviewed`.
- Theo chính sách ứng dụng hiện tại, có 255 mapping đủ điều kiện trên 150 URL. Nhiều mapping dùng chung một trang nên số URL thấp hơn số record. Cờ `verified=false` ở 216 record bao gồm mapping không phù hợp/bị chặn, không đồng nghĩa 216 liên kết đều chết.
- Năm mục vocabulary chỉ để nhận diện nhưng chưa có học liệu vẫn là warning: `.net core`, `english`, `google tag manager`, `mysql`, `pandas`. Không có mục nào trong 410 kỹ năng role bị thiếu hẳn đường dẫn resource trong integrity audit.

## Mẫu quyết định

| Mapping | Quyết định | Vì sao |
| --- | --- | --- |
| PostgreSQL → [PostgreSQL Tutorial](https://www.postgresql.org/docs/current/tutorial.html) | `partial` | Hướng dẫn chính thức nhập môn về truy vấn, join, aggregate và transaction; không bao quát quản trị/vận hành database. PostgreSQL được giữ riêng, không tự chuyển thành năng lực SQL tổng quát. |
| SQL → relational database course của freeCodeCamp | `partial` | Nội dung dạy relational database, PostgreSQL và SQL; không xác nhận mọi dialect hoặc mức production. |
| MongoDB → cùng khóa relational database | `unsuitable` | Trang không dạy MongoDB. |
| REST API → MDN Client-side APIs | `partial` | Dạy cách dùng Web API từ client/Fetch; không phải thiết kế API server-side. |
| Angular/TypeScript → MDN web-development tutorials | `unsuitable` | Nền HTML/CSS/JavaScript không chứng minh bài học Angular hoặc TypeScript chuyên biệt. |
| NLP → Hugging Face LLM course hiện tại | `unsuitable` | Liên kết hiện trỏ sang LLM course; không còn chứng minh khóa NLP tổng quát như mapping cũ. Transformer vẫn được ghi partial với phạm vi hẹp. |
| SEO → Google Search Essentials/Search Console | `partial` | Hỗ trợ nguyên tắc và dữ liệu trong hệ sinh thái Google; không bao quát SEO đa nền tảng hoặc bảo đảm thứ hạng. |
| OpenCV → Tutorials 4.x chính thức | `partial` | Có xử lý ảnh, hiệu chuẩn camera, detection và DNN; vẫn là một thư viện, không phải lộ trình thị giác máy tính đầy đủ. |
| Thương lượng → chương OpenStax về negotiation | `partial` | Cung cấp khung khái niệm; kỹ năng cần role-play, tình huống thực và phản hồi. |
| Tìm kiếm khách hàng → Microsoft Learn Dynamics 365 Sales | `partial` | Hướng dẫn lead/opportunity trong Dynamics; không phải phương pháp sales trung lập hoặc bằng chứng năng lực giao tiếp thực tế. |

## 12 mapping bị chặn

| Nhóm | Số mapping | Lý do |
| --- | ---: | --- |
| Thuế Việt Nam (`kế toán thuế`, `kê khai thuế`, `HTKK`, `thuế TNCN`) | 4 | Cổng thuế mở được nhưng không đối chiếu được trang hướng dẫn hiện hành cụ thể; các thay đổi luật 2026 cần văn bản hợp nhất/đối chiếu mới nhất. |
| Luật lao động | 1 | Xác nhận metadata của văn bản hợp nhất nhưng chưa đối chiếu toàn văn và sửa đổi sau ngày ban hành; không dùng làm gợi ý tư vấn pháp lý. |
| Meta Blueprint (`Facebook Ads`, `quản lý fanpage`, `Facebook`) | 3 | Trang yêu cầu đăng nhập/chặn lần review; chưa kiểm tra được khóa cụ thể. |
| VMware/Broadcom Learning | 1 | Trang tải động, không xác nhận được khóa VMware cụ thể. |
| YouTube Creator Academy (`kịch bản video`, `YouTube`, `sáng tạo kịch bản`) | 3 | URL chuyển tới channel chung thay vì một trang học Academy có nội dung xác định. |
| **Tổng** | **12** | Các mapping vẫn được giữ nhưng không được gợi ý. |

`blocked` mô tả mức độ bằng chứng truy cập/kiểm tra trong đợt này, không khẳng định nguồn chắc chắn không có nội dung. Có thể review lại nếu có URL/khóa học cụ thể và nguồn hiện hành.

## Phạm vi còn thiếu và việc tiếp theo

- Đã giải quyết hết 187 mapping resource, nhưng đây không phải review độc lập bởi chuyên gia nghề nghiệp/pháp lý.
- Ngân hàng phỏng vấn vẫn có 752 câu: 6 câu có review nội bộ, 12 template, 734 câu chưa được review. Đây là một backlog khác, không được tính vào 187 resource mapping.
- Với nghề cần giao tiếp, bán hàng, xử lý vấn đề và làm việc nhóm, khóa học chỉ bổ trợ. Lộ trình dùng mô phỏng/role-play, nhiệm vụ có người giám sát, phản hồi từ mentor/đồng nghiệp và bằng chứng thực tế; thiếu khóa học không chặn thực hành.
- Học liệu partial vẫn cần portfolio/bài tập theo bối cảnh. Các mục thuế, lao động, chứng nhận an toàn, kiến trúc hệ thống rộng hơn phần mềm và thực hành nghề Việt Nam cần nguồn chuyên biệt trước khi tăng mức tin cậy.

Kiểm kê số liệu mới nhất: [resource-audit-2026-10-25.json](resource-audit-2026-10-25.json) và [resource-audit-2026-10-25.md](resource-audit-2026-10-25.md).
