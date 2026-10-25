# Đợt 1 — Khôi phục luồng tích hợp AI Career Coach

Ngày thực hiện: **24/10/2026**, múi giờ Asia/Saigon.
Project: `khắc phục ma trận vấn đề/AI-Career-Coach`.
Nhánh/HEAD lúc bắt đầu: **AI-Specialist / a430250**. Git sạch khi bắt đầu;
không có `AGENTS.md` áp dụng trong các thư mục tổ tiên hoặc project.
Không tạo nhánh, commit, push hay PR; không reset hoặc sửa dữ liệu thật.

## Kết quả

Luồng CV/kỹ năng nhập tay → Profile → Matcher → Recommender → Streamlit đã
được nối và kiểm thử local. Loader đọc đủ **131 role** thực tế, giữ skill
metadata. Số lượng chỉ được dùng trong test nghiệm thu, không nằm trong logic
sản phẩm. Full pytest trên **Python 3.12.14: 169 passed**, không skip/xfail.

## Baseline đã kiểm tra lại

Trước khi sửa, chạy bằng Python 3.10.6 sẵn có trên máy:

```powershell
python -m pytest -q -p no:cacheprovider --ignore=tests/test_cv_parser.py --tb=short
# 7 failed, 125 passed in 1.45s
python -m pytest -q -p no:cacheprovider --tb=short
# ERROR collecting tests/test_cv_parser.py: ModuleNotFoundError: No module named 'docx'
python -c "from modules import calculate_match_score"
# ImportError: cannot import name 'calculate_match_score' from 'modules'
```

Sáu failure Profile gồm năm kỳ vọng viết hoa và một lỗi unknown; failure
Interview là tra `Data Analyst`. Đọc code xác nhận app/Interview chỉ lấy `roles`
từ object, trong khi dữ liệu thật là list. Các lỗi này vẫn tồn tại ở HEAD khởi
đầu. Có cảnh báo dọn console `pyreadline3` của môi trường Python 3.10 sau pytest;
không xuất hiện trong môi trường nghiệm thu 3.12.

## File thay đổi

| File | Nội dung |
| --- | --- |
| `modules/catalog.py` (mới) | Loader chung, đường dẫn `Data/` theo module; hỗ trợ list, object roles/positions, chuyển trường legacy và giữ metadata; lỗi schema/ID rõ ràng. |
| `modules/profile.py` | Nhận diện chính xác từng entry bằng vocabulary/alias; giữ và báo unknown; thêm `build_profile_from_cv` dùng Extractor/merge_skills. |
| `modules/matcher.py` | Dùng loader role chung, giữ nguyên API và thuật toán so khớp. |
| `modules/interview.py` | Dùng loader chung; tra ID/tên Anh/tên Việt/nhãn ghép; phát hiện tên mơ hồ; làm mới cả cache tên khi clear cache. |
| `modules/__init__.py` | Export lazy `build_profile_from_cv`; giữ các API public hiện có. |
| `app.py` | Import API mới; gộp CV với form; hiện kết quả CV/JD có giải thích; dùng match_role và missing_details để tạo roadmap; resolve tài liệu qua các tuần. |
| `tests/test_catalog.py` (mới) | Test fixture các schema, metadata, legacy, dữ liệu sai, đủ role thực tế và độc lập cwd. |
| `tests/test_app.py` (mới) | Import/loader app, AppTest startup, form, CV-only/CV+form, CV/JD, unknown, lỗi upload, điểm đủ skill, shared resource và phỏng vấn. |
| `tests/test_profile.py` | Chốt năm assertion lowercase; thêm alias, unknown chứa substring, override và gộp CV/form. |
| `tests/test_interview.py` | Tra toàn bộ role thật theo ID/tên/nhãn ghép, tên mơ hồ và fixture các dạng catalog. |
| `tests/test_skill_extractor.py` | Đường dẫn test đúng casing `Data/`. |
| `tests/doc-cai-nay-de-test-module-extractor-dung-hon.md` | Đồng bộ ví dụ đường dẫn `Data/`. |
| `docs/interface.md` | Hợp đồng Profile/Extractor/Matcher/Recommender/catalog/Interview và ví dụ tham chiếu resource qua tuần. |
| `docs/progress/dot_01.md` (mới) | Biên bản thực hiện, môi trường, bằng chứng và giới hạn nghiệm thu. |

Không thay đổi `requirements.txt`, `Data/`, normalizer, API Extractor hay thuật
toán khử trùng Recommender. `get_course_recommendations` vẫn được test như caller
legacy; app hiện dùng roadmap trực tiếp.

## Quyết định hợp đồng

1. `normalize_skill` chỉ NFC/lowercase/khoảng trắng, vẫn trả chuỗi cho tên lạ.
   Nhận diện tách biệt bằng vocabulary từ roles và alias chung. Profile giữ
   canonical làm khóa; UI chịu trách nhiệm nhãn hiển thị. Unknown cũng được
   chuẩn hóa và giữ trong cả `skills` lẫn `unrecognized_skills`.
