# Giao diện tích hợp — Đợt 5

Đợt 5 tổ chức kết quả trong tab Tóm tắt, Khoảng cách, Lộ trình, Tài liệu và Phỏng vấn. `Data/demo_profiles.json` chứa hồ sơ tổng hợp có nhãn; nút dùng mẫu cập nhật đồng bộ widget và snapshot, tăng revision, xóa CV/phiên phỏng vấn cũ. Export dùng hợp đồng ở cuối tài liệu.

Luồng hiện hành: CV PDF/DOCX → văn bản → Extractor → gộp kỹ năng nhập tay →
Profile → Matcher theo role → Recommender → giao diện Streamlit.
CV/JD được đối chiếu riêng bằng `match_cv_to_jd`; kỹ năng nhập tay không được
coi như bằng chứng xuất hiện trong CV khi so với JD.

Các API level, lịch giờ, gợi ý và chấm phỏng vấn Đợt 4 có schema/công thức ở
[assessment_contract.md](assessment_contract.md), là phần hợp đồng của tài liệu
này. `compute_gap`, `build_timed_roadmap`, `suggest_roles`, `score_answer` được
export qua `modules`; các API presence/roadmap cũ bên dưới tiếp tục được giữ.

## Canonical và nhãn hiển thị

`normalize_skill(name: str) -> str` chỉ chuẩn hóa Unicode NFC, chữ thường và
khoảng trắng. Hàm không kiểm tra vocabulary, không giải alias và không trả
`None` cho kỹ năng lạ: `normalize_skill(" ABC ") == "abc"`.

Canonical là khóa đối chiếu giữa các module. Vocabulary chung lấy qua
`modules.catalog.load_skill_vocabulary()`: hợp tên kỹ năng role từ
`Data/roles.json` và list canonical độc lập ở `Data/skill_catalog.json`.
`build_vocabulary(roles)` vẫn chỉ trả vocabulary từ role để tương thích caller.
Catalog nhận diện bổ sung không thay yêu cầu role và không cam kết có resource.
Alias chung đọc từ `Data/skill_aliases.json`, chuẩn hóa cả khóa và đích;
đích alias phải thuộc vocabulary (có test kiểm tra dữ liệu thật).
Ví dụ `Python3 → python`, `Node.js → nodejs`, `Communication → giao tiếp`,
`JS → javascript`, `ML → thuật toán học máy`, `Git/GitHub → git`.
Không mặc định alias `py` khi chưa khai báo trong dữ liệu.

Các canonical độc lập bổ sung: `pandas`, `mysql`, `english`, `google tag manager`,
`.net core`. Không ánh xạ chúng sang `python`, `sql`, `tiếng anh chuyên ngành`,
`google analytics` hoặc `asp.net core`. Gỡ hai alias gộp sai Google Tag Manager
và .NET Core; `GTM → google tag manager` là alias viết tắt chính xác.
Các alias còn lại giữ quy ước sẵn có; không mở rộng theo quan hệ kỹ năng cha/con.
Profile nhập tay, trích CV và CV/JD dùng cùng vocabulary/alias; role matching
chỉ đối chiếu yêu cầu có thật của role. Một JD có pandas/MySQL/English nay được
nhận diện ngay cả khi các kỹ năng này không xuất hiện trong role catalog.

Nhãn dịch/viết hoa để hiển thị thuộc mapping/UI (`display_skill`, `format_role`),
không được dùng để thay canonical trong Profile hoặc khóa resource. Matcher
vẫn giữ tên kỹ năng do role khai báo ở `matched`, `missing`, `missing_details`;
Recommender chuẩn hóa các tên này trước khi tra resource.

`extract_skills(text, vocabulary, aliases=None, fuzzy=False) -> list[str]`
giữ thứ tự xuất hiện, loại trùng, ưu tiên cụm dài và che span đã khớp.
Chỉ trả kỹ năng nhận diện trong vocabulary. `fuzzy` mặc định tắt; khả năng
fuzzy phụ thuộc package tùy chọn `rapidfuzz`. App Đợt 2 không bật fuzzy và không
cài/thêm dependency này. Nhánh fuzzy hiện chỉ xét token/tên đơn từ dài ít nhất
5 ký tự; chuỗi ngắn ≤3 không được fuzzy. Alias JS/ML/GTM luôn là exact matching.

