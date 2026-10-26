# Hợp đồng bổ sung Đợt 4

Đây là phần mở rộng của `interface.md`, không thay thế API presence/roadmap cũ.
Chốt schema trước khi nối UI. Tất cả API chỉ đọc catalog local, không gọi mạng.

## compute_gap(levels:dict[str,int], role:dict) -> dict

Level là khai báo tường minh: 0 chưa có, 1 cơ bản cần hướng dẫn, 2 làm việc độc
lập ở tác vụ quen thuộc, 3 xử lý/phân tích tác vụ phức tạp. Đây là tự đánh giá,
không là chứng chỉ. Profile giữ khóa thiếu là unknown; **chỉ API này** quy mọi
skill role không có trong levels thành current=0. UI phải giải thích và yêu
cầu xác nhận trước khi gọi, không lấy tên trong CV làm level.

```python
{"role_id": "r", "items": [
 {"skill": "sql", "required": 3, "current": 1, "gap": 2,
  "priority": 6, "status": "below_required"}],
 "match_percent": 33.3, "missing": ["sql"]}
```

`gap=max(0,required-current)`, `priority=weight*gap`. Status `met` khi gap=0,
`missing` khi gap>0 và current=0, `below_required` khi 0<current<required.
Percent = 100 × tổng(weight × min(current/required,1)) / tổng(weight), chỉ tính
required>0, làm tròn 1 chữ số và giới hạn 0–100. Required=0 là không yêu cầu,
không vào mẫu số. Role rỗng trả percent=0, items/missing rỗng. Thứ tự items và
missing giữ thứ tự yêu cầu role; missing bao gồm skill đã có nhưng level thấp.
Required/current phải là int 0–3, weight dương hữu hạn (mặc định 1 như Matcher
khi thiếu trường weight); required không có
không được suy ngầm. Tên/alias trùng sau canonical gây lỗi. Không mutate input.
`match_role.percent` tiếp tục là phần trọng số **presence**, không đổi semantics.

## Đối chiếu JD theo nhóm đã xác nhận

`extract_jd_skill_requirements(jd_text) -> dict` trả `all_skills`,
`must_have`, `nice_to_have`, `unclassified`. Bộ trích xuất chỉ gán nhóm khi
nhận ra tiêu đề rõ ràng như “Yêu cầu bắt buộc / Requirements”, “Ưu tiên / Nice
to have” hoặc “Trách nhiệm / Responsibilities” (tiêu đề đứng riêng, ở đầu
dòng, hoặc sau dấu câu/phân tách danh sách). Kỹ năng trong phần văn bản
không có tiêu đề tương ứng nằm ở `unclassified`; ứng dụng không suy mức độ bắt
buộc chỉ từ việc một kỹ năng xuất hiện trong câu.

Người dùng có thể bỏ kỹ năng không đúng hoặc chuyển kỹ năng giữa ba nhóm ở bước
rà soát. Mỗi kỹ năng canonical chỉ được nằm trong một nhóm. Alias được giải về
tên canonical trước khi kiểm tra trùng.

`compare_confirmed_jd_requirements(candidate, must_have, nice_to_have,
unclassified=(), *, must_weight=.85, nice_weight=.15) -> dict` trả từng nhóm
với `skills`, `matched`, `missing`, `count`, `percent`. Tỷ lệ từng nhóm là số
kỹ năng trùng hồ sơ chia cho số kỹ năng trong nhóm đó. `overall_percent` và
`percent` chỉ có khi có ít nhất một kỹ năng bắt buộc; khi có cả hai nhóm bắt
buộc và ưu tiên, tổng hợp = (85% × tỷ lệ bắt buộc + 15% × tỷ lệ ưu tiên) / tổng
trọng số được cấu hình. Khi không có nhóm ưu tiên, tỷ lệ bắt buộc được dùng
riêng. Nhóm chưa phân loại luôn có tỷ lệ riêng và không tham gia tổng hợp.

Các tỷ lệ chỉ là heuristic trùng khớp tên kỹ năng trong vocabulary đã được
người dùng xác nhận. Chúng không xác minh mức độ thành thạo, đầy đủ các yêu cầu
ngoài catalog, đủ điều kiện ứng tuyển hay xác suất tuyển dụng. Nếu không có kỹ
năng bắt buộc, không tạo điểm tổng hợp; UI phải nói rõ điều đó. API cũ
`compare_confirmed_skills_to_jd` và `match_cv_to_jd` tiếp tục được giữ cho các
caller cần schema phẳng.

## build_timed_roadmap(gap, resources, hours_per_week=8) -> dict