2. Mỗi entry form là một kỹ năng ứng viên tuyên bố. `SQL wizardry` không được
   nhận thành `sql` nhờ substring. CV là văn bản nên dùng `extract_skills` theo
   phrase/boundary; không biến toàn bộ từ chưa nhận diện trong CV thành skill.
3. `build_profile_from_cv` là API bổ sung, giữ đúng năm khóa Profile; kỹ năng CV
   nhận diện được gộp với kỹ năng form qua `merge_skills`. Unknown của form
   không bị bỏ. CV-only tạo Profile có kỹ năng; CV lỗi không làm mất form.
4. App giữ đầy đủ kết quả `match_cv_to_jd`, hiển thị percent và matched/missing.
   Điểm chỉ xét kỹ năng nhận diện trong JD có trong CV; kỹ năng nhập tay không
   bù vào CV để tăng điểm. Không khôi phục TF-IDF/API cũ.
5. App dùng trực tiếp `match_role` cho điểm trọng số và gap; không tự đếm matched
   để suy điểm. `missing` vẫn list[str]; `missing_details` giữ name/weight/level.
   Level chỉ là metadata yêu cầu, chưa phải mức ứng viên.
6. Roadmap giữ nguyên chữ ký/list[dict], ưu tiên bằng missing_details. Renderer
   lập index toàn roadmap và tra resource_keys cho tuần dùng lại tài liệu.
   Chỉ `skills_without_resources` mới là bằng chứng thiếu tài liệu; resources
   tuần hiện tại rỗng vẫn có thể tham chiếu tuần trước.
7. Loader hỗ trợ list và object roles/positions; nếu có cả hai khóa thì roles
   ưu tiên. Không âm thầm bỏ role lỗi hoặc làm mất weight/level. Casing Data/
   được giữ nguyên, mặc định đường dẫn độc lập cwd.
8. Hai tên Việt trong dữ liệu thật bị trùng: “Chuyên viên tổ chức sự kiện”
   (`event_executive`, `event_planner`) và “Chuyên viên chăm sóc khách hàng”
   (`customer_service_executive`, `customer_service_representative`). Tra tên
   trùng gây ValueError hướng dẫn dùng ID hoặc `tên Việt · tên Anh`; tên duy
   nhất tra bình thường. Không sửa dữ liệu hoặc tự chọn role cuối cùng. UI
   dùng ID nên không mơ hồ. API chọn câu hỏi/seed/xen kẽ loại vẫn được giữ.

## Môi trường và lệnh nghiệm thu

Windows x64, Python **3.12.14**, pytest **9.1.1**, Streamlit **1.66.0**,
python-docx **1.2.0**, pdfplumber **0.11.10**. Tất cả dependency trực tiếp được
cài theo đúng `requirements.txt` vào `.venv` của project; không đổi Python toàn
máy. `.venv` và các thư mục temp/test bên trong đã được Git ignore.

Python bundled dùng để tạo môi trường:

```powershell
$runtimePython = 'C:\Users\letrungtanh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $runtimePython -m venv .venv
& $runtimePython -m pip --python .venv install -r requirements.txt
& $runtimePython -m pip --python .venv check
```

`venv` đã tạo interpreter nhưng bước `ensurepip` trả exit 1. Cài bằng pip của
runtime với `--python .venv` giải quyết bootstrap mà không sửa Python gốc.
Lần pip đầu trong sandbox lỗi `NameResolutionError: Failed to resolve pypi.org`;
chạy lại ngoài sandbox tải/cài đủ dependency thành công. `pip check` trả
**No broken requirements found**.

Pytest temp mặc định của sandbox từng lỗi `could not create numbered dir ...`
ở AppData. Chỉ định temp vào `.venv` để tránh lỗi quyền thư mục:

```powershell
New-Item -ItemType Directory -Path '.venv/tmp' -Force | Out-Null
$env:TEMP = (Resolve-Path '.venv/tmp').Path
$env:TMP = $env:TEMP
```

Các lệnh dưới chạy từ project đích, sau khi cấu hình temp như trên:

| Lệnh | Kết quả |
| --- | --- |
| `python -m pytest -q -p no:cacheprovider --ignore=tests/test_cv_parser.py --tb=short` ngay sau sửa bảy lỗi, trước thêm test mới | 132 passed in 1.09s (Python 3.10; chỉ kiểm tra tiến triển, không dùng làm nghiệm thu cuối). |
| `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-core tests/test_matcher.py tests/test_recommender.py tests/test_skill_extractor.py tests/test_profile.py tests/test_catalog.py tests/test_interview.py tests/test_cv_parser.py --tb=short` | **158 passed in 1.43s**, gồm cả 4 test CV Parser PDF/DOCX. |
| `.\.venv\Scripts\python.exe -m pytest -vv -s -p no:cacheprovider --basetemp=.venv/pytest-ui-outside tests/test_app.py -o faulthandler_timeout=30 --tb=short` | **11 passed in 5.77s**; AppTest thực thi Streamlit, thao tác form và kiểm tra kết quả UI/core. |
| `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-full --tb=short` | **169 passed in 5.90s**, full suite, không skip/xfail. |
| `git diff --check` | Không có lỗi whitespace. |

