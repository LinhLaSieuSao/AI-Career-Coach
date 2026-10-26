# Cổng chất lượng bốn nghề demo — Bước 1

Ngày đối chiếu: **26-10-2026**. Nguồn máy đọc được: [`demo-role-quality-2026-10-26.json`](demo-role-quality-2026-10-26.json). Cổng này kiểm dữ liệu đang ghi trong repo; không mở mạng, không tự xác nhận chuyên gia, quyền sử dụng hay năng lực người dùng. Kết quả **fail có chủ đích** là backlog nội dung cần giảm dần qua các bước tiếp theo.

## Baseline theo nghề

| Role | Yêu cầu skill | Câu hiện có | Thiếu câu đúng skill/Level | Template/chưa review | Câu chung chung | Thiếu context/rubric đích | Lượt resource | Thiếu scope/locator | Chờ kiểm tra link độc lập | Record rejected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `sales_executive` | 8 | 5 | 3 | 3 | 2 | 5/5 | 15 | 15 | 15 | 2 |
| `frontend_developer_react` | 11 | 7 | 4 | 0 | 5 | 7/7 | 22 | 21 | 22 | 1 |
| `data_analyst` | 10 | 6 | 4 | 0 | 2 | 6/6 | 19 | 19 | 19 | 2 |
| `backend_developer_java` | 10 | 7 | 3 | 0 | 3 | 7/7 | 20 | 20 | 20 | 1 |
| **Tổng lượt theo role** | **39** | **25** | **14** | **3** | **12** | **25/25** | **76** | **75** | **76** | **6** |

Resource có **53 ID duy nhất** trên bốn role, vì một resource có thể phục vụ nhiều role. Hai URL homepage nằm ở `frontend_developer_react`. Không có câu sai Level hoặc thiếu red flags về mặt cấu trúc, không có mapping rejected nào lọt qua policy gợi ý hiện tại. `content_reviewed_at` đang hiện diện ở các resource demo; ngày đó **không** phải ngày kiểm tra link độc lập.

Ngoài các lỗi trên, **8/39 yêu cầu skill chưa có mapping đủ điều kiện ở Level đích**: sales 4, frontend 0, data analyst 2, backend Java 2. Cổng kiểm cả sự hiện diện này để không thể đạt PASS bằng cách bỏ hết resource đang lỗi. Lộ trình thực hành kỹ năng mềm vẫn là đường học hợp lệ; nó cần rubric và bằng chứng riêng trước khi được coi là đóng khoảng trống Level.

## Ý nghĩa từng cổng

- **Câu hỏi:** đối chiếu skill/Level của `roles.json` với câu cùng role trong `Data/interview_question/`. Prompt có placeholder rõ, “hãy kể theo STAR” hoặc “hãy mô tả cách bạn dùng” bị đưa vào hàng biên tập. `evaluation_rubric.level_<Level>_criteria` phải có nội dung; cổng đồng thời ghi tình trạng cả ba mức rubric. `context_scenario` phải ghi bối cảnh rõ. Chỉ ghi `reviewed` khi có review thật; câu AI chưa được rà giữ `unreviewed` và provenance/note minh bạch.
- **Học liệu:** yêu cầu có mapping đủ điều kiện ở Level đích, kiểm `scope_granularity` ở cấp lesson/module/chapter/spec cùng `evidence_locator`, URL root homepage, `content_reviewed_at` và trục kiểm tra truy cập độc lập. Scope/locator có mặt mới là điều kiện hình thức, **chưa xác nhận nội dung dạy đúng Level**. 165 URL do chủ dự án báo đã mở thủ công là một trục riêng, không đổi thành `independently_accessible` per record.
- **Rejected:** sáu lượt mapping `unsuitable` vẫn là hàng đợi xử lý record. Kiểm tra hành vi riêng đã **PASS**: policy không đề xuất các mapping này. Schema hiện chưa có cơ chế archive, nên gate không tự giả định một trường `archived` để bỏ qua record. Bước xử lý học liệu cần xác định cơ chế lưu record cũ và mapping thay thế; không xóa record hoặc đổi nhãn thành reviewed để giảm số.

## Lệnh nghiệm thu

```powershell
$py = 'D:\Linh\.venvs\ai-career-coach-py312\Scripts\python.exe'
& $py scripts/audit_demo_role_quality.py --as-of 2026-10-26 --json-output docs/verification/demo-role-quality-2026-10-26.json
& $py -m pytest tests/test_demo_role_quality.py --no-cov -q
& $py -m pytest tests/test_demo_role_quality.py --runxfail --no-cov -q
& $py scripts/audit_demo_role_quality.py --as-of 2026-10-26 --strict
```

Kết quả tại baseline: báo cáo `gate_passed=false`; test thường **1 passed, 4 xfailed** (backlog được nhìn thấy, không làm suite cấu trúc đỏ vì lỗi nội dung đã biết); `--runxfail` **4 failed, 1 passed**, exit 1; `--strict` phải exit 1. `xfail` chỉ bắt `AssertionError`, nên exception trong mã audit vẫn làm test thường đỏ. Khi từng role hết backlog, bỏ `xfail` của role đó để cổng CI trở thành bắt buộc; một XPASS với `strict=True` sẽ báo đỏ cho đến khi cập nhật gate.

Lượt nghiệm thu cuối đã xác nhận `--strict` exit 1 và `--runxfail` trả **4 failed, 1 passed**. Chạy chung file mới với `test_evidence_schema.py` và `test_data_integrity.py` đạt **32 passed, 4 xfailed**; `git diff --check` qua. Các số liệu dữ liệu trước/sau Bước 1 giữ nguyên (14 cặp thiếu câu, 3 template, 25 câu thiếu rubric đích, 8 cặp thiếu học liệu Level đích), vì bước này xây cổng kiểm tra và báo cáo, chưa biên tập nội dung.

Mỗi bước sửa tiếp theo cần chạy lại báo cáo JSON và so sánh `issue_occurrences_by_role`, đồng thời đọc danh sách ID cụ thể trong `roles[role_id].issues`. Không suy mức tiến bộ bằng cách làm mất record hoặc chuyển trạng thái giả.
