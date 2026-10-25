# Đợt 3 — Integrity và chất lượng tài nguyên

Thực hiện ngày **24/10/2026**, local Windows, Python **3.12.14** trong `.venv`
của project. Nhánh **AI-Specialist**, HEAD **a430250**. Không đổi nhánh,
reset/commit/push/PR; giữ thay đổi đang có từ Đợt 1/2. Không thấy AGENTS.md áp
dụng trong các thư mục cha/project đã kiểm tra.

Đã đọc `docs/interface.md`, tiến độ Đợt 1/2, báo cáo ma trận ở thư mục cha,
loader, dữ liệu và core hiện hành. Baseline chạy lại **231 passed**, bao gồm
AppTest và CV Parser; không suy từ audit cũ. Không cần chữa lại luồng Đợt 1/2.

## Đã triển khai

- `modules/data_quality.py`: integrity offline của roles/resources/aliases/
  catalog/câu hỏi, ID/uniqueness, canonical, khóa ngoại, level/weight, loại và
  chi phí/ngôn ngữ, duration/provenance, ngày và trạng thái review. Role skill
  thiếu resource là lỗi; skill chỉ để nhận diện chưa có tài liệu là warning.
- `scripts/check_links.py`: CLI GET từng URL chuẩn hóa duy nhất, timeout kết
  nối/đọc hữu hạn, tối đa 5 redirect, workers 1–8, phân loại 5 trạng thái. Mẫu
  HTML 8 KiB để nhận một số kiểu chặn bot. Transport inject được. Mặc định chỉ
  xuất báo cáo; không sửa cờ resource và chặn output ghi đè catalog.
- `tests/test_data_integrity.py`, `tests/test_check_links.py`: fixture hỏng,
  dữ liệu thật, alias câu hỏi, phân biệt thiếu resource/recognition-only, tie
  ổn định, fake transport, redirect/bot/timeout/lỗi, concurrency, CLI không
  mutate, top 30, provenance giờ và tham chiếu xuyên tuần sau dedup toàn roadmap.
- `Data/resources.json`: thêm 30 mapping tiếng Việt, 5 mapping demo khác; giữ
  đủ 410 ID cũ và mọi nhóm skill. Review/thay URL 12 bản ghi cũ chưa verified,
  đánh dấu các mapping quá chung hoặc chưa đọc được bằng trạng thái trung thực.
- `requirements.txt`: khai báo trực tiếp `requests==2.34.2` cho công cụ CLI;
  dependency đã có sẵn trong môi trường, không thay Python toàn máy.
- `docs/interface.md`, `docs/data_quality.md`: hợp đồng provenance, trạng thái
  và cách dùng dữ liệu chưa biết cho Đợt 4; bảng top 30 và 3 role demo.
- `docs/reports/dot03_*.json`: snapshot trước/sau, HTTP trước/sau, bằng chứng
  số phút chính thức, nhật ký từng URL/mapping và danh sách chưa review.

## Thống kê thực tế

| Chỉ số | Trước sửa | Sau sửa |
| --- | ---: | ---: |
| Role / skill role / skill nhận diện | 131 / 410 / 415 | 131 / 410 / 415 |
| Resource / URL duy nhất | 410 / 98 | 445 / 135 |
| Tiếng Anh / Việt | 382 / 28 | 387 / 58 |
| Câu hỏi | 752 | 752 |
| `verified=false` | 12 | 52 |
| Record có giờ công bố / URL tương ứng | 0 / 0 | 13 / 11 |
| Record có giờ ước lượng biên tập | 0 | 0 |
| Record giờ chưa biết | 410 | 432 |
| Lỗi integrity | 0 | 0 |

334 record `unreviewed`; 44 `reviewed`, 15 `partial`, 23 `unsuitable`, 29
`blocked`. Cờ false tăng do bỏ xác nhận cho 23 mapping OpenStax không dạy skill
được gắn và 29 mapping Autodesk chưa đọc được, không phải do xóa tài liệu.
12 bản ghi false ban đầu chuyển sang bài cụ thể đã đọc, giữ ID. Không đặt mọi
cờ thành true. Không review lại toàn bộ catalog và không khẳng định như vậy.

Integrity vẫn báo 5 warning thiếu tài nguyên của `.net core`, `english`,
`google tag manager`, `mysql`, `pandas`; tất cả role skill có tài liệu. Không
thêm các skill độc lập đó vào yêu cầu role để chữa coverage.

## Nguồn, tiếng Việt và duration

