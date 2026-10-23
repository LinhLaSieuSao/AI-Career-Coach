# AI Career Coach

Cộng đồng hỗ trợ người học và người đi làm định hướng nghề nghiệp. Ứng dụng giúp bạn tổng hợp kỹ năng, sở thích và kinh nghiệm; đối chiếu hồ sơ với vị trí quan tâm; tìm kỹ năng cần phát triển, khóa học phù hợp và câu hỏi luyện phỏng vấn.

## Chạy trên máy cá nhân

Ứng dụng dùng Streamlit, nên lệnh `streamlit run app.py` tự khởi động máy chủ local và phục vụ trang tại `http://localhost:8501`. Không cần cài máy chủ web riêng hay tệp chạy `.bat`.

Yêu cầu Python 3.11 trở lên (khuyến nghị Python 3.12). Tải mã nguồn từ GitHub bằng **Code → Download ZIP** rồi giải nén, hoặc clone repository; sau đó mở terminal tại thư mục `AI-Career-Coach`.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Nếu PowerShell chặn kích hoạt môi trường, chạy Python trong `.venv` trực tiếp:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### macOS hoặc Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Các lệnh tạo `.venv` chỉ cần chạy lần đầu. Những lần sau, mở terminal tại thư mục dự án, kích hoạt `.venv` (PowerShell: `\.venv\Scripts\Activate.ps1`; macOS/Linux: `source .venv/bin/activate`) rồi chạy `python -m streamlit run app.py`. Nếu `requirements.txt` thay đổi, cài lại thư viện bằng lệnh `python -m pip install -r requirements.txt`.

Để dừng ứng dụng, nhấn `Ctrl + C` trong terminal. Lần cài thư viện đầu tiên cần kết nối Internet.

## Tính năng

- Tạo hồ sơ từ kỹ năng, sở thích và kinh nghiệm.
- Chọn một vị trí nghề nghiệp để xem yêu cầu kỹ năng và phần còn thiếu.
- Nhận gợi ý khóa học và câu hỏi phỏng vấn theo vị trí.
- Đối chiếu nội dung CV PDF với mô tả công việc.

## Cấu trúc thư mục

```text
AI-Career-Coach/
├── app.py
├── requirements.txt
├── .streamlit/         # Giao diện sáng theo màu thương hiệu
├── brand_assets/       # Logo và tài liệu nhận diện thương hiệu
├── Data/               # Vị trí nghề nghiệp, khóa học, câu hỏi phỏng vấn
└── modules/            # Xử lý hồ sơ, kỹ năng, CV và gợi ý nghề nghiệp
```
