# Checklist Proof of Feasibility

Checklist này chỉ mô tả các cổng có thể kiểm tra từ repo. Chất lượng tư vấn nghề, nội dung học liệu và quyền phân phối cần người có trách nhiệm xác nhận riêng.

| Cổng | Cách kiểm tra | Trạng thái cần đạt |
| --- | --- | --- |
| Cài đặt Python 3.12 | `pip install --require-hashes -r requirements.lock` | Cài sạch không lỗi |
| Unit và giao diện | `python -m pytest -q tests/` | Không có test lỗi |
| Dữ liệu | `tests/test_data_integrity.py` | 131 role, 15 nhóm, 10 phần câu hỏi và alias hợp lệ |
| Docker | `docker compose up --build`, `/_stcore/health` | Container healthy |
| Secret trong image | CI quét tên tệp trong từng layer | Không có `.env`, `.pem`, `.key`, token |
| Link học liệu | `python scripts/check_links.py --output dist/links.json` | Báo cáo URL được rà lại trước release; truy cập được không đồng nghĩa phù hợp |
| License và provenance | [`LICENSES.md`](../LICENSES.md) | Maintainer xác nhận các mục còn mở trước phân phối dữ liệu |

Kết quả kiểm thử local trong một lần chạy không thay thế CI trên đúng commit phát hành, kiểm tra giao diện thực trên nhiều thiết bị hoặc review chuyên môn độc lập.