```python
{"role_id": "r", "hours_per_week": 8,
 "resources": {"url:https://example.org/course": {
   "key": "url:https://example.org/course", "skills": ["sql"],
   "planned_hours": 10, "duration_kind": "published"}},
 "resource_keys": {"sql": ["url:https://example.org/course"]},
 "level_coverage": [{"skill": "sql", "resource_key": "url:https://example.org/course",
                     "levels": [2,3], "content_review_status": "reviewed", "review_note": "..."}],
 "phases": [{"week": 1, "hours": 8, "segments": [
   {"resource_key": "url:https://example.org/course", "hours": 8, "part": 1,
    "duration_kind": "published"}]},
  {"week": 2, "hours": 2, "segments": [
   {"resource_key": "url:https://example.org/course", "hours": 2, "part": 2,
    "duration_kind": "published"}]}],
 "total_weeks": 2, "known_weeks": 2,
 "total_known_hours": 10, "total_estimated_hours": 0, "total_planned_hours": 10,
 "is_estimated": False, "unknown_duration": [], "unresolved": [],
 "completion_basis": "resource_metadata_not_skill_attainment"}
```

Chỉ xử lý item gap>0, sắp priority giảm dần ổn định khi bằng nhau. Chọn tài liệu
cho từng mức current+1..required: `level_from <= mức <= level_to`, verified=true
và trạng thái nội dung reviewed/partial. Không tin cờ verified legacy khi chưa
review. Trong các lựa chọn tại một mức: ưu tiên reviewed, giờ công bố rồi ước
lượng có căn cứ rồi giờ unknown, tiếp theo bao phủ nhiều mức cần học hơn; bằng
nhau giữ thứ tự catalog. Không tự chọn tất cả phương án thay thế.

Giữ metadata từng mapping khi xét level/độ phù hợp, union danh tính theo ID hoặc
URL chuẩn hóa như roadmap cũ. Một danh tính được phân bổ đúng một lần cho toàn
lộ trình; `resource_keys` giữ mọi skill liên quan. Mapping thiếu giờ không ghi
đè giờ có nguồn của cùng danh tính; giờ công bố được ưu tiên hơn ước lượng.
Nếu các mapping được chọn có số giờ cùng loại mâu thuẫn, giữ unknown thay vì
chọn số tùy tiện. `duration_evidence` giữ source/basis/hours/kind của căn cứ
được dùng; `planned_hours` có thể biết dù mapping đầu tiên thiếu duration_hours.
Dùng toàn bộ
giờ tài nguyên đã chọn, không chia giờ theo tỷ lệ level hoặc số skill.

Giờ công bố chỉ dùng khi dương hữu hạn và có duration_source HTTP(S) cùng
duration_basis. `estimated_duration_hours` dùng riêng khi có
estimated_duration_basis hoặc duration_basis; duration_kind=estimated, cộng
riêng, UI phải nêu cơ sở. Giờ không có provenance là unknown. Giá trị giờ sai
kiểu/âm/NaN/inf, budget không dương/bool, level range sai, gap mâu thuẫn và tên
trùng gây lỗi rõ; không sửa dữ liệu để lập lịch được.

Mỗi phase là một tuần có tổng giờ không vượt budget; resource dài chia segment
tham chiếu cùng key. `known_weeks` là số tuần của phần có thể phân bổ (kể cả
ước lượng có nhãn), không phải thời gian toàn bộ lộ trình. `total_known_hours`
chỉ cộng giờ công bố; `total_estimated_hours` riêng; tổng hai phần là
total_planned_hours. Nếu có bất kỳ unresolved, total_weeks=null. Nếu đầy đủ
nhưng dùng ước lượng, total_weeks vẫn là số dự kiến với is_estimated=true.
Không gap trả 0 tuần/giờ và danh sách rỗng.

`unknown_duration` liệt kê resource_key, skills, reason.
`unresolved` có reason và skill hoặc skills/resource_key/levels phù hợp:
no_resources, unreviewed_content, blocked_resource, unsuitable_content,
missing_url, missing_resource_identity, unverified_link, level_mismatch,
partial_content, unknown_duration, unverified_duration, estimate_without_basis,
conflicting_duration. Partial vẫn có thể xếp phần đọc được nhưng không coi
skill đã được bao phủ đầy đủ. Có link/range không chứng minh đạt năng lực;
completion_basis luôn nhắc đây chỉ là kế hoạch theo metadata tài nguyên.
Planner không suy stack, điều kiện tiên quyết hay năng lực người học từ văn
xuôi. UI hiển thị review_note/access_note của tài liệu đã chọn; ví dụ REST C#
chỉ là nguồn tham khảo khác stack đối với Java, không chứng minh thực hành Java.

