# Rà soát hành trình người dùng tổng quan

**Ngày:** 25-10-2026
**Nhánh:** `Nhanh-Linh`
**Ứng dụng:** Streamlit local, `http://127.0.0.1:8501`
**Phương pháp:** AppTest trên script thật, unit test cho parser/matcher/export, HTTP loopback và Chromium/Playwright thật; axe-core chạy trên giao diện landing và trang kết quả.

## Kết quả thực thi

- `pytest tests/test_exhaustive_user_flows.py -vv -s`: **28 passed**, 17.85 giây.
- Regression liên quan chặn xác nhận hồ sơ không còn kỹ năng: **2 passed**, 5.72 giây.
- HTTP local: **200**, nội dung `text/html; charset=utf-8`.
- Các cảnh báo `missing ScriptRunContext` trong log là cảnh báo thường gặp của AppTest khi chạy script ở chế độ bare; không phát sinh exception trong các ca pass.
- `pytest -q`: **460 passed**, 103.50 giây.
- `pytest browser_tests/test_accessibility_responsive.py -q -s`: **4 passed**, 31.42 giây.
- Chromium dùng luồng bàn phím để chọn hồ sơ mẫu và xác nhận; màn hình landing/kết quả không tràn ngang tại 375px/414px. Bài 200% dùng CSS zoom trong viewport 800px (đây là stress test layout, không phải đổi mức zoom của trình duyệt/Windows).
- Sau xác nhận, 13 liên kết học liệu có `target="_blank"` cùng `noopener noreferrer`; reload mở lại ứng dụng và không hiển thị exception. HTTP status của đích liên kết chưa được kiểm tra trong browser này.
- axe-core quét landing và kết quả: **0 critical/serious**, còn 2 cảnh báo minor `presentation-role-conflict` (mỗi trạng thái một cảnh báo). Chưa quét screen reader.

### Cải thiện được xác nhận trong lượt này

- Chuẩn hóa hậu tố phiên bản cho các công nghệ đã biết (`Python 3.12`, `SQL Server 2019`, `Vue 3`) và alias React/Vue theo đúng tên canonical trong catalog. Các tên dạng `skill 11` và chuẩn `ISO 45001` giữ nguyên để tránh gộp nhầm.
- Bước rà soát hiển thị tổng số kỹ năng, số khớp catalog và tên cần người dùng rà soát; khi không còn kỹ năng nào, thông báo chỉ rõ thao tác để tiếp tục.
- Kết quả giải thích cách tính gợi ý, cảnh báo kỹ năng ngoài catalog và phân biệt lộ trình theo giai đoạn với lịch theo tuần có thời lượng.
- Link học liệu mở tab mới an toàn; caption và chữ phụ trong uploader được tăng độ tương phản. Thông báo riêng tư được giới hạn ở xử lý phiên local, không ghi file dự án và không gửi CV tới API bên ngoài.
- Có thể chạy browser suite độc lập bằng `python -m pytest browser_tests/test_accessibility_responsive.py -q -s`; cài thêm `playwright` và `axe-playwright-python` từ `requirements-dev.txt`.

### Tổng kết ma trận 8 chuyên đề