`merge_skills(cv_skills, form_skills, aliases=None) -> list[str]` gộp CV trước,
form sau, chuẩn hóa, giải alias và loại trùng; không loại kỹ năng chưa biết.

## Catalog: role và resource

`modules.catalog.load_roles(path: str | Path | None = None) -> list[dict]`
đọc mặc định `Data/roles.json` theo vị trí module, độc lập cwd. Dạng hỗ trợ:

- List role trực tiếp (dữ liệu hiện tại, 131 role).
- Object `{"roles": [...]}`.
- Object legacy `{"positions": [...]}`; `title` làm tên/ID dự phòng,
  `required_skills` làm `skills` nếu chưa có trường `skills`.

Nếu có cả `roles` và `positions`, `roles` được ưu tiên; `roles` sai kiểu sẽ gây
lỗi, không âm thầm chuyển sang dữ liệu khác. Thiếu/trùng ID, record không phải
object hoặc `skills` không phải list gây `ValueError`. ID chuyển thành chuỗi.
Loader giữ metadata của role và từng skill, bổ sung `name`, `title`, `name_vi`
dự phòng; không rút skill thành tên rồi mất `weight`/`level`. App sắp xếp role
để hiển thị; loader giữ thứ tự dữ liệu. App, Matcher, Profile và Interview dùng
chung quy tắc loader; không hardcode số role trong logic sản phẩm.

Role hiện hành có dạng:

```json
{"id": "sample", "name": "Sample Role", "name_vi": "Vị trí mẫu",
 "skills": [{"name": "python", "weight": 3, "level": 2}]}
```

`Data/resources.json` là object có khóa tên kỹ năng canonical:

```json
{"python": {"skill_name": "python", "category": "technical",
 "resources": [{"id": "python_001", "title": "Tutorial",
 "url": "https://example.org/tutorial", "provider": "Example",
 "type": "course", "language": "en", "cost": "free",
 "level_from": 1, "level_to": 3, "duration_hours": null,
 "verified": true, "last_checked": "2026-10-22"}]}}
```

Mọi đường dẫn mặc định trỏ vào `Data/` đúng casing, độc lập cwd.
`verified` là metadata có sẵn, không phải kiểm tra HTTP ở thời điểm chạy.

### Provenance và chất lượng tài nguyên (Đợt 3)

Giữ cấu trúc mapping/list và toàn bộ ID cũ; cho phép nhiều bản ghi skill dùng
chung URL. Các trường mới được Recommender giữ nguyên từ bản ghi đầu tiên khi
khử trùng. Cần xem từng mapping gốc nếu đánh giá độ phù hợp riêng cho mỗi skill.

| Trường | Ý nghĩa |
| --- | --- |
| `content_review_status` | `reviewed`: đã đọc, phù hợp phạm vi ghi chú; `partial`: chỉ đáp ứng một phần; `unsuitable`: nội dung đã đọc không dạy skill được gắn; `unreviewed`: chưa review mapping; `blocked`: chưa đọc được do chặn truy cập. |
| `content_reviewed_at`, `review_note`, `evidence_locator` | Ngày ISO thực tế, phạm vi/giới hạn và phần trang/PDF/slide đã đọc. Không đặt ngày review nội dung khi chỉ gặp 403. |
| `verification_origin` | `content_read_dot03`, `blocked_dot03`, hoặc `legacy_not_revalidated`. Cờ `verified=true` cũ không được coi là đã review Đợt 3. |
| `access_note` | Tách quyền đọc tài liệu khỏi tài khoản, giấy phép công cụ/lab hoặc tiêu chuẩn đầy đủ có phí. |
| `duration_hours` | Số dương do nhà xuất bản công bố cho **tài nguyên cụ thể**, hoặc `null` nếu chưa biết. Thời gian học dự kiến của nhà xuất bản vẫn là dự kiến, không phải đo năng lực người học. |
| `duration_source`, `duration_basis`, `duration_checked_at` | URL bằng chứng, loại căn cứ, ngày kiểm chứng. `publisher_catalog_minutes`: số phút trong API Microsoft / 60, đối chiếu `duration_catalog_uid`; `publisher_approximate_guide_minutes`: thời gian gần đúng ghi trong hướng dẫn Spring. |
| `estimated_duration_hours` | Ước lượng biên tập riêng, số dương và có `duration_basis`; không thay thế `duration_hours`. Chưa có ước lượng biên tập nào trong dữ liệu Đợt 3. |

