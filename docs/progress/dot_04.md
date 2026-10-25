# Đợt 4 — Level, lịch giờ, gợi ý role và phỏng vấn theo gap

Thực hiện local ngày **24/10/2026**, Windows / Python **3.12.14**, nhánh
**AI-Specialist**, HEAD **a430250**. Không đổi nhánh, reset, stage, commit,
push hoặc tạo PR. Các thay đổi Đợt 1–3 đang có trong working tree được giữ.
Không thấy AGENTS.md áp dụng trong project/các thư mục cha đã kiểm tra.

Đã đọc interface, data_quality, tiến độ 01–03, báo cáo ma trận và code/dữ liệu
hiện hành. Prerequisite chạy lại: **282 passed in 15.30s**, gồm app khởi động,
loader list 131 role, Profile unknown/alias, app dùng core, parser/upload/undo,
integrity và tham chiếu resource xuyên tuần. Không cần chữa bù nền Đợt 1–3.

## Kết quả

Full suite bản cuối: **362 passed in 18.03s**, không skip/xfail. Thêm **80
test** cho các API/luồng mới. Không thêm dependency, LLM, embedding hoặc dịch
vụ trả phí. API và dữ liệu chạy offline; chỉ tra tài liệu chính thức bằng web
tool trong lúc review nội dung câu hỏi, không có request mạng trong scoring,
ranking, planner hoặc pytest.

- Profile thêm `levels`, giữ năm khóa cũ. Dương thì bổ sung presence; 0 không
  tự thêm presence, tên từ CV không tự có level. Chuẩn hóa/alias, từ chối bool,
  float, ngoài 0–3 và trùng canonical. Test cấu trúc thêm khóa được phép, vẫn
  giữ assertion cho mọi khóa cũ.
- `compute_gap` trả mọi gap về level, kể cả skill đã có nhưng chưa đạt yêu
  cầu. Level bỏ trống **chỉ trong API này** được tính 0. UI có mode riêng và
  checkbox xác nhận quy ước trước khi gọi; mode presence tiếp tục match_role.
- `build_timed_roadmap` là API mới trả dict, tách khỏi build_roadmap trả list.
  Chọn theo level và review metadata, xếp priority ổn định; budget từng tuần
  không vượt giới hạn, tài liệu dài chia segment cùng key. Sourced hours,
  editorial estimate và unknown là ba trạng thái riêng.
- Danh tính chung theo ID/URL chỉ phân bổ một lần; mapping thiếu giờ có thể
  dùng giờ có nguồn từ mapping khác. Giờ công bố ưu tiên hơn estimate; số giờ
  cùng loại mâu thuẫn trở thành unknown. Giữ resource_keys của mọi skill và
  duration_evidence chỉ rõ căn cứ thực sự dùng.
- `suggest_roles` đọc catalog thật, trả matched/missing/reasons và điểm
  heuristic, không tự chọn role. Nút chọn cập nhật snapshot **và widget role**
  trước rerun, giữ đúng lựa chọn khi gửi lại hồ sơ. Interest-only dùng được ở
  API; validation form vẫn giữ điều kiện kỹ năng/CV của Đợt 2.
- `get_questions(..., focus_skills=None)` giữ behavior cũ với None, ưu tiên
  câu cho skill gap rồi bù câu role, không lặp ID và tái hiện theo seed.
- `score_answer` dùng rubric riêng từng câu; trả criteria/feedback sau submit.
  Không có rubric được review thì score=null/unavailable, không chấm 0 giả.
  Public question không chứa đáp án, red_flags, rubric hoặc review note private.

Đã so AST với bản lưu đầu đợt: **match_role, match_cv_to_jd, build_roadmap,
get_course_recommendations không đổi thân hàm/chữ ký**. `modules/skill_extractor.py`
và `Data/roles.json` không có diff với HEAD. Không sửa resource/duration/alias
để làm lịch thật trông đầy đủ; giữ casing Data/.

## Schema và công thức

Hợp đồng đầy đủ được chốt trước khi nối UI tại
[assessment_contract.md](../assessment_contract.md), được tham chiếu như một
phần của [interface.md](../interface.md). Interface cập nhật cả Profile,
validation/state và mở rộng Interview, không giữ mô tả “chưa có suggest_roles”.