| Chuyên đề | Phạm vi đã kiểm tra | Số ca/bước trong bộ mới | Trạng thái | Rủi ro còn lại |
|---|---|---:|---|---|
| 1. Nhập liệu, encoding, paste | 10 biến thể văn bản người dùng; CV dán hơn 40.000 từ qua giao diện; CV tay không cần file | 11 | Đạt về an toàn/không crash; một số phiên bản công nghệ phổ biến và alias đã chuẩn hóa; tên lạ vẫn cần người dùng xác nhận | P2 – gợi ý gần đúng không tự sửa mọi lỗi chính tả và danh mục vẫn hữu hạn |
| 2. Trạng thái và điều hướng | Back–edit; demo sang hồ sơ cá nhân; submit/rerun; reload Chromium sau kết quả | 4 luồng AppTest/browser | Đạt cho luồng và reload không crash | P2 – chưa nghiệm thu việc F5 giữ hay khôi phục trạng thái hồ sơ; chưa đo spam click thật |
| 3. Tệp CV biên | Hủy/xóa và thay PDF→DOCX; 3 loại magic bytes giả; scan; PDF 20 trang; bố cục hai cột | 8 tình huống gộp trong 3 test functions | Đạt cho parser và widget mô phỏng | P2 – file chooser/cancel thật chưa được thao tác trong browser |
| 4. Chuyển nghề và JD | Sinh viên ít tín hiệu; kế toán→Data/ML; sở thích trái năng lực; JD must/nice/unclassified và đối chiếu sau xác nhận | 4 tình huống | Đạt theo heuristic và luật phân loại hiện tại | P2 – điểm không phải thẩm định chuyên gia hay mức sẵn sàng tuyển dụng |
| 5. Rà soát kỹ năng và level | Thêm kỹ năng tùy chỉnh; level 0/1/3 và để trống; công thức gap; bỏ chọn toàn bộ | 2 luồng AppTest | Đạt; hồ sơ rỗng ở bước xác nhận bị chặn kèm hướng dẫn | P3 – người dùng vẫn phải tự khai báo level đúng |
| 6. Kết quả 5 tab và minh bạch | Kiểm tra đủ 5 tab, heuristic, gap, sơ đồ lộ trình, thiếu học liệu, câu trả lời trống/đã gửi và không chấm điểm; kiểm tra 13 link | 3 nhóm kiểm tra + Chromium | Đạt cho giao diện/logic đã kiểm tra; link mở tab mới an toàn | P2 – chưa có lựa chọn thời hạn 4/8 tuần; URL đích/404 chưa kiểm tra live |
| 7. Export và riêng tư | UTF‑8, CSV formula injection với `= + - @`, CV thô không vào file, thông báo riêng tư | 2 nhóm kiểm tra | Đạt ở hàm export và nội dung hiển thị | P2 – chưa kiểm toán lưu trữ tiến trình/session trên OS; đây không phải chứng nhận bảo mật |
| 8. Bàn phím, viewport, zoom, accessibility | Tab/Enter chọn demo và xác nhận; 375/414px landing + kết quả; stress CSS zoom 200%; axe landing + kết quả | 4 browser tests | Đạt luồng bàn phím đã bao phủ, không tràn ngang; 0 lỗi axe critical/serious, còn 2 cảnh báo minor | P2 – CSS zoom chỉ mô phỏng; chưa kiểm tra screen reader, toàn bộ luồng bằng bàn phím hoặc zoom trình duyệt thật |

**Quy ước:** P1 ảnh hưởng trực tiếp khả năng sử dụng/có thể chặn người dùng; P2 có khả năng gây nhầm hoặc giảm độ tin cậy; P3 cần chú ý nhưng chưa phải lỗi chức năng. Không có P0 được tái hiện.

## Điểm nghẽn trải nghiệm và bằng chứng

1. **Tên kỹ năng nhập không chuẩn.** Dấu tiếng Việt, chữ hoa, dấu đầu dòng, dấu trích dẫn, NBSP, chữ đơn và chuỗi Telex không làm ứng dụng crash. Phiên bản phổ biến như `Python 3.12`, `SQL Server 2019`, `Vue 3` được chuẩn hóa; alias như `React.js`, `Vue.js`, `Vue3` ánh xạ tới tên catalog. Các lỗi gõ như `kyx nawng` vẫn cần người dùng xem gợi ý và xác nhận. App giữ nguyên tên không chắc chắn thay vì âm thầm ghi nhận sai.

2. **Hồ sơ cần tối thiểu một kỹ năng.** CV rỗng hoặc không nhận ra kỹ năng được đưa tới bước rà soát nhưng không thể xác nhận nếu cuối cùng người dùng bỏ hết kỹ năng. Cảnh báo chỉ rõ phải giữ/thêm một kỹ năng. Đây là điểm chặn có thông điệp hành động; không tạo kết quả nghề giả từ sở thích.

3. **Điểm và sở thích được tách rõ.** Với một kỹ năng, app đưa cảnh báo độ tin cậy thấp. Sở thích trái với năng lực thiết kế không thể tự đẩy Security lên điểm cao do giới hạn 5 điểm khi skill fit rất thấp. Chỉ số là heuristic; nó không đo xác suất được tuyển.

