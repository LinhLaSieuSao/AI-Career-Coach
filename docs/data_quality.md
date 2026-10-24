# Chất lượng dữ liệu — Đợt 3

Ngày review: **24/10/2026**. Repo `AI-Specialist`, nền `a430250` cùng thay đổi
Đợt 1/2 chưa commit. Dữ liệu dưới đây được tính lại từ JSON thật, không là giới
hạn schema. Giữ đủ 410 ID tài nguyên gốc, 410 nhóm skill, 131 role, 752 câu hỏi;
không thay yêu cầu role/câu hỏi, không bỏ mapping vì URL trùng.

## Thống kê trước và sau

| Chỉ số | Trước | Sau |
| --- | ---: | ---: |
| Role / skill của role | 131 / 410 | 131 / 410 |
| Canonical nhận diện, gồm catalog độc lập | 415 | 415 |
| Resource record / URL duy nhất | 410 / 98 | 445 / 135 |
| Tiếng Anh / tiếng Việt | 382 / 28 | 387 / 58 |
| `verified=false` | 12 | 52 |
| Thời lượng công bố: record / URL | 0 / 0 | 13 / 11 |
| Record có ước lượng biên tập | 0 | 0 |
| Record chưa biết `duration_hours` | 410 | 432 |

Số `verified=false` tăng do ghi nhận 23 mapping không phù hợp và 29 mapping
Autodesk bị chặn, thay vì giữ cờ tin cậy cũ. Đây không phải 52 link hỏng.
12 bản ghi chưa verified ban đầu đã được đối chiếu và đổi sang nguồn cụ thể,
giữ ID; trạng thái nội dung/HTTP vẫn được phân biệt.

Sau review: **44 reviewed, 15 partial, 23 unsuitable, 29 blocked, 334
unreviewed**. 59 mapping reviewed/partial nằm trên 40 URL đã đọc; thêm một URL
catalog bị chặn tạo thành 41 URL được đọc hoặc thử đọc khi tính cả mục không
phù hợp. Nhóm URL theo trạng thái có thể giao nhau: cùng mục OpenStax phù hợp
một phần cho marketing nhưng không phù hợp cho Shopee/tour/UX writing.

5 canonical nhận diện chưa có tài nguyên vẫn được giữ: `.net core`, `english`,
`google tag manager`, `mysql`, `pandas`. Đây là warning, không phải lỗi thiếu
liên kết của role. Integrity sau sửa: **0 lỗi, 5 warning này**.

Snapshot tính lại: [trước](reports/dot03_baseline.json),
[sau](reports/dot03_after.json). Danh sách từng record/URL, phần đã đọc, phạm vi,
ngày, các mapping chưa review và ứng viên bị loại nằm trong
[nhật ký nội dung](reports/dot03_content_reviews.json). Hash/thời điểm tải được
giữ khi lấy bằng HTTP local; nguồn đọc qua web tool ghi phương pháp riêng,
không bịa mã HTTP hoặc hash. Không lưu lại toàn văn tài liệu bên ngoài vào repo.

## HTTP và review nội dung

Chạy riêng CLI, workers=4, timeout kết nối tối đa 5 giây, timeout đọc 10 giây,
tối đa 5 redirect; không retry. Timeout là từng thao tác mạng, không phải thời
gian tổng của URL. Mẫu HTML tối đa 8 KiB có thể không nhận ra mọi trang chặn bot.

| Lần chạy UTC ngày 24/10/2026 | URL | reachable | redirect | blocked | timeout | error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 06:09:41–06:10:07, trước sửa | 98 | 60 | 24 | 11 | 2 | 1 |
| 06:26:34–06:27:10, sau sửa | 135 | 66 | 42 | 22 | 5 | 0 |

Báo cáo [trước](reports/dot03_links_before.json) và
[sau](reports/dot03_links_after.json) chứa thời gian UTC chính xác từng URL,
đích redirect, mã HTTP hoặc lỗi. Các nguồn ASQ/ISO/PACE đọc được bằng web tool
nhưng client local bị chặn; British Council/FPT có lần local timeout dù đã
đọc được nội dung. Không xóa bằng chứng đọc nội dung, không chuyển 403/429
thành kết luận “link chết”, không sửa `verified` tự động theo báo cáo HTTP.