AppTest trong sandbox từng treo ở `asyncio.new_event_loop → _fallback_socketpair
→ socket.accept` (trace từ `faulthandler_timeout=25`). Đã dừng các lần chạy treo
và chạy lại UI/full pytest local ngoài sandbox, không sửa app/test để né lỗi.
Các warning `missing ScriptRunContext` từ harness/bare import là warning của
Streamlit, không có `app.exception` trong các luồng AppTest nghiệm thu.

AppTest chưa có setter uploader được dùng ở test này: test cung cấp file DOCX
thật tại biên `st.file_uploader`, sau đó vẫn chạy parser thật, Profile/Matcher/
Recommender thật và renderer. Đây là giới hạn mô phỏng thao tác chọn file, không
phải skip CV Parser hay chỉ compile/import. Test riêng kiểm tra widget uploader
có mặt khi startup; test PDF/DOCX của parser cũng chạy trong full suite.

## Trạng thái ma trận

| ID | Kết quả Đợt 1 | Phần còn lại |
| --- | --- | --- |
| P02 | **Một phần**: nhận diện/alias dùng chung xuyên CV/Profile/Matcher; unknown không còn bị nhận sai là known. | Mở rộng/rà alias (JS, pandas, MySQL, English; alias không đồng nghĩa) và quyết định vocabulary ở đợt sau. |
| P03 | **Đã xử lý blocker Đợt 1**: canonical NFC/lowercase, nhận diện riêng, năm assertion đồng bộ; display thuộc UI. | Có thể mở rộng mapping nhãn hiển thị; không đổi canonical để trình bày. |
| P07 | **Đã xử lý trong phạm vi hiện hành**: app import/gọi CV/JD đúng API, giải thích percent/matched/missing, gộp CV vào Profile. | Không mở rộng vocabulary hay đo mức thành thạo trong đợt này. |
| P09 | **Một phần**: tra role theo dữ liệu thật, ID/tên/nhãn ghép, xử lý tên Việt trùng; giữ lựa chọn câu hỏi hiện có. | focus_skills, scoring/rubric/quality vẫn chưa triển khai. |
| P12 | **Đã xử lý blocker casing**: test/ví dụ dùng Data/, loader chung độc lập cwd. | Chưa chạy Linux CI trong lượt local; không migration tên folder. |
| P17 | **Một phần**: interface hiện hành đầy đủ Profile/Matcher/Recommender và dữ liệu/tham chiếu qua tuần. | Tài liệu kiến trúc/demo/screenshot nằm ở đợt sau. |
| P27 | **Đã xử lý blocker Đợt 1**: app điều phối core, có AppTest startup và các luồng tích hợp, full pytest pass. | Kiểm tra giao diện trình duyệt/mobile, các nhánh validation/undo rộng hơn ở đợt sau. |

P05 được nối roadmap hiện có như phụ thuộc tích hợp; chưa nghiệm thu toàn bộ
P05 về level/giờ. Các mục P khác ngoài phạm vi không được coi là hoàn thành.

## Phần chưa nghiệm thu và điều kiện Đợt 2

- Python 3.12 local đã nghiệm thu; chưa chạy Python 3.11, Linux CI, Docker hoặc
  kiểm tra bố cục trực quan/mobile. Không coi AppTest là kiểm tra pixel/layout.
- Hai tên Việt trùng phải được caller phân biệt bằng ID/nhãn ghép; dữ liệu thật
  được giữ nguyên. Không còn lỗi tra tên duy nhất hoặc tự chọn nhầm role.
- Đợt 2 bổ sung `parse_document`/mã lỗi rõ ràng, validation form trống/role
  placeholder, nhánh upload/CV không có text và undo/rerun; giữ các API cũ.
- Rà vocabulary/alias dựa trên ý nghĩa thực; không gộp MySQL thành SQL hay tiếng
  Anh chung thành tiếng Anh chuyên ngành chỉ để nhận diện nhiều hơn.
- Giữ 169 test hiện tại làm regression; bổ sung test khi mở rộng hành vi. Cần
  tiếp tục dùng môi trường 3.11/3.12 đầy đủ dependency và chạy full suite.
- Gap theo level và lịch theo giờ chưa triển khai: cần thu thập level ứng viên,
  dữ liệu thời lượng có căn cứ và API bổ sung riêng trước khi mở rộng.

Các file ở bảng thay đổi là tập cần review/commit. Không commit `.venv`, temp
hoặc cache. Không có bước nghiệm thu bắt buộc Đợt 1 nào còn bị chặn bởi dependency.