4. **JD phân loại thận trọng.** Chỉ các heading nhận diện rõ mới gán kỹ năng vào must-have/nice-to-have. Kỹ năng ở đoạn không rõ heading để riêng, không bị đưa vào tổng hợp như yêu cầu bắt buộc. Người dùng còn bước xác nhận nhóm trước khi tính 85/15. Đây là hành vi tốt để tránh đoán mức ưu tiên từ văn xuôi.

5. **Chưa có quyền chọn số tuần cho chế độ presence.** Lộ trình presence hiện chia theo cấu trúc tuần do hệ thống dựng; không có điều khiển “4 tuần/8 tuần”. Chế độ level nhận ngân sách giờ/tuần và tính số tuần theo thời lượng có căn cứ; khi thiếu duration/review, tổng tuần để “Chưa xác định”. Không nên trình diễn như thể người dùng tùy chỉnh được thời hạn.

6. **Liên kết và tình trạng học liệu.** Browser xác nhận 13 link được render mở tab mới an toàn với `noopener noreferrer`. Bài test không truy cập 13 URL để xác minh HTTP 200/404 hoặc redirect. Giao diện có nhãn trạng thái nội dung, cảnh báo partial/missing và phần thực hành bổ sung. Nội dung `partial` vẫn cần bài tập/portfolio theo bối cảnh; với kỹ năng mềm, role-play, nhiệm vụ có giám sát và phản hồi là lộ trình chính, không phải đợi khóa học.

7. **Quyền riêng tư có thông báo, chưa phải kiểm toán hệ điều hành.** Giao diện nêu CV được xử lý trong phiên, không ghi thành tệp dự án và không gửi tới API bên ngoài. Export loại toàn văn CV nhưng giữ phần kinh nghiệm người dùng nhập tay. Chưa có bằng chứng từ kiểm toán process/session rằng dữ liệu chỉ tồn tại trong RAM hoặc không được hệ điều hành ghi vào pagefile/log; không diễn đạt thông báo giao diện thành bảo đảm tuyệt đối.

8. **Kết quả browser và giới hạn.** Chromium thực sự chạy được 4 bài: Tab/Enter tới nút demo và xác nhận hồ sơ; focus-visible xuất hiện; landing/kết quả không tràn ngang ở 375px và 414px; 13 link có thuộc tính mở tab an toàn; reload không báo exception. axe báo 0 lỗi critical/serious và 2 minor `presentation-role-conflict`. Phần 200% là CSS zoom stress test nên chưa chứng minh trải nghiệm ở mức zoom trình duyệt/Windows thật. Bài bàn phím mới bao phủ đường demo tới trang kết quả, chưa bao phủ mọi điều khiển và screen reader.

## Kịch bản demo

### 1. Chuyển nghề kế toán sang Data Engineer

1. Ở trang bắt đầu, nhập `Kế toán, Excel, Phân tích tài chính`, chọn `Data Engineer`.
2. Sang rà soát, giữ Excel và các kỹ năng liên quan; khai level đúng với thực tế, không tự suy level từ kinh nghiệm.
3. Xác nhận, mở tab **Khoảng cách** để cho thấy các thiếu hụt như SQL/Python/pipeline, rồi mở **Lộ trình** và **Tài liệu**.
4. Nhấn mạnh đây là gợi ý kỹ năng và học liệu cục bộ, không phải dự đoán tuyển dụng; nếu tài liệu không đủ tin cậy, hệ thống phải chỉ ra phần unresolved.

### 2. JD có must-have, nice-to-have và kỹ năng chưa phân loại

1. Dán CV mẫu có Python/SQL và JD có các heading riêng `Yêu cầu bắt buộc`, `Điểm cộng`, `Mô tả công việc`.
2. Ở bước 2, xem các kỹ năng được trích và xác nhận/chỉnh nhóm; không chấp nhận nhóm chưa phân loại như must-have.
3. Mở **Tóm tắt** để trình bày bao phủ bắt buộc/ưu tiên riêng và kỹ năng còn thiếu; nhắc tỷ trọng 85/15 là heuristic, không chấm năng lực thực tế.

### 3. Hồ sơ kỹ năng mềm và luyện phỏng vấn an toàn