### Nguồn cũ được rà soát

| Nhóm | Xử lý và giới hạn |
| --- | --- |
| 9 mapping ASQ | Thay index bằng bài cụ thể về flowchart, Lean, PDCA/cải tiến liên tục, 5S, ISO 9001, QA/QC, 8D, FMEA, 7 QC tools. Đọc định nghĩa/quy trình; phạm vi nhập môn, không phải khóa chuyên sâu. |
| SOP | Dùng PDF EPA QA/G-6, đọc quy trình viết/review/kiểm soát và cấu trúc SOP. Bản 2007 chỉ dùng học phương pháp, không chứng minh quy định hiện hành. |
| ISO 14001 / 45001 | Dùng tổng quan chính thức ISO. Tổng quan miễn phí, toàn văn tiêu chuẩn có phí (`freemium` + `access_note`), không gắn nhãn toàn bộ tiêu chuẩn miễn phí. |
| OpenStax marketing 1.1, 35 mapping | Đọc mục tiêu/nội dung mục 1.1. 12 mapping giữ ở mức nền tảng `partial`, 23 `unsuitable`; không xóa ID hay URL dùng chung. Không coi đoạn giới thiệu marketing là bài thực hành công cụ. |
| Autodesk catalog/start, 29 mapping | URL thật trả 403; `/learn` đọc được chỉ là điều hướng. Ghi `blocked`, chưa review độ phù hợp từng skill, giữ mọi mapping và bỏ cờ verified cho các mapping này. |
| Microsoft Learn trang chủ | Đọc trang điều hướng: không dùng làm bằng chứng một bài chuyên biệt. Thay bằng module cụ thể cho nhóm ưu tiên; các mapping cũ khác tiếp tục `unreviewed`. |
| URL chung khác | 334 record còn `unreviewed` được liệt kê đầy đủ trong nhật ký, trong đó có 94 URL. Chưa review hết OpenStax kế toán/nhân sự, WHO, Cisco, VBPL và các nguồn còn lại. |

Không chọn bản PDF Vẽ kỹ thuật ở HAUI chỉ có 8 trang bìa/mục lục; nguồn thư
viện Sơn La lỗi TLS hostname cũng bị loại, không tắt kiểm tra TLS. Thay bằng
bài giảng trường học đã tải và đọc 13 slide, đặc biệt slides 7–12 có trình tự
đọc bản vẽ và bài tập. Nhãn `reviewed` chỉ phù hợp phạm vi đó; level 1/2 của tài
nguyên mới không khẳng định người học đã đạt level 3 của nghề.
Ứng viên tài liệu Figma ở thư viện Phenikaa timeout kết nối 25 giây; chưa đọc
được nên không dùng làm bằng chứng mở rộng nguồn UI/UX.

## Top 30 và tiếng Việt

Đếm mỗi canonical tối đa một lần trong mỗi role; sắp `(-role_count, canonical)`
với NFC/Unicode tăng dần khi bằng nhau. Bảng được sinh từ dữ liệu sau sửa.
**30/30 có nguồn tiếng Việt đã đọc; 27 reviewed, 3 partial**. Không tuyên bố
30/30 đã có giáo trình đầy đủ: cẩn thận mới có checklist email, tiếng Anh
chuyên ngành mới có thư tín công việc, UI/UX mới có nguyên tắc nhập môn. Ba mục
này cần nguồn sâu hơn theo bối cảnh nghề. Phần còn lại cũng chỉ cam kết phạm vi
ghi chú, không bao phủ mọi trình độ.