`verified=true` mới chỉ khẳng định đã kiểm tra nội dung trong phạm vi ghi chú,
kể cả `partial`; không cam kết đạt level của role hay kết nối HTTP hiện tại.
`unsuitable`/`blocked` phải có `verified=false`. `last_checked` cũ được giữ nếu
chưa kiểm tra lại; không dùng nó thay ngày review nội dung. Báo cáo HTTP riêng
ở `docs/reports/dot03_links_*.json` ghi từng lần thử thực tế và UTC.

`level_from`/`level_to` là phạm vi tài nguyên, không chứng nhận trình độ sau học.
`language` mô tả nội dung thực đọc (`vi`, `en`, `multilingual`), không suy từ
locale trong URL. `cost` nhận `free`, `freemium`, `paid`, `unknown`; bài miễn phí
có thể cần phần mềm trả phí để thực hành. Không suy giờ từ số trang, reading
time tự động, `learning_time_months` của role hoặc mức level.

Integrity offline: `modules.data_quality.audit_project()` trả `errors`,
`warnings`, `stats`, `top30`; không gọi mạng. Role skill thiếu tài liệu là lỗi;
canonical chỉ dùng nhận diện chưa có resource là warning. Tên skill ở câu hỏi
có thể là alias hợp lệ nhưng phải giải được về yêu cầu của đúng role. Top 30
đếm số role chứa skill, mỗi role tối đa một lần, tie theo canonical NFC tăng dần.

CLI kiểm tra URL chạy tay: `python scripts/check_links.py --timeout 10 --workers 4`.
Mỗi URL chuẩn hóa chỉ được GET một lần, tối đa 5 redirect, workers 1–8, timeout
kết nối/đọc hữu hạn; đây là timeout từng thao tác, không phải deadline tổng.
Chỉ đọc mẫu HTML 8 KiB. Không có retry HEAD/GET; redirect hợp lệ vẫn phát sinh
request tới đích. Báo cáo phân loại reachable/redirect/error/timeout/blocked;
401/403/429/451 hoặc dấu hiệu chặn bot là **unverified**, không kết luận link
hỏng. 200 chỉ là `transport_only`. Script không sửa JSON nguồn, không ghi đè
catalog kể cả khi truyền `--output` trùng đường dẫn. Live check không nằm trong CI.

Đợt sau phải giữ `null` dưới nhãn “chưa xác định”, không biến thành 0/8 giờ
hoặc tổng tuần chắc chắn; chỉ cộng giờ các tài nguyên đã chọn sau dedup theo
`resource_keys`. Không cộng tất cả phương án thay thế hay toàn bộ nguồn dùng
chung cho mỗi skill. Trạng thái `unsuitable`, `blocked`, `unreviewed` cần được
hiển thị/lọc rõ ở lớp lựa chọn mới. `build_roadmap` hiện vẫn giữ hợp đồng trả
tất cả tài liệu và metadata; chưa tự lọc/xếp hạng lại dựa trên provenance.

## Profile

`build_profile(form_data: dict | None = None, skills: list[str] | str | None = None) -> dict`

`form_data` nhận các trường tùy chọn:

| Trường | Kiểu | Ý nghĩa |
| --- | --- | --- |
| `skills` | str hoặc list[str] | Tách bằng dấu phẩy, chấm phẩy, xuống dòng. Đối số `skills` tường minh ghi đè trường này. |
| `interests` | str hoặc list[str] | Tách như danh sách kỹ năng. |
| `experience` | str | Giữ văn bản, gộp khoảng trắng; không tách theo dấu phẩy. |
| `levels` | dict[str,int] | Khai báo tường minh 0–3, chuẩn hóa canonical/alias; không nhận bool, float, tên rỗng hoặc trùng sau canonical. |

Profile so tên từng kỹ năng nhập tay với vocabulary sau normalize/alias.
Không dùng substring để biến `SQL wizardry` thành kỹ năng `sql` đã nhận diện.
Entry chưa biết vẫn chuẩn hóa, giữ trong `skills` và báo riêng. Các tiền tố
`interesting:`, `interest:`, `sở thích:` chuyển entry sang sở thích.

Profile luôn có đúng các khóa:

| Khóa | Kiểu | Ý nghĩa |
| --- | --- | --- |
| `skills` | list[str] | Canonical đã nhận diện và entry chưa biết đã chuẩn hóa; loại trùng, sắp xếp không phân biệt hoa/thường. |
| `interests` | list[str] | Làm sạch, loại trùng, gồm mục chuyển từ kỹ năng; giữ cách viết để hiển thị. |
| `experience` | str | Kinh nghiệm dạng văn bản đã làm sạch. |
| `unrecognized_skills` | list[str] | Tập con của `skills`, chưa thuộc vocabulary sau alias. |
| `moved` | list[dict[str,str]] | `{"item": "games", "from": "Kỹ năng", "to": "Sở thích"}`. |
| `levels` | dict[str,int] | Chỉ giữ mức đã khai báo; thiếu khóa là unknown, không suy từ tên trong CV. Level dương bổ sung presence; level 0 không tự bổ sung presence. |

`None`, mapping rỗng hoặc giá trị thiếu tạo Profile rỗng theo schema trên.

`build_profile_from_cv(form_data: dict | None = None, cv_text: str = "") -> dict`
là API bổ sung cho luồng app, giữ nguyên schema Profile. Trích CV bằng
vocabulary/alias chung, gộp với Profile nhập tay qua `merge_skills`, loại trùng
và sắp xếp. CV-only có kỹ năng nếu nhận diện được. Entry chưa biết của form vẫn
được giữ/báo; các từ văn xuôi không nhận diện trong CV không tự biến thành kỹ
năng ứng viên tuyên bố. CV trống không làm mất kỹ năng nhập tay.

UI mặc định giữ kỹ năng chưa biết và cho phép người dùng bỏ chọn trước khi
đưa danh sách kỹ năng hiệu lực vào Matcher.

`undo_profile_move(profile, index, *, original_interests=()) -> dict` trả bản
sao Profile sau khi hoàn tác một item. Chuẩn hóa/giải alias kỹ năng được khôi
phục, bổ sung `unrecognized_skills` khi cần, loại trùng. Không xóa sở thích được
nhập tường minh trong `original_interests` hoặc còn được tham chiếu bởi item
`moved` khác. Giữ cả `levels` và năm khóa cũ của Profile.

## CV Parser

`parse_document(source, filename=None) -> dict` được export qua `modules`:

```python
{"text": "Python developer", "error_code": None, "message": ""}
```

`source` là path str/Path, binary file-like hoặc None. `filename` ghi đè tên
file-like/path để chọn parser; đuôi `.pdf`/`.docx` không phân biệt hoa/thường.
File-like có seek được rewind trước khi đọc; parser không đóng stream của
caller. Nội dung text chuẩn hóa NFC, giữ thứ tự paragraph/table và bảng lồng
nhau trong DOCX; ô bảng gộp chỉ được đọc một lần.

