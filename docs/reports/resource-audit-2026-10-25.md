# Kiểm kê học liệu và dữ liệu phỏng vấn — 2026-10-25

## Kết quả hiện tại

- Số liệu cuối sau khi xử lý 187 mapping: 131 vị trí, 410 nhóm kỹ năng role, 416 kỹ năng nhận diện, 471 học liệu trên 165 URL.
- Trạng thái nguồn: 55 `reviewed`, 200 `partial`, 175 `unsuitable`, 41 `blocked`, **0 `unreviewed`**.
- Có 255 mapping đủ điều kiện gợi ý trên 150 URL đã xác minh: nội dung phải review và có ghi chú phạm vi; partial luôn kèm giới hạn. Một URL có thể được gắn với nhiều kỹ năng.
- `verified=false` có 216 record; đây gồm các mapping `unsuitable`/`blocked` và không đồng nghĩa mọi link đều hỏng. Cờ URL tự nó không chứng minh nội dung phù hợp.
- Có 5 kỹ năng chỉ có trong vocabulary nhận diện, chưa có tài liệu: `.net core`, `english`, `google tag manager`, `mysql`, `pandas`.
- Ngân hàng phỏng vấn có 752 câu cho 131 vị trí, mỗi vị trí 5–7 câu. Sáu câu có ngày, nguồn và ghi chú review nội bộ; 12 câu là template; 734 câu chưa được review.
- UI giới hạn câu hỏi ở `min(10, số câu có sẵn)`. Không chấm điểm tự động. Câu chưa review có cảnh báo; câu tình huống dùng khung triển khai, không dùng một đáp án chung.
- Bảng review 187 mapping cuối, gồm từng record/URL và quyết định, nằm trong [resource-review-2026-10-25.md](resource-review-2026-10-25.md) và [JSON chi tiết](resource-review-2026-10-25.json).

## Học liệu đã bổ sung hoặc xác nhận

