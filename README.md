# AI Career Coach

AI Career Coach là ứng dụng Streamlit mã nguồn mở giúp tạo hồ sơ kỹ năng, đối chiếu với role trong catalog, xem khoảng cách kỹ năng, tìm tài liệu và luyện phỏng vấn. Các phép tính trong bản hiện tại dùng quy tắc tường minh; không gọi LLM, embedding hoặc dịch vụ trả phí.

Ứng dụng phân biệt điểm presence theo kỹ năng nhận diện, gap theo level do người dùng tự khai báo và điểm heuristic gợi ý role. Không điểm nào là xác suất tuyển dụng. PDF scan chưa được OCR; các rubric máy chấm mới chỉ có ở một nhóm nhỏ câu hỏi demo.

## Chạy local

Cần Python 3.12. Tạo môi trường ảo và cài runtime:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Trên macOS/Linux:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Mở địa chỉ local do Streamlit in ra, thường là `http://localhost:8501`. Dữ liệu được nạp từ thư mục `Data/` cạnh mã nguồn; app không gửi CV tới API bên ngoài. Xóa nội dung đã nhập khỏi trình duyệt khi dùng máy dùng chung.

## Chạy test

Cài bộ phát triển riêng (nó bao gồm runtime):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest --cov=app --cov=modules --cov-report=term-missing
```

`tests/` dùng fixture PDF/DOCX tổng hợp. Bài kiểm tra không cần truy cập link tài liệu; script kiểm tra liên kết là công cụ dev riêng.

## Docker

```bash
docker build -t ai-career-coach:local .
docker run --rm -p 8501:8501 ai-career-coach:local
```

Health endpoint: `http://localhost:8501/_stcore/health`. Image dùng Python 3.12, chạy bằng user không phải root và cài `requirements.txt` runtime.

## Demo

Màn hình “Dùng hồ sơ mẫu tổng hợp” có ba hồ sơ minh họa gắn với role thật trong catalog. Mỗi hồ sơ được đánh dấu synthetic; không mô tả người thật, kinh nghiệm thật hay kết quả tuyển dụng. Xem [docs/demo.md](docs/demo.md) để có kịch bản và lời dẫn.

## Tài liệu và dữ liệu

- [Hợp đồng API](docs/interface.md)
- [Sơ đồ kiến trúc](docs/architecture.md)
- [Chất lượng và giới hạn dữ liệu](docs/data_quality.md)
- [Kiểm kê giấy phép và provenance](LICENSES.md)
- [Checklist PoF local](docs/pof-checklist.md)

## Đóng góp

Xem [CONTRIBUTING.md](CONTRIBUTING.md). Hãy dùng fixture tổng hợp, giữ metadata nguồn và không đánh dấu resource/câu hỏi là reviewed nếu chưa có căn cứ.

## License và cộng đồng

Mã nguồn được phân phối theo [MIT License](LICENSE), giữ nguyên tên chủ bản quyền đang có trong tệp license. Trạng thái license của dữ liệu role, câu hỏi và tài liệu nguồn chưa được xác nhận đầy đủ; xem [LICENSES.md](LICENSES.md) trước khi phân phối lại bộ dữ liệu.

Repository hiện chưa xác minh Issues/Discussions hoặc kênh cộng đồng công khai, nên ứng dụng không trỏ tới một cộng đồng giả. Không có website, mailing list, tag hay release được tạo trong đợt local này.
