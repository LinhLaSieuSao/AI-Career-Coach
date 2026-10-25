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
no_resources, unreviewed_content (gồm blocked/unsuitable), level_mismatch,
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

UI nhập levels bằng object JSON trong form, từ chối khóa trùng kể cả cùng
chính tả trước khi parser ghi đè. Level lỗi giữ nguyên hồ sơ đã chấp nhận trước;
thay hồ sơ hợp lệ reset consent/mode và câu trả lời. Đổi mode/role/gap reset
phiên phỏng vấn để không dùng đáp án/điểm của bộ câu hỏi cũ. Form vẫn giữ điều
kiện hợp lệ Đợt 2: kỹ năng có nội dung hoặc CV hợp lệ, không lưu hồ sơ chỉ có
interests; API suggest_roles riêng vẫn nhận được interests-only.

## get_questions(..., focus_skills=None) và score_answer(question_id, answer)

None giữ thuật toán cũ: shuffle theo seed, xen kẽ technical/scenario, không
lặp ID. Focus chuẩn hóa/alias: đưa câu có skill trong focus lên trước, giữ thứ
tự seed/xen kẽ trong từng nhóm, sau đó bù câu role còn lại tới n. Danh sách
focus rỗng tương đương không ưu tiên. Không có câu cho một gap không bịa câu.
Public whitelist chỉ id/type/skill/level/weight/question/time_minutes/quality
và role_id; không reference_answer/good_answer_points/red_flags/rubric/review_note.

Rubric private ở `Data/interview_rubrics.json`: từng question_id có review_status,
reviewed_at, review_note, sources và criteria[{id,label,points,groups}]. Mỗi
group là OR các cụm tương đương; criterion đòi **mọi group** (AND), tổng points
bằng 10. Không tạo rubric tự động từ câu trả lời mẫu. Câu hỏi và rubric phải
cùng được reviewed; thiếu/không hợp lệ trả:

```python
{"score": None, "criteria": [], "feedback": ["..."], "method": "rubric",
 "status": "unavailable", "reason": "missing_or_unreviewed_rubric"}
```

Rubric dùng được trả status=scored, score 0–10, criteria có id/label/met/score/
max_score và feedback nêu ý đạt/thiếu. Answer trống ở API này có score=0 khi
rubric có sẵn; không có rubric vẫn None. UI yêu cầu trả lời trước khi submit.
ID không tồn tại/trùng gây ValueError, answer không phải str gây TypeError.
Chuẩn hóa riêng phần chấm: NFC/lowercase, bỏ dấu tiếng Việt, so cụm theo ranh
giới từ, không fuzzy; phủ định gần cụm có thể ngăn nhận điểm. Quy tắc không
hiểu ngữ nghĩa sâu, không xác minh sự thật hay tính nhất quán lập luận, có thể
bỏ sót cách diễn đạt mới hoặc cho điểm câu liệt kê khái niệm. Luôn nêu giới hạn.

Đã review nội bộ 6 cặp question/rubric thuộc ba role demo (2/role), sửa câu hỏi
thành tình huống cụ thể. 12 câu demo còn lại quality=template và unavailable.
Không giả tên reviewer hoặc thẩm định độc lập. Câu khác trong bank chưa được
gắn reviewed. UI chỉ gọi feedback/reference/scoring sau submit; các API đọc
feedback cũ dành cho caller tin cậy, không là cơ chế xác thực người dùng.