| Kỹ năng | Tài liệu | Review | Phạm vi đã đối chiếu |
| --- | --- | --- | --- |
| JavaScript | [MDN JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide) | reviewed | Cú pháp, kiểu, điều khiển luồng, hàm, object, promise và module. |
| React | [React Quick Start](https://react.dev/learn) | reviewed | Component, JSX, dữ liệu, điều kiện, danh sách và sự kiện. |
| TypeScript | [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/) | reviewed | Basics, everyday types, narrowing, functions, object types, classes, modules. |
| Machine learning | [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course/) | reviewed | Nền tảng khái niệm và bài thực hành; có điều kiện tiên quyết về Python/toán. |
| Kubernetes | [Kubernetes Tutorials](https://kubernetes.io/docs/tutorials/kubernetes-basics/) | reviewed | Deploy, expose, scale, update, debug; cần cluster để thực hành. |
| CRM | [HubSpot Free Tools Course](https://academy.hubspot.com/courses/hubspot-free-tools) | partial | HubSpot CRM cụ thể; trang khóa học nêu 5 bài thực hành và 1 giờ 22 phút. Không đại diện mọi CRM. |
| CI/CD | [GitHub Actions — Get started](https://docs.github.com/en/actions/get-started) | partial | Tài liệu liên kết riêng CI và CD workflows trên GitHub Actions; không trung lập với nền tảng khác. |
| PyTorch | [PyTorch Tutorials](https://docs.pytorch.org/tutorials/intro.html) | reviewed | Learn the Basics, xây dựng và huấn luyện mô hình; phiên bản tài liệu có thể thay đổi. |
| Ngân sách | [OpenStax: Prepare Operating Budgets](https://openstax.org/books/principles-managerial-accounting/pages/7-2-prepare-operating-budgets) | reviewed | Ngân sách hoạt động và mối quan hệ với master budget; nền tảng giáo trình. |
| Lập báo cáo | [Microsoft Learn: Power BI report creation](https://learn.microsoft.com/power-bi/create-reports) | partial | Tạo report/dashboard trên Power BI, không bao quát mọi công cụ hoặc phương pháp báo cáo. |
| Phân tích tài chính | [OpenStax: Analyzing Financial Statements §14.7](https://openstax.org/books/introduction-business-2e/pages/14-7-analyzing-financial-statements) | partial | So sánh báo cáo và phân tích tỷ số thanh khoản, sinh lời, hoạt động, nợ; giáo trình nhập môn Hoa Kỳ, không thay cho tuân thủ kế toán Việt Nam, định giá hay mô hình tài chính. |
| Viết nội dung | [Google Technical Writing](https://developers.google.com/tech-writing) | partial | Chỉ viết tài liệu kỹ thuật; nội dung quảng cáo/business writing cần portfolio và biên tập viên góp ý. |
| Agile/Scrum | [The Scrum Guide](https://scrumguides.org/scrum-guide.html) | reviewed | Xác nhận hướng dẫn định nghĩa Scrum; cần thực hành trong nhóm để hình thành kỹ năng. |
| Google Analytics | [Google Skillshop](https://skillshop.withgoogle.com/) | reviewed | Danh mục có đào tạo Google Analytics; chỉ đào tạo cách dùng công cụ Google. |
| Java | [Dev.java General Tutorials](https://dev.java/learn/) | partial | Nguồn Oracle/OpenJDK hiện hành về Java fundamentals, OOP, generics/lambda, exceptions, collections/streams; không thay thế Spring Boot, kiểm thử và vận hành production. |
| Tableau | [Tableau Free Training Videos](https://www.tableau.com/learn/training) | partial | Video Desktop, Cloud/Server và Prep là các nhánh sản phẩm riêng; chỉ nhập môn, không gộp thời lượng hay coi là portfolio hoàn chỉnh. |
| SEO | [Google Search Central SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide) | partial | Crawl/index, cấu trúc trang, nội dung hữu ích và Search Console; dành cho Google Search, không bảo đảm thứ hạng. |
| Thống kê | [OpenStax Introductory Statistics 2e](https://openstax.org/books/introductory-statistics-2e/pages/1-introduction) | partial | Giáo trình nhập môn về mô tả, xác suất, ước lượng, kiểm định, hồi quy/ANOVA; chưa thay cho phân tích nghiệp vụ bằng dữ liệu/công cụ thực tế. |
| C# | [Microsoft Learn: C# First Steps](https://learn.microsoft.com/training/paths/csharp-first-steps/) | reviewed | Lộ trình nền tảng C#; Microsoft công bố 2 giờ 39 phút. Không đại diện mọi framework .NET. |
| Canva | [Canva Design School](https://www.canva.com/design-school/) | partial | Có Canva Essentials nhập môn khoảng 1 giờ; danh mục gồm nội dung có thể yêu cầu Canva Pro, nên chi phí/phạm vi mỗi khóa cần kiểm tra. |
| Figma | [Figma Courses, tutorials and projects](https://help.figma.com/hc/en-us/categories/23557013073047-Courses-tutorials-projects) | partial | Bài học theo sản phẩm như Figma Design/portfolio/design system; không phải đánh giá năng lực UX theo người dùng thực. |
| Nền tảng mạng | [Cisco Networking Basics](https://www.netacad.com/courses/networking-basics) | reviewed | Trang chính thức nêu 17 module, 13 lab và 22 giờ; phù hợp nền tảng mạng, không chứng minh kỹ năng quản trị production. |
| Data warehouse | [Microsoft Fabric Data Warehouse](https://learn.microsoft.com/en-us/fabric/data-warehouse/tutorial-introduction) | partial | Hướng dẫn kho dữ liệu trên Microsoft Fabric; yêu cầu tenant/trial và nền tảng vendor-specific. |
| ETL | [Azure Data Factory Tutorials](https://learn.microsoft.com/en-us/azure/data-factory/data-factory-tutorials) | partial | Copy/ingest, data flow và pipeline trên Azure; trang lưu ý Fabric Data Factory là hướng phát triển tiếp theo. |
| Kiến trúc cloud | [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/) | partial | Khung review kiến trúc AWS, không phải giáo trình kiến trúc hệ thống trung lập nền tảng. |
| Kiến trúc phần mềm | [SEI: Software Architecture: Principles and Practices](https://sei.cmu.edu/training/software-architecture-principles-practices/) | partial | Kiến trúc phần mềm, thuộc tính chất lượng, pattern/tactic, thiết kế, tài liệu và đánh giá; yêu cầu kinh nghiệm hệ thống phần mềm, khóa trả phí, không bao quát phần cứng/vận hành/hạ tầng. |
| An toàn lao động (nhập môn) | [ILO: Participatory Action-Oriented Training](https://www.ilo.org/publications/participatory-action-oriented-training) | partial | Sổ tay 2011 về checklist, giải pháp thực tế/chi phí thấp và cải tiến tại nơi làm việc; không thay luật/quy chuẩn hiện hành hoặc khóa huấn luyện được cấp phép tại Việt Nam. |
| Bóc tách khối lượng | [Autodesk Forma Takeoff — Performing Quantity Takeoff](https://help.autodesk.com/cloudhelp/ENU/Takeoff-Takeoff/files/Performing_Takeoff.html) | partial | Luồng thao tác đo bóc 2D/3D trong sản phẩm Autodesk; không phải phương pháp độc lập theo mọi bộ môn/định mức và không hướng dẫn lập dự toán Việt Nam. |
| Quản lý tồn kho | [OpenStax: Inventory Management §10.4](https://openstax.org/books/introduction-business-2e/pages/10-4-pulling-it-together-resource-planning) | partial | Bao quát đặt, nhận, lưu, theo dõi và đánh đổi chi phí; chưa phải bài tập ERP/WMS hoặc vận hành kho theo SKU thực. |
| Phân tích yêu cầu | [IIBA: The Business Analysis Standard](https://www.iiba.org/globalassets/business-analysis-resources/the-business-analysis-standard/files/the-business-analysis-standard.pdf) | partial | Bao quát stakeholder, elicitation, yêu cầu và thiết kế; cần ghép domain cụ thể và bài tập dự án, tài liệu tiếng Anh. |

Mỗi mục tương ứng với record có `content_reviewed_at`, `review_note`, `evidence_locator` và `verification_origin` trong `Data/resources.json`. Các nguồn được dẫn để người dùng mở đọc; không sao chép nội dung của publisher vào ứng dụng.

## Rà soát mapping dùng chung

Ở vòng trước đã review thêm 141 mapping trên các trang có nhiều skill dùng chung: 38 được giữ ở mức `partial` và 103 đánh dấu `unsuitable` cho skill tương ứng. Sau đó đã mở và đối chiếu 80 trang cho 187 mapping cuối: 126 `partial`, 49 `unsuitable`, 12 `blocked`. Từng mapping có quyết định riêng; không kế thừa nội dung của cổng tổng quan sang kỹ năng cụ thể chỉ vì cùng publisher.

Các trang tổng quan như Microsoft Learn, WHO Academy và cổng văn bản pháp luật không được xem là khóa dạy mọi kỹ năng. Cờ `verified=false` hiện có 216 record; chất lượng nội dung được quyết định bởi `content_review_status` và ghi chú phạm vi, không chỉ bởi trạng thái liên kết.

## Thực hành thay cho khóa học bắt buộc

`modules/practice_guidance.py` tạo route trải nghiệm khi thiếu kỹ năng giao tiếp, bán hàng/tìm khách hàng, chăm sóc khách hàng, xử lý vấn đề, quản lý nhóm, tổ chức sự kiện, viết nội dung hoặc trait liên quan. Route yêu cầu nhiệm vụ thật có giám sát hoặc role-play, phản hồi từ đồng nghiệp/mentor và bằng chứng tự theo dõi. Với bán hàng, người dùng luyện hỏi nhu cầu, xử lý phản đối bằng thông tin kiểm chứng và xác nhận bước tiếp theo; app không chỉ dựa vào tỷ lệ chốt.

Trong lộ trình, route thực hành được hiển thị riêng với tài liệu. Hoàn thành khóa học không được coi là đã đạt kỹ năng; ngược lại, thiếu khóa học cũng không chặn kế hoạch thực hành kỹ năng mềm.

## Nguồn chưa được đưa vào danh sách đề xuất

Đã thêm sổ tay PAOT của ILO ở mức `partial` cho thực hành OSH nhập môn: có checklist, cải tiến nơi làm việc và group work, đồng thời là tài liệu năm 2011 nên không thay cho yêu cầu pháp lý, đào tạo được cấp phép, an toàn điện hoặc PCCC tại Việt Nam. [Trang ILO về PAOT](https://www.ilo.org/resource/training-material/participatory-action-oriented-training-paot), [PDF sổ tay (113 trang)](https://www.ilo.org/sites/default/files/wcmsp5/groups/public/@asia/@ro-bangkok/@sro-bangkok/documents/publication/wcms_169357.pdf).

Các nhóm có nguồn mức `partial` được gợi ý kèm giới hạn cụ thể gồm Java, Tableau, SEO, thống kê, Canva/Figma, CRM/CI/CD, data warehouse/ETL, Power BI, phân tích tài chính theo giáo trình Hoa Kỳ, kiến trúc phần mềm và PAOT an toàn lao động nhập môn. Nguồn này chỉ hỗ trợ một phần và không khẳng định người học đạt level nghề.

Bóc tách khối lượng, tồn kho, phân tích yêu cầu và phân tích tài chính hiện có tài liệu nền tảng partial; vẫn cần bài tập theo bản vẽ/định mức Việt Nam, dữ liệu SKU thật, domain dự án và báo cáo thực tế. Kiến trúc hệ thống rộng hơn phần mềm vẫn cần nguồn trung lập. Các mapping thuế và lao động được giữ `blocked` cho đến khi có thể đối chiếu nguồn pháp lý hiện hành và phạm vi áp dụng đầy đủ. Chưa xác minh được khóa huấn luyện an toàn đủ điều kiện pháp lý tại Việt Nam; PAOT chỉ là phương pháp thực hành nhập môn, không phải chứng nhận tuân thủ. Cisco Networking Basics chỉ dạy nền tảng mạng, không chứng minh năng lực quản trị mạng production.

## Giới hạn của đợt rà soát

Đợt cuối đọc và đối chiếu nội dung 80 trang cho 187 mapping `unreviewed` ban đầu. Tất cả đã được xử lý thành 126 `partial`, 49 `unsuitable` và 12 `blocked`; các mục bị loại không được gợi ý. Phân loại dựa trên nội dung nhìn thấy và phạm vi liên kết tại thời điểm review, không phải xác nhận độc lập về chất lượng khóa học hay hiệu lực pháp lý. Các nguồn bị chặn có thể được review lại khi có truy cập hoặc tài liệu cụ thể. Danh sách quyết định theo từng record nằm trong [resource-review-2026-10-25.json](resource-review-2026-10-25.json); history các vòng trước ở `docs/reports/dot03_content_reviews.json`.

Audit dữ liệu local: `docs/reports/resource-audit-2026-10-25.json`.
