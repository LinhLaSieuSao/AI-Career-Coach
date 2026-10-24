Để bạn ấy nghiệm thu trên nhánh GitHub có các thay đổi của bạn, cần có những file sau:
- modules/skill_extractor.py
- tests/test_skill_extractor.py
- tests/conftest.py
- Data/roles.json
- Data/skill_aliases.json
- Data/resources.json — test dùng file này để đối chiếu skill với tài nguyên.
Ngoài ra, máy bạn ấy cần cài Python và pytest. Nếu muốn chạy chế độ fuzzy (fuzzy=True), cần cài thêm rapidfuzz; chế độ mặc định không bật fuzzy.
Cách test: clone repo hoặc checkout nhánh/PR của bạn, mở terminal tại thư mục gốc repo, cài pytest nếu thiếu (python -m pip install pytest), rồi chạy:
pytest tests/test_skill_extractor.py -v
Kết quả đạt là toàn bộ test trong file báo PASSED.