## suggest_roles(profile, top_k=5) -> list[dict]

S = percent presence theo trọng số của match_role / 100. I = số interest duy
nhất khớp / số interest duy nhất khai báo. Interest chuẩn hóa/giải alias và
khớp cả cụm theo ranh giới từ trong tên Anh/Việt hoặc canonical skill của role;
không substring kiểu `ai` trong từ khác. Không mở rộng đồng nghĩa suy đoán.

Cả skills và interests có tín hiệu khai báo: score=100*(0.8*S+0.2*I). Chỉ có
skills: 100*S. Chỉ interests: 100*I. Mỗi thành phần nằm 0–1 trước khi cộng.
Không tín hiệu hoặc mọi role có score=0 trả []; bỏ role score=0, có thể ít hơn
top_k. top_k là int không âm, 0 trả [], bool/âm gây ValueError. Điểm làm tròn
1 chữ số; tie theo role_id tăng dần. Không dựa trên levels hay tự đánh giá level.

Mỗi kết quả có role_id, role_name, score, skill_percent, interest_percent,
matched, missing, matched_interests, reasons:list[str], method='heuristic'.
Điểm là mức xếp hạng quy tắc, không là xác suất tuyển dụng. Dữ liệu catalog
không có sở thích cá nhân chuẩn hóa sâu; tên/sở thích ngoài phạm vi khớp có thể
không tạo tín hiệu. UI không tự chọn role đầu danh sách.

UI dùng wizard hai bước: nhập hồ sơ, sau đó xác nhận/bỏ kỹ năng và chọn Level
0–3 bằng selectbox cho từng kỹ năng. Không yêu cầu nhập JSON. Giá trị thiếu
Level vẫn là unknown; Level 3 không được gợi ý tự động. Thay hồ sơ đã xác nhận
reset mode/kết quả/phỏng vấn cũ; lỗi ở bản nháp không ghi đè hồ sơ đã lưu.
Điều kiện tạo hồ sơ là có kỹ năng hoặc CV hợp lệ; chỉ có interests/experience
không tạo hồ sơ. API suggest_roles riêng vẫn nhận được interests-only.

## Luyện phỏng vấn và hướng dẫn câu trả lời

`get_questions(role_id, n, seed=None, focus_skills=None)` trả bản sao công khai,
xen kẽ câu kỹ thuật/tình huống, không lặp ID và ưu tiên gap trước. `n` phải là
số nguyên dương; UI giới hạn tối đa ở `min(10, số câu hợp lệ hiện có của role)`
để không yêu cầu vượt số dữ liệu ngân hàng thực sự có. Focus rỗng tương đương
không ưu tiên. Không có câu phù hợp thì UI thông báo, không tự tạo câu.

Public whitelist gồm id/type/skill/level/weight/question/time_minutes/quality
và role_id. Đáp án, gợi ý, lưu ý cần tránh và nguồn review chỉ được truy xuất
sau khi người dùng gửi câu trả lời trong UI. Phiên chỉ giữ câu trả lời đã gửi
trong session hiện tại; không lưu vào file hoặc dịch vụ ngoài.

Ứng dụng **không tính điểm tự động**, không khớp cụm từ và không xếp hạng câu
trả lời. Checklist là danh sách tự phản tư, không cộng thành điểm. Câu hỏi có
`quality=reviewed` phải có ngày, ghi chú và URL nguồn trong chính record; trạng
thái này chỉ nói đã review nội bộ, không phải thẩm định độc lập. Mọi record
không đạt điều kiện đó được xem là chưa review. UI gắn cảnh báo, yêu cầu kiểm
chứng nội dung chuyên môn và gọi câu trả lời tình huống là cách triển khai tham
khảo, không phải đáp án duy nhất.

`get_question_feedback(question_id)` trả nội dung tham khảo, loại câu hỏi,
trạng thái review và nguồn tương ứng (nếu có). ID không tồn tại hoặc trùng gây
`ValueError`. Nội dung chưa review không được gắn nhãn đáp án đã kiểm chứng.
Người dùng tự rà soát bối cảnh, lý do, bằng chứng, kết quả và điều đã học; app
không suy diễn ý nghĩa hay xác nhận tính đúng thay cho người phỏng vấn.

Trong bộ dữ liệu hiện tại có 752 câu: 6 record đã review nội bộ, 12 record có
nhãn template, còn 734 record chưa có trạng thái review. Sáu record review đã
giữ ngày, ghi chú và nguồn ngay trong câu hỏi; rubric cụm từ chấm máy đã được
loại bỏ vì không thể đánh giá ngữ nghĩa hoặc chứng cứ trải nghiệm đáng tin cậy.