| error_code | Điều kiện |
| --- | --- |
| `None` | Đọc thành công và có text sau khi trim. |
| `NO_FILE` | Không có source, chuỗi path rỗng hoặc path không tồn tại. |
| `UNSUPPORTED_FORMAT` | Thiếu đuôi hoặc đuôi ngoài PDF/DOCX. Không đoán định dạng bằng nội dung. |
| `EMPTY` | Tệp 0 byte, DOCX chỉ có khoảng trắng, hoặc PDF đọc được nhưng không trích được text và không đủ bằng chứng trang ảnh. |
| `UNREADABLE` | Lỗi mở/đọc/giải mã, file hỏng, bảo vệ, stream đóng/không dùng được hoặc nội dung không đúng đuôi. |
| `SCANNED_PDF` | Đọc PDF thành công, không có text và **mọi trang** có raster image, không có text character. Đây là bằng chứng PDF dạng ảnh; chưa làm OCR. |

Mọi failure có `text=""`, kèm `message` thân thiện. PDF trắng hoặc chỉ có nét
vẽ là EMPTY, không được kết luận scan. PDF không giải mã được là UNREADABLE.
PDF có cả ảnh và text dùng phần text đọc được; không gán mã scanned.

`_read_pdf`/`_read_docx` là reader nội bộ có thể raise, dùng chung cho API mới
và wrappers. `parse_document` phân loại trực tiếp từ reader và metadata trang,
không đoán nguyên nhân từ chuỗi rỗng của wrapper đã nuốt lỗi.
Giữ `extract_text`, `extract_text_from_pdf`, `extract_text_from_docx` cho caller
cũ: trả string, lỗi đọc thành `""`; `extract_text` vẫn raise ValueError cho
đuôi không hỗ trợ. `extract_text_from_pdf` vẫn export như trước.

## Validation và state giao diện

`modules.submission.prepare_submission(form_data, source=None, *, filename=None,
jd_text="") -> dict` chuẩn bị ứng viên kết quả trước khi ghi session_state:
`accepted`, `profile`, `document`, `cv_extraction`, `cv_jd_result`,
`original_interests`, `errors`. Không chỉnh sửa state của UI.

- Ít nhất một kỹ năng sau khi tách/loại rỗng/chuyển interest, **hoặc** CV có text
  hợp lệ mới tạo Profile. Kỹ năng chưa biết vẫn là khai báo hợp lệ. Chỉ có JD,
  sở thích, kinh nghiệm, dấu phân cách hay khoảng trắng không tạo Profile.
- Không file + form kỹ năng hợp lệ tạo Profile bình thường. JD-only yêu cầu CV
  hợp lệ, không báo scan. CV lỗi/rỗng/sai định dạng được báo theo parser; nếu
  vẫn có kỹ năng form hợp lệ thì có thể lưu Profile form cùng thông báo lỗi CV.
- CV-only hợp lệ được lưu dù chưa chọn role. CV có text nhưng không nhận diện
  kỹ năng vẫn được lưu để xem, không tự dựng skill hoặc kết quả role khi danh
  sách kỹ năng hiệu lực rỗng. JD lỗi nhận diện không làm mất Profile hợp lệ.
- Selectbox role có `index=None` và placeholder. Chưa chọn role vẫn tạo Profile
  và đối chiếu CV/JD, nhưng không có điểm role, roadmap hay phỏng vấn. Chọn role
  và gửi lại form hoặc bấm nút chọn trong gợi ý mới có kết quả theo role.
  `suggest_roles` hiển thị lý do/điểm heuristic; không tự chọn role đầu tiên.
- Khi `accepted=True`, app ghi đồng bộ Profile/role/CV/comparison, tăng
  `profile_revision`, lưu sở thích nhập tường minh, reset widget unknown và
  phiên/câu trả lời phỏng vấn trước. Kết quả CV/JD cũ không đi theo hồ sơ mới.
- Khi `accepted=False`, chỉ cập nhật `submission_errors` và
  `submission_rejected`; giữ nguyên snapshot đã lưu. Có nhãn rõ kết quả đang
  hiển thị là hồ sơ trước, không gán lỗi/bản nháp mới cho kết quả cũ. Lần gửi
  hợp lệ tiếp theo thay toàn snapshot và xóa thông báo lỗi cũ.
