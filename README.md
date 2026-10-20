# AI-Career-Coach
Phát triển hệ thống phân tích kỹ năng, kiến thức, sở thích và kinh nghiệm của sinh viên, đối chiếu với yêu cầu tuyển dụng để xác định khoảng cách năng lực. Từ đó, hệ thống đề xuất lộ trình học tập, tài liệu cần ôn tập và bộ câu hỏi phỏng vấn phù hợp với từng vị trí công việc
## Cấu Trúc Thư Mục

ai-career-coach/
├── app.py                         # [C] Frontend: giao diện Streamlit và điều phối
├── modules/
│   ├── __init__.py                # [B]
│   ├── skill_extractor.py         # [A] Trích xuất và chuẩn hóa kỹ năng
│   ├── profile.py                 # [A] Xử lý kiến thức, sở thích, kinh nghiệm
│   ├── matcher.py                 # [A] Tính điểm phù hợp và kỹ năng thiếu
│   ├── recommender.py             # [A] Đề xuất lộ trình và tài liệu
│   └── interview.py               # [A] Câu hỏi phỏng vấn và chấm câu trả lời
├── data/
│   ├── roles.json                 # [A] Vị trí và kỹ năng yêu cầu
│   ├── resources.json             # [A] Tài liệu học theo kỹ năng
│   └── interview_questions.json   # [A] Bộ câu hỏi phỏng vấn
├── tests/
│   ├── test_matcher.py            # [A] Unit test cho matcher
│   ├── test_recommender.py        # [A] Unit test cho recommender
│   └── test_skill_extractor.py    # [A] Unit test cho skill_extractor
├── docs/
│   ├── architecture.md            # [B] Kiến trúc, nêu rõ phần AI
│   ├── interface.md               # [B] Hợp đồng hàm giữa các module
│   └── demo.md                    # [C] Kịch bản demo chi tiết
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   └── bug_report.md          # [B] Template báo lỗi
│   └── workflows/
│       └── ci.yml                 # [B] Luồng kiểm thử tự động CI
├── Dockerfile                     # [B] Cấu hình Docker container
├── docker-compose.yml             # [B] Điều phối dịch vụ Docker
├── .dockerignore                  # [B] Danh sách bỏ qua khi build Docker
├── .gitignore                     # [B] Danh sách bỏ qua khi commit Git
├── .env.example                   # [B] Mẫu tệp biến môi trường
├── requirements.txt               # [B] Các thư viện phụ thuộc
├── README.md                      # [B] Tổng hợp, [C] Bổ sung phần demo
├── LICENSE                        # [B] Giấy phép phần mềm
├── LICENSES.md                    # [B] Chi tiết các giấy phép phụ thuộc
├── CONTRIBUTING.md                # [B] Hướng dẫn đóng góp mã nguồn
└── CHANGELOG.md                   # [B] Nhật ký thay đổi hệ thống

## Nhánh Git theo từng thành viên
feature/ai-core        # A: thư mục modules/ (trừ __init__.py), data/, tests/ phần AI
feature/backend-infra  # B: Docker, CI, tài liệu kỹ thuật, các file cấu hình gốc
feature/frontend-demo  # C: app.py, docs/demo.md, phần giao diện trong README
