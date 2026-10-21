# Sử dụng image Python 3.13 chính thức, bản siêu nhẹ
FROM python:3.13-slim

# Đặt thư mục làm việc bên trong container
WORKDIR /app

# Copy tệp yêu cầu môi trường vào trước
COPY requirements.txt .

# Cài đặt các thư viện (bổ sung python-docx nếu requirements chưa có)
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir python-docx

# Copy toàn bộ mã nguồn vào container
COPY . .

# Mở cổng 8501 cho giao diện Streamlit
EXPOSE 8501

# Lệnh khởi động ứng dụng
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]