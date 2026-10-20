# AI-Career-Coach
Phát triển hệ thống phân tích kỹ năng, kiến thức, sở thích và kinh nghiệm của sinh viên, đối chiếu với yêu cầu tuyển dụng để xác định khoảng cách năng lực. Từ đó, hệ thống đề xuất lộ trình học tập, tài liệu cần ôn tập và bộ câu hỏi phỏng vấn phù hợp với từng vị trí công việc
## Cấu Trúc Thư Mục
ai-career-coach/
├── app.py                        # [C] Frontend: giao diện Streamlit và điều phối
├── modules/
│   ├── __init__.py               # [B]
│   ├── skill_extractor.py        # [A] trích xuất và chuẩn hóa kỹ năng
│   ├── profile.py                # [A] xử lý kiến thức, sở thích, kinh nghiệm
│   ├── matcher.py                # [A] tính điểm phù hợp và kỹ năng thiếu
│   ├── recommender.py            # [A] đề xuất lộ trình và tài liệu
│   └── interview.py              # [A] câu hỏi phỏng vấn và chấm câu trả lời
├── data/
│   ├── roles.json                # [A] vị trí và kỹ năng yêu cầu
│   ├── resources.json            # [A] tài liệu học theo kỹ năng
│   └── interview_questions.json  # [A] bộ câu hỏi phỏng vấn
├── tests/
│   ├── test_matcher.py           # [A]
│   ├── test_recommender.py       # [A]
│   └── test_skill_extractor.py   # [A]
├── docs/
│   ├── architecture.md           # [B] kiến trúc, nêu rõ phần AI
│   ├── interface.md              # [B] hợp đồng hàm giữa các module
│   └── demo.md                   # [C] kịch bản demo
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   └── bug_report.md         # [B]
│   └── workflows/
│       └── ci.yml                # [B]
├── Dockerfile                    # [B]
├── docker-compose.yml            # [B]
├── .dockerignore                 # [B]
├── .gitignore                    # [B]
├── .env.example                  # [B]
├── requirements.txt              # [B]
├── README.md                     # [B] tổng hợp, C bổ sung phần demo
├── LICENSE                       # [B]
├── LICENSES.md                   # [B]
├── CONTRIBUTING.md               # [B]
└── CHANGELOG.md                  # [B]
## Nhánh Git theo từng thành viên
feature/ai-core        # A: thư mục modules/ (trừ __init__.py), data/, tests/ phần AI
feature/backend-infra  # B: Docker, CI, tài liệu kỹ thuật, các file cấu hình gốc
feature/frontend-demo  # C: app.py, docs/demo.md, phần giao diện trong README