- Undo ghi Profile mới rồi `st.rerun()` để không giữ thông báo item đã hoàn tác.
  Checkbox unknown dùng khóa theo revision + canonical skill, giữ lựa chọn khi
  undo làm thay thứ tự danh sách, và reset ở hồ sơ mới. Nhiều item/undo liên tiếp
  được kiểm tra bằng AppTest.

## Matcher

`match_role(skills, role) -> dict`

Đầu vào là kỹ năng ứng viên và role đầy đủ metadata từ loader. Chuẩn hóa và
giải alias trước khi đối chiếu presence. `percent` là phần trăm tổng trọng số
yêu cầu có trong kỹ năng ứng viên, làm tròn một chữ số thập phân.
Đây chưa phải điểm mức độ thành thạo. Role rỗng kỹ năng cho `0.0`.

```python
{
    "role_id": "sample", "role_name": "Sample Role", "percent": 60.0,
    "matched": ["python"], "missing": ["sql"],
    "missing_details": [{"name": "sql", "weight": 2, "level": 1}],
}
```

`matched`/`missing` là list[str] theo thứ tự role. `missing_details` cùng thứ tự
`missing`, giữ `weight` (mặc định 1), `level` (mặc định None). Skill role có thể
là chuỗi legacy hoặc object; tên rỗng/trùng sau chuẩn hóa, weight không dương
hoặc không hữu hạn gây lỗi rõ ràng. Không suy ra level ứng viên từ việc kỹ năng
được nhắc trong CV. App lấy trực tiếp đầu ra để hiển thị điểm/gap và truyền
metadata cho Recommender.

`match_cv_to_jd(cv_text, jd_text) -> dict`

```python
{"percent": 50.0, "cv_skills": ["python"], "jd_skills": ["python", "sql"],
 "matched": ["python"], "missing": ["sql"]}
```

Trích kỹ năng hai văn bản bằng vocabulary/alias chung. Điểm là tỷ lệ số kỹ năng
duy nhất nhận diện trong JD cũng có trong CV; không phải độ tương đồng từ ngữ,
không dùng TF-IDF. `matched`/`missing` theo thứ tự JD. Văn bản trống hoặc một
bên không nhận diện được kỹ năng gây `ValueError`; UI hiển thị lỗi. Thuật ngữ
chưa biết không nằm trong mẫu số; điểm không đại diện mọi yêu cầu ngoài
vocabulary. Kỹ năng nhập tay không bổ sung vào CV cho phép so này.

## Recommender và tham chiếu qua tuần

`build_roadmap(missing, resources, weeks=4, *, missing_details=None) -> list[dict]`

Truyền nguyên `missing` và `missing_details` từ Matcher. Recommender chuẩn hóa,
loại trùng skill; metadata giúp ưu tiên weight giảm dần, ổn định khi bằng nhau.
Chia cân bằng thành `min(weeks, số skill)` tuần; không có gap trả `[]`.
`weeks` phải là số nguyên dương. Chưa lập lịch theo giờ/level.

Mỗi tuần có `week`, `skills`, `resources`, `resource_keys`,
`skills_without_resources`. Khử trùng tài liệu theo ID hoặc URL chuẩn hóa, kể cả
liên kết bắc cầu; giữ metadata từ bản đầu tiên, bổ sung `key` và `skills`.
Resource không có ID hay URL HTTP(S) sử dụng được bị bỏ qua. Inputs không bị sửa.

Tài liệu chỉ xuất hiện trong `resources` của tuần đầu liên quan. Mỗi skill ở
`resource_keys` có danh sách khóa tài liệu, có thể trỏ tới tài liệu tuần trước.
Ví dụ một tài liệu chỉ có ID, dùng chung cho python và sql:

```python
[
    {"week": 1, "skills": ["python"],
     "resources": [{"key": "id:shared", "id": "shared", "title": "Tutorial",
                    "skills": ["python", "sql"]}],
     "resource_keys": {"python": ["id:shared"]}, "skills_without_resources": []},
    {"week": 2, "skills": ["sql"], "resources": [],
     "resource_keys": {"sql": ["id:shared"]}, "skills_without_resources": []},
]
```

Caller tạo index từ **toàn bộ roadmap**, rồi tra qua `resource_keys`:

```python
catalog = {r["key"]: r for week in roadmap for r in week["resources"]}
for week in roadmap:
    for skill, keys in week["resource_keys"].items():
        documents = [catalog[key] for key in keys]
```

`resources == []` của một tuần không có nghĩa thiếu tài liệu. Chỉ dùng
`skills_without_resources` để báo thiếu. UI hiển thị tài liệu mới và liên kết
đã giới thiệu ở tuần trước; không tạo bản ghi resource trùng để chữa hiển thị.

`get_course_recommendations(missing_skills) -> list[dict]` tiếp tục phục vụ
caller cũ bằng adapter roadmap một tuần. Giữ metadata, bổ sung `course_name`,
`link`, `resource_id`, `skills_achieved`. App hiện gọi roadmap trực tiếp.

## Interview

Giữ cách gọi cũ, mở rộng `get_questions(role_id, n=5, seed=None, focus_skills=None)` và
`generate_interview_questions(missing_skills, max_per_skill=2, *, role=None)`.
Tra được ID, tên Anh, tên Việt duy nhất và nhãn `tên Việt · tên Anh`, không phân
biệt hoa/thường, khoảng trắng hay Unicode tổ hợp. `get_questions` vẫn trả bản
sao câu hỏi công khai, xen kẽ loại câu hỏi, không lộ rubric.

Dữ liệu thật có tên Việt trùng cho hai cặp ID: `event_executive`/`event_planner`
và `customer_service_executive`/`customer_service_representative`. Dùng tên
trùng gây `ValueError` hướng dẫn chọn ID hoặc nhãn ghép; không tự chọn nhầm ngân
hàng. UI dùng ID. Đợt 4 ưu tiên gap và chấm rubric sau submit theo
[assessment_contract.md](assessment_contract.md); câu chưa có rubric trả unavailable,
không điểm 0 giả. Quyền mở đáp án ở luồng UI được kiểm tra bằng AppTest.

## Export và giao diện Đợt 5

Giao diện kết quả dùng năm tab: `Tóm tắt`, `Khoảng cách`, `Lộ trình`, `Tài liệu`,
`Phỏng vấn`. Hồ sơ mẫu trong `Data/demo_profiles.json` phải có
`synthetic: true`; nút chọn mẫu cập nhật widget và snapshot cùng revision,
role, CV comparison và phiên phỏng vấn.

`modules.export.export_report(profile, gap, roadmap, format="markdown") -> str`
nhận Profile mapping, kết quả `compute_gap`, kết quả `match_role` hoặc `None`,
cùng timed roadmap mapping, weekly roadmap list hoặc list rỗng. `format` chỉ
nhận `markdown`/`csv`; giá trị khác raise `ValueError`, Profile không phải
mapping raise `TypeError`.

CSV dùng standard-library `csv` và schema cột ổn định:
`section, role_id, skill, required, current, gap, priority, status, score,
week, hours, resource_key, title, url, duration_kind, duration_hours, source,
note`. Chuỗi bắt đầu bằng `=`, `+`, `-`, `@` sau khoảng trắng đầu được prefix
apostrophe để giảm rủi ro formula injection; dữ liệu numeric giữ dạng numeric.
Unicode và quoting theo RFC CSV. Resource key dùng chung trong weekly roadmap
chỉ xuất một lần.

Markdown chứa skills/interests/levels khai báo, gap hoặc presence score, nguồn
resource, unresolved/unknown duration và giới hạn; không xuất toàn văn CV.
Export sinh ở local khi người dùng bấm download, không lưu report ở server.
