# Đợt 2 — Parser, validation, alias và undo

Ngày thực hiện: **24/10/2026**, Asia/Saigon.
Project: `khắc phục ma trận vấn đề/AI-Career-Coach`.
Nhánh/HEAD giữ nguyên **AI-Specialist / a430250**. Không có `AGENTS.md` áp dụng.
Đã đọc interface, biên bản Đợt 1 và báo cáo ma trận trước khi sửa.

Các sửa đổi Đợt 1 đang ở working tree chưa commit khi bắt đầu; đã giữ chúng,
không reset, đổi nhánh, commit, push hay tạo PR. `dot_01.md` được giữ làm hồ sơ
lịch sử. Nền tảng Đợt 1 được chạy lại: **169 passed in 5.95s** trên Python
3.12.14, gồm startup AppTest, 131 role thật, unknown/alias và app dùng core.
Không cần sửa bù nền tảng Đợt 1 để triển khai Đợt 2.

## Kết quả nghiệm thu

Full suite cuối cùng: **231 passed in 12.00s**, không skip/xfail. Có **25 test
CV Parser**, **12 test controller**, **27 test app/Streamlit AppTest**. Không
chỉ compile/import: AppTest tương tác form, role, checkbox, undo và uploader.
Upload dùng API widget thật của Streamlit 1.66, không còn monkeypatch uploader
như cách kiểm tra Đợt 1. Fixture đều tổng hợp, không dùng CV cá nhân.

Dữ liệu giữ **131 role / 410 canonical kỹ năng role**. Catalog nhận diện hợp
thành **415 kỹ năng**, thêm 5 canonical độc lập; **54 alias**. Không sửa role
requirements hoặc resources để tạo coverage giả. Không đổi casing `Data/`.

## Thay đổi và file cần review/commit của Đợt 2

| File | Thay đổi |
| --- | --- |
| `modules/cv_parser.py` | Reader nội bộ dùng chung có raise; API parse_document phân loại lỗi từ đọc thật và bằng chứng trang; giữ wrappers string. |
| `modules/__init__.py` | Export lazy parse_document. |
| `modules/submission.py` (mới) | Controller chuẩn bị/validate kết quả trước khi ghi state, tách lỗi CV/JD khỏi khả năng tạo Profile. |
| `app.py` | Dùng controller/parser có cấu trúc; role placeholder; không tạo kết quả rỗng; giữ snapshot cũ khi draft lỗi; undo rerun và reset widget đúng phạm vi. |
| `modules/catalog.py` | load_skill_vocabulary hợp kỹ năng role với catalog nhận diện độc lập; kiểm tra kiểu/entry trùng. |
| `Data/skill_catalog.json` (mới) | pandas, mysql, english, google tag manager, .net core; không thêm yêu cầu role hoặc link học tập. |
| `Data/skill_aliases.json` | js→javascript, git/github→git, gtm→google tag manager; bỏ GTM→Analytics và .NET Core→ASP.NET Core. |
| `modules/profile.py` | Dùng vocabulary chung mới; undo_profile_move chuẩn hóa kỹ năng khôi phục, phân loại unknown và giữ sở thích gốc. |
| `modules/matcher.py` | CV/JD dùng cùng vocabulary chung mới; chữ ký/đầu ra/công thức Matcher giữ nguyên. |
| `tests/document_fixtures.py` (mới) | PDF text/trắng/nét vẽ/ảnh và DOCX tổng hợp, không có dữ liệu cá nhân. |
| `tests/test_cv_parser.py` | Path/file-like, consumed stream, đuôi/override, empty/corrupt/ảnh, DOCX nested/merged table, wrappers và export public. |
| `tests/test_submission.py` (mới) | Form trống, JD-only, CV hợp lệ/lỗi, skill form độc lập, không tự tạo skill. |
| `tests/test_app.py` | Upload qua AppTest thật; validation, role tùy chọn, snapshot lỗi, undo liên tiếp và widget/phiên phỏng vấn. |
| `tests/test_profile.py` | Vocabulary độc lập, toàn bộ ví dụ P02 trong cả form/CV và undo nhiều item/sở thích gốc. |
| `tests/test_skill_extractor.py` | Alias exact/các cặp không gộp sai; integrity đích alias, không chain/cycle/collision canonical. |
| `tests/test_catalog.py` | Catalog mở rộng/legacy, entries sai/trùng, cwd và không thay role requirements. |
| `tests/test_matcher.py` | Không lấy pandas/MySQL/English/GTM/.NET Core thay kỹ năng cha hoặc sản phẩm khác trong JD. |
| `tests/test_recommender.py` | Kỹ năng mới chưa có resource vẫn được giữ và báo thiếu, không tạo link giả. |
| `tests/doc-cai-nay-de-test-module-extractor-dung-hon.md` | Bỏ số lượng test cũ đã lỗi thời trong hướng dẫn chạy. |
| `docs/interface.md` | Hợp đồng parser, validation/controller/state, undo, vocabulary/alias cập nhật. |
| `docs/progress/dot_02.md` (mới) | Biên bản này. |

