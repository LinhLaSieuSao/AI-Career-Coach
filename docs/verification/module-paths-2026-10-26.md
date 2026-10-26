# Kiểm tra đường đi dữ liệu qua module

Ngày: 2026-10-26; dataset `01dba94c2991f18af28a6163e019e0ef54a734dc4c4fff6b55b7c19d731a9bae`.

131/131 role qua các API lõi; 0 role có lỗi. Hồ sơ đầu vào là hai kỹ năng đầu của mỗi role với Level 1 tổng hợp.

Kiểm tra gồm presence match, level gap, lộ trình presence, lộ trình theo giờ, lấy 3 câu phỏng vấn và hướng dẫn sau gửi. PASS chỉ nói các module đọc và nối dữ liệu không exception/sai role; không chứng minh độ phù hợp nghề, nội dung đúng hoặc giao diện trình duyệt.

| API | Số lượt đạt |
| --- | ---: |
| answer_guidance | 393 |
| interview_selection | 131 |
| level_gap | 131 |
| presence_match | 131 |
| presence_roadmap | 131 |
| timed_roadmap | 131 |

## Lỗi theo role

Không có lỗi trong phạm vi kiểm tra này.

```powershell
python scripts/audit_module_paths.py --as-of 2026-10-26
```