Profile có skills, interests, experience, unrecognized_skills, moved, **levels**.
Các level không khai báo vẫn không có trong dict, không tự chèn 0 ở Profile.
Form dùng JSON và từ chối khóa trùng trước khi JSON parser ghi đè; draft lỗi
không thay hồ sơ hợp lệ trước đó. Undo giữ levels, các widget cũ tiếp tục có
regression. Hồ sơ mới/role/mode/gap khác reset phiên phỏng vấn tương ứng.

Gap:

```text
items = [{skill, required, current, gap, priority, status}]
gap = max(0, required-current)
priority = weight*gap
match_percent = round(100 * sum(weight*min(current/required,1)) / sum(weight), 1)
```

Percent chỉ tính required>0, giới hạn 0–100; role rỗng 0 và list rỗng.
Status là missing/current=0, below_required hoặc met. Required/current int
0–3; weight dương hữu hạn, thiếu weight mặc định 1 theo Matcher. Required=0
không vào mẫu số, kể cả weight rất lớn. Không đổi ý nghĩa percent presence.

Timed result có `phases[{week,hours,segments[{resource_key,hours,part,duration_kind}]}]`,
`resources` index, `resource_keys`, `level_coverage`, `total_weeks`, `known_weeks`,
`total_known_hours`, `total_estimated_hours`, `total_planned_hours`,
`is_estimated`, `unresolved`, `unknown_duration`, `completion_basis`.

Chỉ mapping reviewed/partial với verified=true được xét; cần phủ các mức
current+1..required. Trong cùng mức: reviewed trước partial, giờ công bố trước
estimate có căn cứ trước unknown, rồi bao phủ nhiều mức hơn và thứ tự catalog.
Partial vẫn unresolved. Các lỗi thiếu resource/review, level mismatch, thiếu
giờ/provenance hoặc conflict đều có reason. Có unresolved thì total_weeks=null;
known_weeks chỉ là phần đã phân bổ. Nếu dùng estimate có căn cứ và không có
unresolved, số tuần là dự kiến với is_estimated=true. Không suy giờ theo level,
số trang hay mặc định 8 giờ/resource; 8 giờ/tuần là budget.

Ranking: S=weighted presence percent/100, I=tỷ lệ interest duy nhất khớp cụm
theo ranh giới từ trong từng tên Anh/Việt/skill role. Không cho cụm nối qua hai
trường độc lập tạo match giả. Cả hai tín hiệu: 100*(0.8*S+0.2*I); chỉ skills:
100*S; chỉ interests: 100*I. Làm tròn một chữ số, tie theo role_id; bỏ score=0.
Không tín hiệu trả []; top_k=0 trả []; bool/âm/sai kiểu gây lỗi. Đây không là
xác suất được tuyển hoặc điểm level.

## Review câu hỏi và giới hạn chấm

Giữ **752/752 ID, thứ tự câu và ngân hàng role**. Chỉ sửa nội dung 6 câu demo
thành tình huống cụ thể và thêm rubric; 12 câu demo còn lại giữ template.

| Role | Câu reviewed có rubric | Template/unavailable |
| --- | --- | ---: |
| backend_developer_java | q02 Spring DI/layer/validation, q03 REST tạo đơn | 5 |
| data_analyst | q01 grain/join/đối soát, q02 Power BI model/filter context | 4 |
| sales_executive | q01 khám phá nhu cầu/bước tiếp theo, q03 chất lượng lead/kênh | 3 |

Rubric private ở `Data/interview_rubrics.json`, có review_status/date/note,
sources và criteria {id,label,points,groups}. Tổng trọng số 10; mỗi criterion
đòi đủ các nhóm khái niệm AND, trong nhóm là các cách diễn đạt OR. Không tạo
rubric từ việc đếm độ dài hoặc so nguyên câu mẫu. Chấm độc lập từng ý, nêu
ý đạt/thiếu; rỗng có 0 khi rubric sẵn sàng. ID sai/trùng báo lỗi; câu thiếu
rubric/quality phù hợp, rubric hỏng hoặc thiếu file trả unavailable/None.

Review nội bộ dựa trên nội dung từng câu và nguồn đã đọc:

- [Spring constructor injection](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired.html).
- [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html), phần POST, 201, 400.
- [SQL joins](https://learn.microsoft.com/en-us/sql/relational-databases/performance/joins?view=sql-server-ver17).
- [Power BI star schema/measures](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema).
- [Dynamics lead qualification](https://learn.microsoft.com/en-us/dynamics365/sales/qualify-lead-convert-opportunity-sales)
  và [nguồn tạo lead](https://learn.microsoft.com/vi-vn/training/modules/manage-leads-dynamics-365-sales/2-create-leads).

Không gán tên reviewer hoặc giả review của chuyên gia độc lập. Điểm là khả
năng nhắc các nhóm khái niệm trong rubric; không xác minh tính đúng của toàn
bộ lập luận, thành tích, tính nhất quán hay năng lực thực. Có thể bỏ sót diễn
đạt khác hoặc cho điểm câu chỉ liệt kê khái niệm. Phủ định chỉ nhận diện cục
bộ, không hiểu ngữ nghĩa đầy đủ. Các giới hạn này hiện trong feedback/UI.
Red flags cũ là gợi ý tham khảo, không tự biến thành trừ điểm máy chấm.

**6/752 câu có scoring; 746 chưa có**, gồm 12 template trong demo và 734 câu
ngoài phạm vi. Không đánh reviewed hàng loạt. Integrity offline bổ sung kiểm
tra foreign key rubric, criteria, ngày và nguồn. Review nội dung một câu không
bắt buộc phải có machine rubric; khi thiếu, API vẫn trả unavailable.

## Đối chiếu dữ liệu thật và phần còn thiếu

[dot04_demo_assessments.json](../reports/dot04_demo_assessments.json) ghi timestamp,
môi trường và hai probe API/role: levels rỗng và levels khai báo một phần bằng
fixture. Không là CV/người dùng thật; API levels rỗng được gọi với chủ ý current=0.
Tất cả đều có total_weeks=null, không sửa metadata tài liệu để thay kết quả.

| Role | Giờ có nguồn với levels={} | Giờ có nguồn với fixture khai báo một phần | Tổng tuần |
| --- | ---: | ---: | --- |
| backend_developer_java | 3.3833 | 0.9333 | null |
| data_analyst | 2.9833 | 0.3500 | null |
| sales_executive | 1.9333 | 1.9333 | null |

Giờ giảm khi mức cần nâng cao hơn phạm vi tài liệu nhập môn; không được dùng
intro level 1 để mặc nhiên đạt level 2/3. Giờ trên là tổng tài liệu đã chọn,
không là thời gian hoàn thành nghề. Nguồn REST C# khác stack Java được ghi rõ
review_note và hiện trong UI; planner không suy stack/prerequisite từ văn xuôi.
Tài liệu dùng chung không nhân giờ theo skill. Cả ba còn thiếu review/level
coverage và nhiều duration; 432 record tài nguyên toàn catalog vẫn null,
không có ước lượng biên tập thực được thêm. 5 skill nhận diện độc lập thiếu
resource vẫn warning riêng. Integrity hiện tại **0 errors**, 5 warning đó.

## Lệnh và kết quả

Chạy từ root repo, dùng `.venv` Python 3.12.14, Streamlit 1.66.0, pytest 9.1.1;
dependency cũ sẵn có, không thay Python toàn máy. Full suite đặt TEMP/TMP như sau:

```powershell
$env:TEMP = (Resolve-Path '.venv/tmp').Path
$env:TMP = $env:TEMP
```

| Lệnh | Kết quả thực tế |
| --- | --- |
| `.\.venv\Scripts\python.exe -X utf8 -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot04-baseline --tb=short` | 282 passed in 15.30s, trước sửa. |
| `.\.venv\Scripts\python.exe -X utf8 -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot04-core tests/test_assessment.py tests/test_timed_roadmap.py tests/test_profile.py tests/test_matcher.py tests/test_recommender.py tests/test_interview.py --tb=short` | 187 passed in 2.01s, phiên bản core đầu. |
| `.\.venv\Scripts\python.exe -X utf8 -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot04-ui-regression tests/test_app.py tests/test_submission.py tests/test_data_integrity.py --tb=short` | 68 passed in 16.05s. |
| `.\.venv\Scripts\python.exe -X utf8 -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot04-ui-new tests/test_app_assessment.py --tb=short` | 6 passed in 7.99s, trước bổ sung edge assertion cuối; được chạy lại trong full suite. |
| `.\.venv\Scripts\python.exe -X utf8 -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot04-affected tests/test_assessment.py tests/test_timed_roadmap.py tests/test_interview_assessment.py tests/test_data_integrity.py tests/test_matcher.py tests/test_recommender.py tests/test_skill_extractor.py tests/test_profile.py tests/test_submission.py tests/test_interview.py --tb=short` | 257 passed in 2.58s, trước các edge case bổ sung cuối. |
| `.\.venv\Scripts\python.exe -X utf8 -m pytest -q -p no:cacheprovider --basetemp=.venv/pytest-dot04-complete --tb=short` | **362 passed in 18.03s**, code/test cuối, không skip/xfail. |
| `audit_project()` | 0 errors, 5 warning recognition-only; có kiểm tra rubric. |
| So 752 question ID/thứ tự/role bank với HEAD | Giữ nguyên toàn bộ. |
| So AST 4 API cũ với snapshot đầu Đợt 4 | Không đổi thân hàm/chữ ký. Extractor/roles không diff HEAD. |
| Pip runtime local: `python -m pip --python .venv check` | No broken requirements found. |
| `git diff --check` | Không lỗi whitespace. |

80 test mới: 29 assessment/Profile/ranking; 32 timed roadmap; 13 focus/rubric/
integrity; 6 AppTest. Có weighted percent, required=0, alias duplicate/invalid,
unknown CV levels, shared resource/conflict/unknown/estimate, ngân sách phân số,
resource dài, level mismatch, catalog thật, top_k/tie/no-network, answer rỗng/
không liên quan/unavailable, không lộ metadata private, consent level, snapshot
lỗi và đồng bộ widget role. Regression cũ gồm CV Parser, upload, undo và API
presence/roadmap đều chạy trong full suite; không chỉ compile/import.

Chưa chạy Linux/Python 3.11, Docker, native browser/mobile hoặc nghiệm thu bố
cục. Không có blocker môi trường cho full local Python 3.12. Chưa thẩm định
rubric độc lập hoặc đo độ chính xác trên câu trả lời thực tế.

## P-ID và đầu vào Đợt 5

| ID | Trạng thái phạm vi Đợt 4 |
| --- | --- |
| P04 | Đã có input level, compute_gap và UI tách presence/level, unknown/consent rõ, regression. Đây là tự đánh giá, chưa chứng minh năng lực. |
| P05 | Đã có planner theo giờ, budget, dedup, partial/unknown/estimate và UI. Dữ liệu thời lượng/level vẫn một phần; không nghiệm thu lịch hoàn chỉnh cho role thật. |
| P08 | Đã có suggest_roles local, công thức/thành phần chuẩn hóa, reasons/tie/no-signal và chọn role tường minh. Chưa đo chất lượng xếp hạng bằng dữ liệu người dùng. |
| P09 | Đã có focus gap, seed/bù câu, private/public boundary, scorer rubric và fallback. 6 câu có rubric nội bộ; phần nội dung/chấm điểm toàn bank còn tiếp tục review. |

Đợt 5 có thể dùng các API/schema ổn định này để bố trí UI/export/demo; cần giữ
unknown/null/partial trong báo cáo, không biến known_weeks thành tổng tuần.
Mở rộng nguồn theo đúng level/stack và rubric có thẩm định trước khi tuyên bố
lộ trình hoàn chỉnh hoặc chất lượng đánh giá năng lực. Chưa tạo hồ sơ mẫu UI,
export, release, LLM hoặc giao diện hoàn thiện.

## File cần commit khi người dùng quyết định

Phần riêng Đợt 4 (không tự stage/commit):

- `app.py`; `modules/__init__.py`, `profile.py`, `matcher.py`, `recommender.py`,
  `interview.py`, `submission.py`, `data_quality.py`; mới `modules/levels.py`,
  `modules/timed_planner.py`.
- `Data/interview_rubrics.json`; ba bank `Data/interview_question/part_01_software.json`,
  `part_02_data_ai.json`, `part_06_sales_customer_ecommerce.json`.
- `tests/test_profile.py`; mới `tests/test_assessment.py`, `test_timed_roadmap.py`,
  `test_interview_assessment.py`, `test_app_assessment.py`.
- `docs/interface.md`, `docs/assessment_contract.md`, `docs/data_quality.md`,
  `docs/reports/dot04_demo_assessments.json`, `docs/progress/dot_04.md`.

Các file đang thay đổi khác từ Đợt 1–3 được giữ nguyên, cần quyết định commit
cùng hay tách do người dùng. Snapshot/script chuẩn bị một lần trong `.venv/`
bị ignore; không thuộc mã sản phẩm hoặc artifact cần commit.