1. Chọn hồ sơ demo backend hoặc nhập hồ sơ tổng hợp; chỉ dùng dữ liệu giả lập.
2. Mở **Lộ trình**/**Tài liệu** để chỉ ra hoạt động role-play, bài tập có người giám sát, mentor/đồng nghiệp phản hồi khi khóa học không đủ.
3. Mở **Phỏng vấn**, thử gửi câu trả lời trống để thấy nhắc nhập; nhập một câu trả lời giả lập rồi gửi.
4. Cho xem khung tham khảo và checklist tĩnh; hệ thống không phân tích hay chấm câu trả lời. Nhắc backlog review của ngân hàng câu hỏi tách biệt với mapping học liệu.

## Các bước nghiệm thu còn lại

1. Kiểm tra F5/back/forward để xác định rõ hành vi lưu và khôi phục trạng thái hồ sơ sau reload.
2. Kiểm tra zoom 200% bằng mức phóng thực của browser/OS; mở rộng luồng keyboard tới tất cả input, tabs, menu, tải xuống, và kiểm tra screen reader.
3. Kiểm tra 13 URL học liệu theo HTTP status/redirect/access denied; không gửi CV thật tới dịch vụ ngoài.
4. Xác định chính sách lưu session của Streamlit local trước khi đưa ra khẳng định “RAM-only”; giữ tuyên bố hiện tại ở phạm vi thông báo giao diện.

## Nghiệm thu bổ sung ngày 26-10-2026

Đợt này chạy server Streamlit local riêng trên `http://127.0.0.1:8504/`, mở bằng trình duyệt và nhập dữ liệu giả như người dùng. Đã nhập `Python 3.12; postgre sql; Pyhton`, kinh nghiệm “đã dùng Python và SQL, chưa sử dụng Docker”, JD bắt buộc Python/SQL/PostgreSQL và ưu tiên Docker/Git. Wizard nhận alias/version, gợi ý sửa `Pyhton → python`, tách nhóm JD, nhưng trước sửa còn đưa Docker từ câu phủ định vào kỹ năng hồ sơ. Sau sửa, kiểm thử AppTest và Chromium xác nhận câu phủ định rõ không còn tạo skill tự nhận. Người dùng vẫn có thể tự khai Docker riêng, đúng với luồng xác nhận.

Thử hồ sơ mẫu Data Analyst rồi nhập `Docker; SQL` ở bước 2 đã tái hiện `StreamlitDuplicateElementKey` do SQL trùng theo chữ hoa/thường. Bản sửa cho ô thêm skill rerun ngoài form, hiện Level của Docker **trước** khi xác nhận và gộp skill trùng/alias vào một điều khiển. Kiểm tra lại bằng trình duyệt thật: không exception, Level Docker chọn được, kết quả có 5 tab. Tab Lộ trình hiển thị 4 giai đoạn ưu tiên; tab Tài liệu nêu 471 mapping và phạm vi `partial`; nhãn “tuần” trên tài liệu presence đã đổi thành “giai đoạn”. Tab Phỏng vấn hiển thị 6/16/3/727 câu theo trạng thái; gửi trống nhận nhắc nhập, gửi câu giả định chỉ hiện khung/checklist không chấm điểm. Reload trả về form đầu và không khôi phục kết quả; UI nay nêu rõ chính sách đó và có nút xóa phiên.

Kiểm thử sau sửa: **466/466** test core/AppTest pass (89,33 giây); **5/5** Chromium browser tests pass (27,81 giây). Smoke core pass, validator 752 câu/131 role không có lỗi cấu trúc, golden benchmark 23 hồ sơ tổng hợp có Hit@3 100%, MRR@3 0,949 và Forbidden@3 0%. Các metric synthetic này chỉ là regression, không chứng minh độ phù hợp tuyển dụng ngoài đời. Axe trên landing và kết quả: **0 critical/serious**, còn **2 minor `presentation-role-conflict`** ở `stFileUploaderDropzone` của Streamlit; lỗi tương phản màu nghiêm trọng ở notice success đã sửa và quét lại. Bài kiểm tra 200% vẫn là CSS zoom; screen reader và zoom OS/browser thực chưa được nghiệm thu.

Gói nguồn `0.4.0-candidate` local có ZIP, tar.gz, manifest và checksum; giải nén ZIP vào thư mục mang version rồi smoke và validator từ thư mục giải nén đều pass với Python/dependencies **đã cài sẵn**. Đây chưa phải clean install từ gói và chưa phải release công khai. Docker Desktop CLI có nhưng daemon local chưa chạy; CI xanh trên GitHub thuộc `main` SHA `8827a81`, không thuộc source dirty hiện tại. [Kiểm tra GitHub mới](github-latest-2026-10-26.json) xác nhận repo công khai, Issues/Discussions bật, chưa có tag/release.

Rà toàn bộ 165 URL học liệu bằng GET ngắn: 91 reachable, 47 redirect, 20 blocked và 7 timeout. [Báo cáo link](../reports/links-live-2026-10-26.md) liệt kê 42 mapping đủ điều kiện chịu ảnh hưởng từ nhóm blocked/timeout; không tự coi 403/timeout là nội dung sai. [Inventory dữ liệu](data-readiness-2026-10-26.md) tách kiểm tra cấu trúc (pass) khỏi cổng review chuyên môn và provenance/quyền (pending). Hiện còn 727 câu phỏng vấn unreviewed, 3 template, 751/1.248 ô skill×level thiếu nguồn đủ điều kiện; không record role/question/resource có bộ metadata provenance đầy đủ. [Ma trận B3/PoF](b3-pof-gap-matrix.md) nêu điều kiện để hướng tới 10/10 và phần phải do owner/chuyên gia/giám khảo xác nhận.

Sau đó đã tạo venv runtime mới và cài `requirements.lock` có hash **từ ZIP ứng viên đã giải nén** thành công, chạy smoke, validator, inventory ngay từ thư mục gói và khởi động Streamlit với health 200 trên cổng thử 8505. [Nhật ký phạm vi clean install](clean-install.md) ghi giới hạn môi trường và các bước chưa thử. Danh sách [131 role và 40 skill ưu tiên review](priority-review-2026-10-26.md) giúp chia backlog theo locator cụ thể; thứ tự này là khối lượng phục vụ, không phải mức rủi ro nghề nghiệp.

### Bổ sung review dữ liệu và module ngày 26-10

Người dùng dự án đã báo kiểm tra thủ công được toàn bộ 165 URL ở trang gốc. [Bản ghi có fingerprint](../../Data/link_review_attestation.json) và [phụ lục báo cáo link](../reports/links-live-2026-10-26.md) giữ riêng lời xác nhận này; 20 `blocked` và 7 `timeout` của bot không được coi là 27 link chết. Cổng inventory/CI sẽ báo khi tập URL thay đổi, nhưng không tự nâng nội dung, Level hoặc quyền tái sử dụng.

Review theo role×skill cho thấy 750/1.192 cặp có câu hỏi, 674/1.192 có học liệu đúng Level nghề yêu cầu; với weight ≥ 2, lần lượt 715/950 và 505/950. Chín mapping từng gắn Level 1–3 quá rộng đã thu hẹp theo [bằng chứng nguồn](../reviews/resource-level-scope-2026-10-26.md), trong đó trang chủ Google Skillshop chuyển từ `reviewed/course` sang `partial/directory`. Ma trận hiện có 77 reviewed, 411 partial và 760 thiếu trên 1.248 ô; việc giảm coverage là loại overclaim. UI presence hiện ghi Level nội dung và nhắc khi thấp hơn Level vị trí. [Hàng đợi 131 nghề](priority-review-2026-10-26.md) đã được sinh lại theo đúng Level, cùng 67 câu hỏi dạng mẫu và 2 mapping Level 1–3 cần chỉ rõ chương/bài.

[Module sweep](module-paths-2026-10-26.md) chạy hồ sơ tổng hợp cho toàn bộ 131 role qua matcher, gap, roadmap presence/timed, chọn 3 câu hỏi và đọc hướng dẫn trả lời: 131/131 role không exception; 393 đáp án tham khảo lấy được. Đây là kiểm tra kết nối dữ liệu/logic, không chứng minh hiệu lực nội dung hay mọi tình huống UI. Sau cả chín sửa Level, bộ core/AppTest đạt **470/470** (166,66 giây), Chromium browser đạt **5/5** (49,91 giây). Máy chủ Streamlit cũ từng giữ module Python trong cache và gây `ImportError` khi app hot reload; sau khi khởi động tiến trình mới trên `127.0.0.1:8504`, giao diện và tab Lộ trình mở lại bình thường. Các số 466 và 751 trong phần nghiệm thu trước ở trên là snapshot trước vòng review Level này.