Top 30 theo số role có canonical, tối đa một lần/role, tie theo NFC tăng dần.
**30 có nguồn tiếng Việt đã đọc, gồm 27 reviewed và 3 partial**. Ba partial:
`cẩn thận` (checklist email), `tiếng anh chuyên ngành` (thư tín công việc),
`thiết kế ui ux` (nguyên tắc nhập môn có lời khuyên cần áp dụng theo bối cảnh).
Chưa nghiệm thu 30/30 giáo trình chuyên biệt bao phủ đủ skill/nghề; không
đánh dấu partial thành đầy đủ chỉ để đạt chỉ tiêu. Các bài/giáo trình khác cũng
chỉ cam kết phạm vi đã đọc. Bảng từng canonical, số role, URL và lý do nằm tại
[docs/data_quality.md](../data_quality.md#top-30-và-tiếng-việt).

Đã đọc nguồn gốc/nhà xuất bản/giáo dục: Đại học Huế, Microsoft Learn, AWS,
British Council, PACE, FPT Arena, Nông Lâm TP.HCM, THCS Bình An, Đại Việt Sài
Gòn, IKIGAI, MISA; Jira là bài thực hành gốc của tác giả trên Viblo. Không dùng
tiêu đề search làm xác nhận. Hướng dẫn AutoCAD 2007 và Jira 2022 ghi rõ giới
hạn phiên bản. PDF HAUI chỉ bìa/mục lục và PDF Sơn La lỗi TLS bị loại. Bài
giảng bản vẽ được đọc từ PPTX đính kèm, không chỉ đọc trang giới thiệu.
Đã thử thêm tài liệu Figma của Phenikaa để mở rộng UI/UX, nhưng local báo
`ConnectTimeout (connect timeout=25)`; không đưa nội dung chưa đọc vào catalog.

Danh sách đầy đủ: [review nội dung](../reports/dot03_content_reviews.json),
có `original_unverified` nêu 12 ID và URL trước/sau; `unreviewed_records` nêu
334 mapping chưa review. Review URL chung: OpenStax marketing 35 mapping;
Autodesk 29 mapping URL catalog bị 403; Microsoft Learn trang chủ chỉ là điều
hướng, không được coi là bài chuyên biệt. Những nhóm tài chính/nhân sự/WHO/
Cisco/VBPL còn lại chưa được nghiệm thu nội dung.

10 module Microsoft lấy số phút từ API publisher, kiểm chứng UID/URL, lưu
snapshot lúc **06:23:19 UTC**; thêm Spring guide ghi **khoảng 15 phút**. 13
record dùng 11 URL do nguồn dùng chung; giờ được chia từ phút / 60, không phải
ước lượng của nhóm. `duration_source`, `duration_basis`, ngày kiểm chứng và
locator đi cùng dữ liệu. Không lấy reading time blog hoặc số trang làm giờ.
Không có ước lượng thủ công, mọi phần chưa biết tiếp tục `null`.

Role demo thật:

| ID | Có nguồn reviewed/partial theo skill | Có nguồn giờ công bố theo skill | Còn thiếu |
| --- | ---: | ---: | --- |
| `backend_developer_java` | 9/10 | 4/10 | Java chưa review; Spring 15 phút là bài khởi đầu, REST tiếng Việt dùng C# cần coi là lựa chọn khác stack. |
| `data_analyst` | 8/10 | 4/10 | Thống kê/Tableau chưa review; giờ không có cho nhiều kỹ năng mềm. |
| `sales_executive` | 7/8 | 2/8 | Thuyết phục chưa review; module Dynamics có điều kiện tài khoản/phần mềm riêng. |

**Chưa đủ dữ liệu cho tổng giờ/tuần hoàn thành cả role.** Đợt 4 có thể xếp phần
đã chọn có giờ, giữ phần chưa biết, không mặc định 8 giờ/resource. Dedup theo
`resource_keys` toàn roadmap, không cộng mọi phương án thay thế. Mốc 8 giờ/tuần
là ngân sách người học, không là thời lượng suy ra của tài liệu. Đợt 5 dùng
ba ID trên; chưa tạo UI hồ sơ mẫu.

## Lệnh và kết quả nghiệm thu

Các lệnh chạy từ root repo. Môi trường Python 3.12.14, Streamlit 1.66.0,
pytest 9.1.1, python-docx 1.2.0, pdfplumber 0.11.10, requests 2.34.2. Full suite
đặt TEMP/TMP vào `.venv/tmp` như Đợt 2; không skip/xfail.

```powershell
$env:TEMP = (Resolve-Path '.venv/tmp').Path
$env:TMP = $env:TEMP
```

| Lệnh | Kết quả thực tế |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot03-baseline --tb=short` | **231 passed in 12.86s**, trước sửa. |
| `.\.venv\Scripts\python.exe -X utf8 -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot03-tools tests/test_data_integrity.py tests/test_check_links.py --tb=short` | **43 passed in 0.33s**, phiên bản công cụ đầu. |
| `.\.venv\Scripts\python.exe -X utf8 -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot03-curated tests/test_data_integrity.py tests/test_check_links.py tests/test_matcher.py tests/test_recommender.py tests/test_skill_extractor.py --tb=short` | **149 passed in 0.90s**, sau thêm dữ liệu. |
| `.\.venv\Scripts\python.exe -X utf8 -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot03-affected tests/test_data_integrity.py tests/test_check_links.py tests/test_matcher.py tests/test_recommender.py tests/test_skill_extractor.py tests/test_catalog.py --tb=short` | **175 passed in 1.12s**, bản code/test cuối. |
| `.\.venv\Scripts\python.exe -X utf8 -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot03-full --tb=short` | **282 passed in 15.61s**, gồm AppTest/upload/undo, CV Parser và regression core. |
| `.\.venv\Scripts\python.exe -X utf8 scripts/check_links.py --timeout 10 --workers 4 --output docs/reports/dot03_links_before.json` | 98 URL: 60 reachable, 24 redirect, 11 blocked, 2 timeout, 1 error. UTC 06:09:41–06:10:07. |
| `.\.venv\Scripts\python.exe -X utf8 scripts/check_links.py --timeout 10 --workers 4 --output docs/reports/dot03_links_after.json` | 135 URL: 66 reachable, 42 redirect, 22 blocked, 5 timeout, 0 error. UTC 06:26:34–06:27:10. |
| `audit_project()` trên dữ liệu cuối | **0 errors**, 5 recognition-only warnings; không gọi mạng. |
| `git diff --check` | Không lỗi whitespace. |
| So JSON `HEAD:Data/resources.json` với bản hiện tại bằng ID | Giữ đủ 410/410 ID, 410/410 nhóm skill. |

`.venv` không có module pip: lệnh `.\.venv\Scripts\python.exe -m pip check`
báo `No module named pip`. Đã chạy bằng pip của runtime local với
`python -m pip --python .venv check`: **No broken requirements found**. Không
cần cài dependency hoặc thay Python toàn máy trong đợt này.

Live checks không nằm trong pytest/CI. Unit test dùng transport giả, không
phụ thuộc mạng. Local 403/429 và timeout là chưa xác minh kết nối, không xóa
nguồn đã đọc bằng web tool hay coi HTTP 200 là nội dung phù hợp. CLI không sửa
JSON. Chưa kiểm tra Linux/Python 3.11, native browser hay layout mobile; full
local Windows/Python 3.12 đã được nghiệm thu.

## P-ID và việc còn lại

| ID | Kết quả trong Đợt 3 |
| --- | --- |
| P01 | Đã bổ sung integrity và regression khóa ngoại/khoảng trắng; không tái tạo lỗi role/resource. |
| P05 | Có provenance giờ cho 3 role demo; **một phần** dữ liệu giờ. Chưa lịch giờ/level hay tổng thời gian toàn role. |
| P06 | Có CLI/report live, review 12 cũ và URL chung, 30 nguồn tiếng Việt đã đọc. **Một phần** về chiều sâu 3 skill và review toàn catalog; 334 record còn chưa review. |
| P09 | Đã kiểm tra khóa ngoại/ID/level/weight/câu hỏi theo đúng role và alias. Chưa review chất lượng rubric, chấm đáp án hoặc phỏng vấn theo gap. |

Điều kiện Đợt 4: hiển thị unknown duration, chọn/lọc tài liệu theo trạng thái,
stack và phạm vi; không coi liên kết đầy đủ là nội dung đã phù hợp; không cộng
trùng giờ; cần review/ước lượng có căn cứ trước khi công bố lộ trình hoàn chỉnh.
Giữ API Matcher/Recommender/Extractor, canonical và casing `Data/` đã chốt.

## File cần commit khi người dùng quyết định

Phạm vi riêng Đợt 3:

- `Data/resources.json`, `requirements.txt`.
- `modules/data_quality.py`, `scripts/__init__.py`, `scripts/check_links.py`.
- `tests/test_data_integrity.py`, `tests/test_check_links.py`.
- `docs/interface.md`, `docs/data_quality.md`, `docs/progress/dot_03.md`.
- Sáu báo cáo `docs/reports/dot03_baseline.json`, `dot03_after.json`,
  `dot03_links_before.json`, `dot03_links_after.json`,
  `dot03_content_reviews.json`, `dot03_published_durations.json`.

Các thay đổi Đợt 1/2 vẫn ở working tree, được giữ nguyên trong phạm vi công
việc này; không tự stage hay tách/chọn commit thay người dùng. Cache tải tài
liệu và script chuẩn bị một lần nằm trong `.venv/` bị ignore, không thuộc bàn
giao. Báo cáo lưu URL/hash/phần đã đọc và số phút cần thiết để review kết quả.