Các file đã sửa Đợt 1 nhưng không đổi thêm trong Đợt 2 vẫn có trong Git status,
gồm `modules/interview.py`, `tests/test_interview.py`, `docs/progress/dot_01.md`.
Cần giữ chúng khi review/commit toàn bộ công việc. Không commit `.venv`/cache/temp.

## Quyết định hợp đồng

### Parser và tương thích

`parse_document(source, filename=None)` trả `{text: str, error_code: str|None,
message: str}`. Thành công có error_code=None, message rỗng. Failure có text
rỗng và message thân thiện:

| Mã | Quy tắc |
| --- | --- |
| NO_FILE | None, path chuỗi rỗng hoặc path không tồn tại. |
| UNSUPPORTED_FORMAT | Thiếu đuôi hoặc ngoài PDF/DOCX; đuôi không phân biệt hoa/thường. |
| EMPTY | 0 byte hoặc đọc được nhưng không có text và chưa đủ bằng chứng trang ảnh. |
| UNREADABLE | Lỗi đọc/giải mã, nội dung sai đuôi, tệp hỏng/bảo vệ hoặc stream không dùng được. |
| SCANNED_PDF | Đọc PDF thành công, không có text; mọi trang đều có raster image và không có text character. |

Không kết luận PDF trắng/nét vẽ/không trích được text là scan. Không OCR. Các
reader nội bộ đọc thật và để exception đi lên API mới; không bọc wrapper đã
nuốt lỗi rồi đoán nguyên nhân. DOCX giữ thứ tự paragraph/table/bảng lồng nhau,
không lặp ô gộp. File-like được rewind và không bị đóng bởi parser.

Giữ `extract_text`, `extract_text_from_pdf`, `extract_text_from_docx` trả string;
lỗi đọc vẫn trả chuỗi rỗng, extract_text vẫn ValueError với đuôi không hỗ trợ.

### Validation và state

- Có kỹ năng form sau khi tách/chuyển interest, hoặc CV có text hợp lệ mới tạo
  Profile. Unknown vẫn là kỹ năng khai báo hợp lệ. Chỉ JD/interests/experience,
  khoảng trắng hoặc dấu phân cách không tạo Profile.
- CV hợp lệ không có kỹ năng nhận diện vẫn lưu để xem văn bản; không dựng skill
  hay điểm role khi danh sách kỹ năng hiệu lực rỗng. CV lỗi không làm mất kỹ
  năng form hợp lệ. JD-only yêu cầu CV, không báo scan.
- Role mặc định None với placeholder. Có thể lưu Profile/so CV-JD khi chưa có
  role, nhưng không có điểm theo role/roadmap/phỏng vấn. Chưa thêm suggest_roles.
- Controller trả candidate, không chỉnh session_state. App chỉ thay đồng bộ
  Profile/role/CV/comparison khi candidate accepted. Draft bị từ chối chỉ cập
  nhật lỗi và cờ rejected, giữ snapshot trước với nhãn rõ ràng. Lần hợp lệ mới
  thay toàn snapshot, không dùng CV/JD hoặc lỗi của hồ sơ cũ.
- Undo cập nhật Profile rồi rerun, không vẽ thông báo chuyển cũ sau hoàn tác.
  Kỹ năng được restore về canonical, unknown được báo đúng. Giữ sở thích nhập
  tường minh hoặc còn do item moved khác tham chiếu. Checkbox unknown dùng khóa
  revision+canonical nên không mất lựa chọn do đổi thứ tự; hồ sơ mới reset các
  checkbox và phiên/câu trả lời phỏng vấn trước.

### Alias, vocabulary, fuzzy

`normalize_skill` và `extract_skills` không bị thay đổi. Matcher/Recommender
giữ API đã chốt. `build_vocabulary(roles)` vẫn chỉ trả kỹ năng role; API mới
`load_skill_vocabulary()` hợp role với list canonical độc lập. Catalog mở rộng
có thể không tồn tại trong fixture/legacy; trường hợp đó dùng vocabulary role.

ML, Communication, Git/GitHub, JS, Node.js nhận diện exact qua cùng alias map ở
form và CV/JD. pandas/MySQL/English là canonical riêng, không phải Python/SQL/
tiếng Anh chuyên ngành. Rà alias công nghệ thấy hai gộp sai rõ ràng: Google Tag
Manager→Google Analytics và .NET Core→ASP.NET Core; đã bỏ hai gộp này, đưa tên
độc lập vào catalog. Giữ các quy ước alias khác để tương thích caller; không sửa
hàng loạt thuật ngữ ngoài phạm vi. Integrity kiểm tra mọi đích có trong catalog
nhận diện, không alias chain/cycle hoặc alias chiếm tên canonical khác.

5 kỹ năng mới chưa có resource. Recommender vẫn giữ chúng, resource_keys rỗng
và skills_without_resources đúng; không đổi role hoặc tạo URL giả. Fuzzy vẫn
tùy chọn/mặc định tắt, app không dùng rapidfuzz và không cài dependency mới.
Nhánh fuzzy sẵn có chỉ xét token/tên đơn từ dài ít nhất 5 ký tự, không fuzzy ≤3.

