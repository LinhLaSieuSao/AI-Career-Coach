# Đối chiếu B3/PoF và kế hoạch đạt mức chấm tối đa

Ngày đối chiếu: 26-10-2026. Rubric gốc là tệp `Đánh giá khả năng phát triển của một dự án Phần mềm tự do nguồn mở.md` do người dùng cung cấp. Bằng chứng GitHub chi tiết nằm trong [snapshot 25-10](github-public-audit-2026-10-25.json) và [kiểm tra trạng thái mới 26-10](github-latest-2026-10-26.json); dữ liệu local có [inventory tái lập](data-readiness-2026-10-26.md). Đây là đánh giá chuẩn bị, không phải điểm giám khảo đã cho.

## Sửa lại kết luận PoF trước đây

Không có cơ sở để giữ mức **125 PoF** cũ. `LinhLaSieuSao/AI-Career-Coach` là repository công khai, có web viewer, README và tài liệu, Issues, Discussions, MIT License và CI xanh ở `main` commit `8827a81` ([run 40157639170](https://github.com/LinhLaSieuSao/AI-Career-Coach/actions/runs/40157639170)). CI đó gồm test Python và Docker build/healthcheck. Bản local `Nhanh-Linh` HEAD `b67cb26` còn nhiều thay đổi chưa công bố, nên không được dùng CI của `main` làm bằng chứng cho chính bản này.

Các khoản PoF **xác nhận được theo cách hiểu GitHub là website dự án**: chưa có release công khai **+50**; thiếu thông báo license trong từng tệp mã **+10** → **60**. Mailing list và thông báo phát hành qua mailing list chưa tìm thấy trong README/docs đã kiểm tra, có thể cộng thêm **tối đa 15** nếu giám khảo yêu cầu đúng hình thức đó. Rubric gốc được viết cho dự án biên dịch kiểu GNU Make; cách áp mục GNU Make/`make install` cho web Python chạy bằng Streamlit cần giám khảo xác nhận. Không cộng chồng các mức release “không tuần tự/không phiên bản/không phát hành” cho cùng một hiện trạng. GitHub Pages tắt và không có homepage riêng không tự chứng minh “không có website” khi trang repo, README và tài liệu web hiện hữu. Trạng thái tải nguồn qua codeload đã được kiểm tra: archive của commit `main` tải được, khoảng 359 KB nén; source tree khoảng 2.36 MB.

Do đó mức chắc chắn hiện tại là **60 PoF theo diễn giải trên**, với khoản điều kiện và cách áp tiêu chí cần xác nhận. Mốc **≤60** là ranh giới 1 điểm B3, không phải bảo đảm sẽ được 1 điểm. Khi có release theo phiên bản, kiểm tra gói chạy được và thông báo license cho mã nguồn, các khoản xác nhận được sẽ giảm; không sửa rubric hoặc gắn nhãn dữ liệu giả để giảm điểm.

## Ma trận B3 trên hiện trạng

| Tiêu chí (tối đa) | Bằng chứng hiện có | Thiếu để có hồ sơ 10/10 | Điều kiện nghiệm thu |
| --- | --- | --- | --- |
| I. Mã nguồn/phần mềm trên Internet (1) | Public `main`, tải source archive được, README chạy local, CI Docker xanh; ZIP ứng viên local đã cài hash trong venv mới và khởi động health 200 | Bản đang cải tiến chưa ở GitHub; bản public còn mô tả phỏng vấn chấm theo cụm từ | Công bố đúng commit đã test; người khác clone, cài lock, chạy local và Docker healthcheck |
| I. OSI license/đúng đề (1) | MIT trong `LICENSE`; web định hướng nghề nghiệp hoạt động | Chưa xác nhận quyền với catalog nghề, câu hỏi, câu trả lời, metadata học liệu và brand | Owner xác nhận phạm vi phân phối từng tập dữ liệu; giấy phép code và dữ liệu được phân biệt rõ |
| I. PoF ≤60 (1) | Mức xác nhận 60 dưới diễn giải nêu trên | Chưa có release; thông báo license từng tệp; câu hỏi về mailing list/GNU Make | Release có version, ZIP và tar.gz với thư mục version, checksum, chạy từ gói; xin cách áp rubric từ giám khảo |
| I. Công cụ mở (0,5) | Git, Python, Streamlit, pytest, Playwright; workflow công khai | Chứng cứ trên commit cải tiến | CI chạy trên đúng SHA phát hành |
| I. License tương thích (0,5) | Direct runtime/dev dependencies được kiểm kê trong `LICENSES.md` | Metadata pin dev đã cũ; thiếu SBOM/transitive và quyền dữ liệu | Cập nhật inventory theo lock, SBOM/artifact và xác nhận dữ liệu trước công bố |
| I. Tài liệu build/cài (0,5) | README có lệnh Python/Docker/browser; đã cài từ ZIP trong venv mới và chạy health, smoke, validator | Chưa chạy browser trong venv gói hoặc Docker local; chưa xác nhận Linux/macOS | Máy sạch Python 3.12 cài bằng hash, chạy app, smoke, browser và Docker theo README |
| I. Kênh công khai (0,5) | GitHub Issues, Discussions đã bật | README local trước đây nói chưa xác minh; hoạt động cộng đồng chưa chứng minh bằng số lượng tương tác | README dẫn đúng kênh; issue/feedback được tiếp nhận, không bịa cộng đồng |
| II. Nguyên gốc (1) | Role-IDF, skill gate, RIASEC thận trọng, policy học liệu và lộ trình thực hành giải thích được | Không có đối chiếu định lượng với baseline/đánh giá giám khảo | Demo nêu cơ chế và điểm khác biệt bằng kịch bản có số liệu tái lập |
| II. Hoàn thiện (1) | 5 tab, CV/JD, lộ trình, phỏng vấn không auto-score; lượt local đạt 474 core/AppTest và 6 Chromium browser tests sau khi kịch bản đã chọn role; dữ liệu qua module lõi 131/131 nghề | 727 câu unreviewed, 3 template, 760/1248 ô skill×level không có tài liệu đủ điều kiện; 674/1192 cặp nghề–skill có mapping ở Level gán nhưng chỉ 4/471 mapping có scope cấp đơn vị và locator; chưa có CI đúng SHA | Test đúng SHA đã công bố; nội dung chưa review không được trình bày như đã chứng thực; owner/chuyên gia rà theo từng role/skill |
| II. Thân thiện (1) | Wizard xác nhận, demo, sơ đồ giai đoạn, không tràn ngang ở viewport hẹp; đã sửa skill phủ định, tên trùng và tương phản success notice | Cần kiểm keyboard/zoom/screen reader rộng hơn; axe còn 2 minor từ uploader Streamlit | Người dùng thêm/sửa Level không lỗi; audit accessibility rộng hơn trên phiên bản ứng viên |
| II. Bền vững (1) | Kiến trúc module, tests, docs, issue tracker, lock | Provenance per-record vắng; release/CI chính phiên bản mới, maintenance process và SBOM chưa có | Inventory, quyền, review owner, release checklist, CI và kênh đóng góp rõ người phụ trách |
| II. Showcase/cộng đồng (1) | 3 demo synthetic, docs/demo, repo công khai | Chưa có bằng chứng trình diễn trước giám khảo hoặc phản hồi cộng đồng; không có release | Diễn tập trên gói phát hành, quay/chụp bằng chứng theo rubric và ghi nhận phản hồi thật |

Phần I có nhiều hạng mục đã có bằng chứng hơn báo cáo cũ. Phần II phụ thuộc đáng kể vào trình diễn, đánh giá chuyên gia và quyết định giám khảo; không thể xác nhận 10/10 chỉ bằng cách tính test pass. Với bằng chứng hiện tại, cần báo **chưa xác nhận 10/10**, không đưa ra một số thập phân có vẻ chính xác nhưng không có cơ sở.

Ước lượng có điều kiện cho **Phần I hiện tại: khoảng 3–5/5**. Mức dưới gồm mã nguồn/cài từ public `main` (1), license MIT code nhưng quyền dữ liệu cần kiểm (ít nhất 0,5), công cụ mở (0,5), tài liệu cài (0,5) và kênh công khai (0,5); PoF và tương thích license có thể bị giám khảo giữ điểm khi cách áp rubric hoặc quyền dữ liệu chưa chốt. Mức trên đòi hỏi chấp nhận GitHub là website dự án, tính PoF ở mức ≤60 và xác nhận tương thích/quyền. **Phần II chưa có khoảng điểm đáng tin cậy** vì nguyên gốc, độ hoàn thiện, tính thân thiện, tính bền vững và showcase đều có phần chấm qua demo/đánh giá của giám khảo. Tổng 10/10 chỉ là mục tiêu sau khi mọi cột điều kiện nghiệm thu được xác nhận; không cộng giả định tối đa thành điểm hiện tại.

## Khung sửa theo cấu trúc hiện có

1. **`modules/skill_extractor.py`, `modules/profile.py`, `app.py`:** tách kỹ năng người dùng tự khai, kỹ năng trích từ CV/kinh nghiệm và kỹ năng JD; bỏ các câu phủ định rõ ràng, vẫn yêu cầu xác nhận với văn cảnh không chắc chắn. Form thêm kỹ năng phải hiện Level trước khi xác nhận và gộp tên/alias trùng. Regression với Python 3.12, `postgre sql`, typo, câu “chưa dùng Docker”, CV tay và thiếu trường.
2. **`modules/matcher.py`, `modules/recommender.py`, `modules/timed_planner.py`:** giữ điểm kỹ năng, sở thích và kinh nghiệm ở vai trò riêng; mọi điểm phải có tử số/mẫu số, giới hạn đầu vào và giải thích. JD nhiều đoạn phải quét hết, must/nice/unclassified cần người dùng rà. Presence roadmap là giai đoạn, lịch tuần chỉ nêu khi thời lượng có căn cứ.
3. **`Data/resources.json`, `modules/resource_policy.py`, `modules/practice_guidance.py`:** ưu tiên các ô role×skill×level người dùng demo thật; giữ `partial` đúng phạm vi; học liệu thiếu nguồn thì có trạng thái unresolved và bài tập/portfolio theo bối cảnh. Với kỹ năng mềm, nhiệm vụ được giám sát, role-play và phản hồi là đường thực hành chính. Thuế/lao động/chứng nhận an toàn cần nguồn thẩm quyền và chuyên gia Việt Nam.

   [Kiểm tra URL bằng bot 26/10](../reports/links-live-2026-10-26.md) ghi 165 URL: 91 reachable, 47 redirect, 20 blocked, 7 timeout. Người dùng đã báo mở thủ công toàn bộ 165 URL ở nguồn gốc và có nội dung; [attestation](../../Data/link_review_attestation.json) gắn với tập URL hiện tại, CI báo khi tập này đổi. Kết quả bot không còn được coi là backlog kiểm tra truy cập, nhưng URL mở được không xác nhận mapping skill–Level hoặc quyền tái sử dụng.
4. **`Data/interview_question/`, `modules/interview.py`:** 727 câu unreviewed và 3 template là backlog nội dung độc lập với resource mapping. Mỗi câu cần tác giả/nguồn, role/skill, hướng dẫn trả lời có bối cảnh, ngày/người review; cờ AI hỗ trợ không biến thành expert review. Giới hạn số câu mỗi phiên và giữ chế độ tự đối chiếu, không tạo điểm tự động từ cụm từ.
5. **`scripts/audit_data_readiness.py`, `LICENSES.md`:** ba cổng riêng cho cấu trúc, review chuyên môn và provenance/quyền tái sử dụng. Link HTTP 200, `verified=true` hoặc nguồn đọc tham khảo không cấp quyền phân phối. Owner cung cấp bằng chứng per-record hoặc manifest gắn rõ với từng record; đánh giá pháp lý không tự động suy từ script.
6. **`browser_tests/`, `.github/workflows/ci.yml`, `Dockerfile`, README:** CI chạy browser thật và fail nếu không có Chromium; Docker dùng lock/hash; README có cách clone/cài/chạy/test đúng. Chạy các ca thiếu trường, sai skill, CV tải và dán, JD dài, sales/data/backend, phỏng vấn, export, reset/reload, bàn phím/axe.
7. **Gói phát hành:** chỉ sau khi dữ liệu và quyền được owner chốt, tạo gói versioned ZIP và tar.gz, kiểm tra checksum/cài từ archive, tag/release trên đúng SHA CI xanh. Changelog và thông báo công khai trỏ tới kết quả thật. Đây là hành động xuất bản, tách khỏi việc chuẩn bị gói ứng viên local.

## Ưu tiên thực hiện và dấu hiệu đóng

| Ưu tiên | Việc cần làm | Đóng khi |
| --- | --- | --- |
| P0 | Lỗi crash form, skill phủ định, lệnh cài và CI bản đang phát triển | Browser + AppTest tái hiện cũ và pass sau sửa; không còn exception; CI đúng SHA xanh |
| P1 | Review/provenance có nguồn và quyền; câu hỏi phỏng vấn; ô học liệu thiếu | Inventory chỉ rõ từng record và owner xác nhận; sản phẩm không quảng bá dữ liệu chưa review như đã kiểm định |
| P1 | Release theo phiên bản và bằng chứng PoF | Archive versioned, hai định dạng, checksum, clean-install từ gói, tag/release, README/CI trùng commit |
| P2 | Accessibility và showcase | Audit keyboard/screen reader trên hành trình đủ, xử lý axe còn lại; kịch bản demo và phản hồi thật |

Mục tiêu 10/10 là **tiêu chí đóng việc**, không phải điểm đang đạt. Giám khảo quyết định cách áp PoF cho Python web, tính nguyên gốc và trình bày; owner/chuyên gia phải xác nhận chất lượng và quyền dữ liệu. Mọi báo cáo sau này cần gắn SHA, ngày, lệnh chạy và ranh giới của bằng chứng.