| # | Canonical | Role | Nguồn đã đọc | Phạm vi/giới hạn |
| ---: | --- | ---: | --- | --- |
| 1 | giao tiếp | 91 | [Đại học Huế](https://csdlkhoahoc.hueuni.edu.vn/data/2025/8/sach_ky_nang_mem-_file_in.pdf) | reviewed: Lắng nghe, phản hồi; phần thực hành giao tiếp. |
| 2 | giải quyết vấn đề | 73 | [PACE](https://www.pace.edu.vn/tin-kho-tri-thuc/ky-nang-giai-quyet-van-de) | reviewed: Quy trình từ xác định nguyên nhân tới theo dõi giải pháp; nhập môn. |
| 3 | làm việc nhóm | 57 | [Đại học Huế](https://csdlkhoahoc.hueuni.edu.vn/data/2025/8/sach_ky_nang_mem-_file_in.pdf) | reviewed: Phân công và phối hợp theo mục tiêu. |
| 4 | tiếng anh chuyên ngành | 55 | [British Council](https://www.britishcouncil.vn/hoc-tieng-anh/tieng-anh-nguoi-lon/kinh-nghiem/5-quy-tac-viet-thu-tin) | partial: Tiếng Anh thư tín công việc; chưa bao phủ thuật ngữ chuyên ngành riêng của từng nghề. |
| 5 | excel | 33 | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/get-started-data-concepts/) | reviewed: Lọc, sắp xếp, công thức, định dạng có điều kiện; bài tập Excel cho web. |
| 6 | git | 23 | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/intro-to-git/) | reviewed: Lệnh Git cơ bản và lịch sử thay đổi; không thay thế Git workflow nâng cao. |
| 7 | cẩn thận | 20 | [British Council](https://www.britishcouncil.vn/hoc-tieng-anh/tieng-anh-nguoi-lon/kinh-nghiem/5-quy-tac-viet-thu-tin) | partial: Checklist kiểm tra người nhận, đính kèm, lỗi trước khi gửi email; chỉ một tình huống luyện cẩn thận. |
| 8 | quản lý thời gian | 19 | [Đại học Huế](https://csdlkhoahoc.hueuni.edu.vn/data/2025/8/sach_ky_nang_mem-_file_in.pdf) | reviewed: Ưu tiên công việc, Eisenhower và Pomodoro. |
| 9 | phân tích dữ liệu | 18 | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/explore-analyze-data-with-python/) | reviewed: Notebook khám phá, thống kê mô tả và trực quan dữ liệu; cần Python cơ bản. |
| 10 | sql | 18 | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/introduction-to-transact-sql/) | reviewed: SELECT và truy vấn nhập môn trên T-SQL; lưu ý khác biệt dialect. |
| 11 | tư duy phân tích | 16 | [PACE](https://www.pace.edu.vn/tin-kho-tri-thuc/ky-nang-phan-tich) | reviewed: Phân chia thông tin, đánh giá và suy luận; tổng quan phương pháp. |
| 12 | python | 14 | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/explore-analyze-data-with-python/) | reviewed: Thực hành NumPy/pandas để khám phá dữ liệu; cần biết Python cơ bản. |
| 13 | sáng tạo | 13 | [Trung tâm IKIGAI](https://vinabook.edu.vn/chuong-7-ky-nang-mem-ky-nang-tu-duy-sang-tao/) | reviewed: Chương giảng về tư duy, rào cản và phương pháp sáng tạo. |
| 14 | docker | 12 | [AWS](https://aws.amazon.com/vi/docker/) | reviewed: Container, image và vòng đời triển khai; tổng quan, chưa có lab Docker. |
| 15 | rest api | 12 | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/build-web-api-aspnet-core/) | reviewed: REST/CRUD bằng ASP.NET Core C#; là ví dụ khác stack, không phải bài Java. |
| 16 | thiết kế ui ux | 12 | [FPT Arena](https://arena.fpt.edu.vn/nguyen-tac-thiet-ke-ui-ux-ban-nen-biet/) | partial: Nhập môn bố cục, tương phản, nhất quán; lời khuyên UI cần kiểm thử theo bối cảnh. |
| 17 | thương lượng | 12 | [Đại học Huế](https://csdlkhoahoc.hueuni.edu.vn/data/2025/8/sach_ky_nang_mem-_file_in.pdf) | reviewed: Đề nghị, nhượng bộ và chuẩn bị đàm phán. |
| 18 | linux | 10 | [AWS](https://aws.amazon.com/vi/compare/the-difference-between-apt-and-apt-get/) | reviewed: Lệnh quản lý gói Debian/Ubuntu; phạm vi Linux package management. |
| 19 | thuyết trình | 10 | [Đại học Huế](https://csdlkhoahoc.hueuni.edu.vn/data/2025/8/sach_ky_nang_mem-_file_in.pdf) | reviewed: Chuẩn bị nội dung theo người nghe. |
| 20 | html | 9 | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/build-first-html-webpage/) | reviewed: Cấu trúc HTML và nội dung trang đầu tiên. |
| 21 | tiếng anh giao tiếp | 9 | [British Council](https://www.britishcouncil.vn/hoc-tieng-anh/tieng-anh-nguoi-lon/kinh-nghiem/muoi-cach-chao-hoi-bang-tieng-anh-how-are-you) | reviewed: Câu chào và phản hồi trong hội thoại; giải thích tiếng Việt. |
| 22 | autocad | 8 | [Đại học Nông Lâm TP.HCM](https://www2.hcmuaf.edu.vn/data/dangnh/file/BG_ACAD2D1_2007_NEW.pdf) | reviewed: Lệnh vẽ, hiệu chỉnh và layer 2D; bản 2007, giao diện có thể khác hiện tại. |
| 23 | chăm sóc khách hàng | 8 | [MISA AMIS](https://amis.misa.vn/57433/ky-nang-cham-soc-khach-hang/) | reviewed: Lắng nghe, xác nhận vấn đề và theo dõi xử lý; ví dụ dịch vụ khách hàng. |
| 24 | css | 8 | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/use-css-styles/) | reviewed: Selector, khai báo và liên kết stylesheet; ví dụ mã thực tế. |
| 25 | lập kế hoạch | 8 | [Đại học Huế](https://csdlkhoahoc.hueuni.edu.vn/data/2025/8/sach_ky_nang_mem-_file_in.pdf) | reviewed: Mục tiêu SMART, phân bổ nguồn lực. |
| 26 | xây dựng mối quan hệ | 8 | [Cao đẳng Đại Việt Sài Gòn](https://daivietsaigon.edu.vn/bai-viet-trung-tam-dao-tao/12-ky-nang-xay-dung-moi-quan-he-sinh-vien-dve-can-biet-6e910.html) | reviewed: Giới thiệu bản thân, mở hội thoại và lắng nghe; áp dụng phù hợp văn hóa, hoàn cảnh. |
| 27 | đọc bản vẽ kỹ thuật | 8 | [THCS Bình An, Đông Hòa](https://thcsbinhan-donghoa.hcm.edu.vn/bai-giang-dien-tu/bai-3-ban-ve-chi-tiet/ct/110350/766693) | reviewed: Đọc bản vẽ chi tiết đơn giản; bài tập có lời giải, chưa đủ cho bản vẽ chuyên nghiệp. |
| 28 | aws | 7 | [AWS](https://aws.amazon.com/vi/what-is-cloud-computing/) | reviewed: Dịch vụ và mô hình cloud, ví dụ AWS; mới ở mức nhập môn. |
| 29 | erp | 7 | [MISA AMIS](https://amis.misa.vn/46175/huong-dan-su-dung-erp/) | reviewed: Quy trình, phân quyền, workflow và ví dụ nghiệp vụ; nền tảng của nhà cung cấp. |
| 30 | jira | 7 | [Thuận Jira / Viblo](https://viblo.asia/p/jira-workflow-tong-quan-va-huong-dan-Qbq5Q734ZD8) | reviewed: Status, transition và cấu hình workflow; bài gốc 2022, UI có thể thay đổi. |

Các bài học/PDF nêu trên đọc công khai miễn phí. Excel/Git/SQL/HTML/CSS/Python
là module chính thức Microsoft; thời lượng lấy từ catalog chứ không từ HTML
động chỉ hiện “min”. Đăng nhập để lưu tiến độ; lab có thể cần công cụ/tài
khoản riêng. AutoCAD cần giấy phép, bài 2007 có UI cũ; AWS có thể thu phí khi
chạy dịch vụ; ERP/Jira có quyền tài khoản/gói sử dụng riêng. Nguồn Jira là bài
hướng dẫn gốc của tác giả năm 2022, không coi UI lịch sử là UI hiện tại.

## Thời lượng và role demo

[Bằng chứng catalog Microsoft](reports/dot03_published_durations.json) lưu
10 mục đã chọn cùng UID, URL, số phút và thời điểm lấy thật
`2026-10-24T06:23:19.413237+00:00`. Hash là hash response catalog gốc; file chỉ
giữ các mục được dùng, không giữ toàn bộ response. Spring ghi thời gian gần
đúng ngay trên hướng dẫn. Đây đều là thời gian học **dự kiến của nhà xuất bản**,
không phải giờ đo thực nghiệm để đạt skill/level. Không dùng reading time tự
động của blog, số trang hoặc đề cương một khóa khác làm giờ của tài liệu này.

| Skill được gắn | Tài nguyên | Phút công bố | Căn cứ |
| --- | --- | ---: | --- |
| excel | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/get-started-data-concepts/) | 37 | publisher_catalog_minutes |
| git | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/intro-to-git/) | 86 | publisher_catalog_minutes |
| sql | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/introduction-to-transact-sql/) | 61 | publisher_catalog_minutes |
| phân tích dữ liệu, python | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/explore-analyze-data-with-python/) | 60 | publisher_catalog_minutes |
| rest api | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/build-web-api-aspnet-core/) | 41 | publisher_catalog_minutes |
| rest api, spring boot | [Spring](https://spring.io/guides/gs/rest-service/) | 15 | publisher_approximate_guide_minutes |
| html | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/build-first-html-webpage/) | 31 | publisher_catalog_minutes |
| css | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/use-css-styles/) | 35 | publisher_catalog_minutes |
| power bi | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/get-started-with-power-bi/) | 21 | publisher_catalog_minutes |
| bán hàng | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/manage-opportunities-dynamics-365-sales/) | 63 | publisher_catalog_minutes |
| tìm kiếm khách hàng | [Microsoft Learn](https://learn.microsoft.com/vi-vn/training/modules/manage-leads-dynamics-365-sales/) | 53 | publisher_catalog_minutes |

13 record có giờ nhưng chỉ 11 URL: Python/phân tích dữ liệu cùng một module;
Spring Boot/REST cùng một hướng dẫn. Không cộng trùng khi lập lịch. Các module
REST tiếng Việt dùng **C#**, Power BI/Dynamics ở locale `vi-vn` thực tế là
**tiếng Anh** (đã đặt `language=en`). Spring là ví dụ Java, cần nền Java/JDK;
15 phút không thay thế thời gian học Java hoặc REST level 3.

| Role ID thật | Skill | Có review/partial | Có tiếng Việt đã đọc | Có tài liệu công bố giờ | Skill chưa có giờ |
| --- | ---: | ---: | ---: | ---: | --- |
| `backend_developer_java` | 10 | 9/10 | 8/10 | 4/10 | java, giải quyết vấn đề, docker, giao tiếp, làm việc nhóm, linux |
| `data_analyst` | 10 | 8/10 | 7/10 | 4/10 | tư duy phân tích, thống kê, giải quyết vấn đề, giao tiếp, làm việc nhóm, tableau |
| `sales_executive` | 8 | 7/8 | 5/8 | 2/8 | giao tiếp, thuyết phục, chăm sóc khách hàng, làm việc nhóm, giải quyết vấn đề, quản lý thời gian |

Mọi skill của các role demo có liên kết resource. Tuy nhiên, Java, thống kê,
Tableau và thuyết phục chưa có mapping được review nội dung trong đợt này.
Đa số skill mềm chưa có giờ công bố; 432 record toàn catalog vẫn `null`.
**Chưa đủ căn cứ công bố tổng giờ hoặc ngày hoàn thành toàn bộ ba role.**
Không tạo ước lượng biên tập để lấp số còn thiếu.

## Đầu vào Đợt 4 và Đợt 5

- Đợt 4 có thể dùng các resource có provenance, phạm vi và giờ công bố để lập
  lịch một phần; phân biệt tài liệu thay thế với tài liệu cần học cùng nhau.
- Luôn giữ kỹ năng/gap chưa có giờ, hiển thị “chưa xác định”; tổng giờ đã biết
  là tổng phần đã chọn, không phải tổng lộ trình. Ngân sách 8 giờ/tuần không
  được biến thành 8 giờ/tài liệu.
- Dedup toàn roadmap, tra `resource_keys` qua mọi tuần trước khi cộng giờ.
  Giữ `skills_without_resources` cho canonical thật sự chưa có tài liệu.
- Tách trạng thái nội dung và HTTP; lọc/giải thích `unsuitable`, `blocked`,
  `unreviewed`, cùng `partial` theo ngữ cảnh. Core hiện chưa tự bỏ các bản ghi
  này để giữ hợp đồng Recommender; chưa có bộ xếp hạng tài nguyên mới.
- Đợt 5 dùng đúng ba ID demo trong bảng; không gọi chúng là hồ sơ mẫu đã tạo
  sẵn. Review câu hỏi/rubric và mở rộng nguồn còn thiếu là công việc tiếp theo.

Kiểm thử offline và lệnh nghiệm thu thực tế: [tiến độ Đợt 3](progress/dot_03.md).

## Hồ sơ demo Đợt 5

`Data/demo_profiles.json` có ba ví dụ tổng hợp cho ba role demo đã dùng trong
probe Đợt 4. Mỗi record có `synthetic: true`, notice UI, role ID thật và
skill/level lấy từ catalog. Experience ghi đây là ví dụ; không có tên, quá
trình làm việc hay kết quả tuyển dụng của người thật. Xem [kịch bản demo](demo.md)
và [kiểm kê license](../LICENSES.md).

## Đối chiếu khi triển khai Đợt 4

Không sửa duration, level range hoặc trạng thái review tài nguyên để làm cho
lịch đầy đủ. `build_timed_roadmap` chỉ chọn mapping reviewed/partial có phạm vi
level phù hợp; bỏ blocked/unsuitable/unreviewed khỏi phần có thể chọn. Partial
vẫn được báo unresolved. Những giờ dưới đây chỉ là tổng giờ công bố của các
tài liệu đã chọn, không phải tổng thời gian đạt nghề.

Probe API với `levels={}` (tường minh áp dụng current=0, không là hồ sơ người
thật), budget 8 giờ/tuần:

| Role ID | Giờ đã chọn có nguồn | Tuần phần đã phân bổ | Tổng tuần | Resource chưa biết giờ |
| --- | ---: | ---: | --- | ---: |
| backend_developer_java | 3.3833 | 1 | null | 4 |
| data_analyst | 2.9833 | 1 | null | 3 |
| sales_executive | 1.9333 | 1 | null | 3 |

Cả ba còn thiếu nội dung được review và phạm vi level cao hơn. Khi fixture có
khai báo một số level, các tài liệu nhập môn có thể không còn phù hợp với mức
cần nâng, nên số giờ chọn **giảm**, không có nghĩa đường học đã hoàn chỉnh.
Snapshot đầy đủ hai probe mỗi role:
[dot04_demo_assessments.json](reports/dot04_demo_assessments.json).

Review phỏng vấn Đợt 4: giữ nguyên 752 ID/thứ tự/ngân hàng role; 6 câu thuộc
ba role demo được sửa tình huống và review cặp rubric tường minh (2 câu/role).
12 câu demo còn lại là template, 734 câu ngoài phạm vi chưa gắn reviewed.
Chỉ 6/752 câu có điểm rubric; 746 câu còn lại trả unavailable/score=null, không
biến đáp án mẫu thành tiêu chí tự động. Rubric có nguồn và ngày ở
`Data/interview_rubrics.json`; đây là review nội bộ, chưa thẩm định độc lập.
Chi tiết công thức, schema và giới hạn:
[assessment_contract.md](assessment_contract.md), [tiến độ Đợt 4](progress/dot_04.md).
