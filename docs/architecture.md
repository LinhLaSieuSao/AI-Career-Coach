# Kiến trúc

```mermaid
flowchart LR
    UI[Streamlit UI] --> PARSE[PDF/DOCX parser]
    PARSE --> EXT[Rule-based skill extractor]
    FORM[Manual skills, interests, levels] --> PROF[Profile normalization and alias catalog]
    EXT --> PROF
    PROF --> PRES[Presence matcher]
    PROF --> GAP[Explicit level gap]
    ROLES[Data/roles.json] --> PRES
    ROLES --> GAP
    ROLES --> SUG[Explainable role ranking]
    RES[Data/resources.json] --> WEEK[Weekly recommender]
    RES --> TIME[Timed planner with evidence]
    PRES --> WEEK
    GAP --> TIME
    PRES --> UI
    GAP --> UI
    SUG --> UI
    WEEK --> UI
    TIME --> UI
    QUESTIONS[Interview question banks] --> INTERVIEW[Focus selection]
    RUBRIC[Reviewed rubric subset] --> SCORE[Keyword rubric scoring]
    INTERVIEW --> UI
    SCORE --> UI
    UI --> EXPORT[Markdown / CSV export]
```

## Thành phần

- **Parser:** `modules/cv_parser.py` đọc PDF/DOCX cục bộ, giữ lỗi có mã rõ ràng. OCR chưa được cung cấp.
- **Extractor/Profile:** `modules/skill_extractor.py` nhận diện cụm từ trong catalog hữu hạn; `modules/profile.py` giữ kỹ năng chưa nhận diện và level khai báo riêng.
- **Matcher:** presence score dùng trọng số kỹ năng role; `compute_gap` dùng level 0–3 đã khai báo và đánh dấu thiếu level là `current=0` chỉ sau khi người dùng xác nhận ở UI.
- **Gợi ý role:** `suggest_roles` tính điểm heuristic theo skill/interests, hoàn toàn local; không dự đoán xác suất tuyển dụng.
- **Recommender:** `build_roadmap` giữ API tuần cũ. `build_timed_roadmap` dùng metadata review, level range và duration có provenance; dữ liệu thiếu làm tổng tuần `null`.
- **Interview:** câu hỏi được ưu tiên theo gap. `score_answer` chỉ chấm rubric được review; phần còn lại trả unavailable. Phép chấm từ khóa không hiểu ngữ nghĩa đầy đủ.
- **Export:** `modules/export.py` tạo Markdown hoặc CSV, escape dữ liệu người dùng có thể trở thành công thức bảng tính, không xuất toàn văn CV.

Ứng dụng không thực hiện inference bằng mô hình AI trong bản này. Tên sản phẩm giữ “AI Career Coach”, còn mọi tính năng hiện có được mô tả theo thuật toán thực sự đang chạy.