## Lệnh và kết quả kiểm thử thực tế

Môi trường giữ từ Đợt 1: Windows x64, `.venv` Python **3.12.14**, pytest **9.1.1**,
Streamlit **1.66.0**, python-docx **1.2.0**, pdfplumber **0.11.10**. Dependency
theo requirements hiện có; không đổi Python toàn máy hoặc cài package mới.

Tất cả lệnh dưới chạy từ project. Temp được đặt trong thư mục ignored của repo:

```powershell
$env:TEMP = (Resolve-Path '.venv/tmp').Path
$env:TMP = $env:TEMP
```

| Lệnh | Kết quả |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot02-baseline --tb=short` | **169 passed in 5.95s**, kiểm chứng Đợt 1 trước sửa. |
| `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot02-core-fixed tests/test_cv_parser.py tests/test_submission.py tests/test_profile.py tests/test_skill_extractor.py tests/test_matcher.py tests/test_recommender.py --tb=short` | **164 passed in 1.88s** tại thời điểm chạy nhóm liên quan, trước các regression catalog/P02 cuối. |
| `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot02-ui tests/test_app.py --tb=short` | **27 passed in 10.38s**. |
| `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot02-full --tb=short` | **230 passed in 12.12s**, trước regression literal Git/GitHub cuối. |
| `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot02-final --tb=short` | **231 passed in 12.00s**, bản code cuối. Không skip/xfail. |
| Runtime Python: `-m pip --python .venv check` | **No broken requirements found**. |
| `git diff --check` | Không lỗi whitespace. |
| `git diff -- Data/roles.json Data/resources.json modules/skill_extractor.py` | Rỗng: không sửa role/resource/normalizer/Extractor để chiều test. |

AppTest/full suite chạy local ngoài sandbox vì socketpair của event loop đã
bị sandbox chặn ở Đợt 1; không sửa test để né lỗi này. Không cần browser/manual
upload: API `AppTest.file_uploader.set_value((filename, bytes, mime_type))` có
trong bản cài thực tế và được dùng để đi qua deserializer, UploadedFile,
parser/controller và UI thật. Đuôi ngoài PDF/DOCX bị widget giới hạn; parser và
controller vẫn có test UNSUPPORTED_FORMAT cho caller ngoài widget.

Một lần test sớm lỗi setup fixture Windows do pytest đặt ID bằng toàn bộ bytes
DOCX quá dài (160 pass/8 error). Đã đặt IDs mô tả ngắn cho param, giữ nguyên
fixture/assertion; nhóm chạy lại pass. Lần collect-only không cấu hình TEMP từng
có warning cleanup thư mục tạm của sandbox sau exit; các lệnh nghiệm thu đầy đủ
có cấu hình TEMP ở trên và kết thúc exit 0.

## Trạng thái P-ID và đầu vào Đợt 3

| ID | Trạng thái trong phạm vi Đợt 2 |
| --- | --- |
| P02 | **Đã xử lý các ví dụ yêu cầu**; vocabulary chung, canonical độc lập, alias JS/Git/GitHub/GTM và bỏ hai gộp công nghệ sai. Catalog hữu hạn; không coi là nhận diện mọi kỹ năng. |
| P10 | **Đã xử lý parser/error contract**; PDF/DOCX nested table, mã lỗi thật, wrappers tương thích. Chưa OCR. |
| P11 | **Đã kiểm chứng** JD-only yêu cầu CV, không tạo Profile/không báo scan. |
| P19 | **Đã xử lý** validation và placeholder; cho lưu Profile không role, không tự tạo gợi ý role. |
| P24 | **Đã xử lý** state + rerun, nhiều item/undo liên tiếp, unknown widget và đổi hồ sơ. |
| P27 | **Đã mở rộng kiểm thử** controller, upload widget và các nhánh validation/undo; app tiếp tục dùng core. Chưa nghiệm thu bố cục pixel/mobile. |

Hạn chế: mới nghiệm thu local Python 3.12/Windows, chưa chạy Linux CI, Python
3.11, Docker hoặc trình duyệt/mobile. AppTest không kiểm tra native file dialog,
HTTP upload hay pixel layout. Không mở OCR, gap level hoặc lịch theo giờ.

Đầu vào Đợt 3: giữ 231 test làm regression; xây integrity/kiểm tra link, xem xét
12 resource chưa verified và chất lượng URL dùng chung; bổ sung tiếng Việt và
duration có căn cứ. 5 canonical nhận diện mới chưa có resource cần được theo
dõi riêng, không tự biến thành yêu cầu role. Phải giữ resource_keys qua tuần
khi khử trùng và phân biệt kiểm tra HTTP với review nội dung. Chỉ mở rộng alias
khi đồng nghĩa có nghĩa; không dùng fuzzy ngắn để tăng coverage.
