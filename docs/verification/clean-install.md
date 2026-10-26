# Cài sạch và bằng chứng tái lập

Hướng dẫn này ghi lại môi trường được dùng để kiểm chứng repo local. Chỉ những kết quả có lệnh và output phía dưới mới được coi là đã xác minh; nó không thay cho CI trên máy khác.

## Windows PowerShell

Tạo môi trường mới trong thư mục repo rồi cài bản khóa có hash:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pytest --basetemp=D:\Linh\.pytesttmp-clean-install
.\.venv\Scripts\python.exe scripts\smoke.py
.\.venv\Scripts\python.exe tests\test_recommendation_quality.py
.\.venv\Scripts\python.exe scripts\validate_question_bank.py
```

## Linux/macOS

```bash
python3.12 -m venv .venv
.venv/bin/python --version
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --require-hashes -r requirements-dev.lock
.venv/bin/python -m pytest
.venv/bin/python scripts/smoke.py
.venv/bin/python tests/test_recommendation_quality.py
.venv/bin/python scripts/validate_question_bank.py
```

## Hồ sơ kiểm chứng của lượt này

- Mục tiêu runtime: CPython 3.12.x; venv kiểm thử riêng được tạo bằng CPython 3.12.15.
- Dependency resolver: `uv pip compile` với `--python-version 3.12 --generate-hashes`; runtime được lưu tại [`requirements.lock`](../../requirements.lock), test/dev tại [`requirements-dev.lock`](../../requirements-dev.lock).
- Install: venv sạch ban đầu không có `pip`/package dự án; `uv pip install --require-hashes -r requirements-dev.lock` đã cài 50 packages. Đây là cài lock từ mạng, không phải cài offline.
- Full suite: `python -m pytest --basetemp=D:\Linh\.pytesttmp-clean-install --cov=app --cov=modules --cov-report=term-missing` — **429 passed / 429**, 156.59 giây, Python 3.12.15 / Windows; tổng coverage **91%**. Không còn test fail.
- Smoke: PASS; `data_analyst`, một phase lộ trình, 3 câu hỏi, **0.864 giây** (<2 giây).
- Golden benchmark: 23 hồ sơ tổng hợp; **Hit@3 100.0%, MRR 0.949, Forbidden@3 0.0%**. Các chỉ số chỉ phản ánh bộ fixture này.
- Question-bank validator: **752 câu / 131 role, 0 lỗi toàn vẹn**; validator không thẩm định chuyên môn.
- Ma trận học liệu: **416 kỹ năng × 3 level = 1,248 dòng**; 89 dòng reviewed, 408 partial, 751 chưa có nguồn đủ điều kiện.
- App local: Streamlit khởi động trên `127.0.0.1:8501`; console chỉ ghi URL và `Uvicorn server started`, không ghi warning/exception. `/_stcore/health` trả **HTTP 200 / `ok`**. Browser thấy trang tiếng Việt, form, role demo, kết quả, sơ đồ lộ trình, tài liệu, câu hỏi và luồng hướng dẫn tự rà soát.
- Browser keyboard smoke: Tab lần lượt qua ba liên kết đầu, Enter mở `#career-toolkit`, Space kích hoạt nút hồ sơ mẫu; đã gửi câu trả lời giả lập. DOM xác nhận `lang="vi"`, nhãn các trường có tên truy cập và notice nói rõ checklist là nội dung tĩnh, không phân tích hay chấm câu trả lời. Đây chưa phải audit WCAG/screen-reader đầy đủ.
- Footprint: mã nguồn + dữ liệu được đo **18.6 MB / 417 file** (loại `.git`, venv, test cache). Trong venv kiểm chứng, toàn `site-packages` là **311.0 MB / 8,690 file**; riêng thư mục `pyarrow`, `pandas`, `streamlit`, `pydeck`, `numpy`, `numpy.libs`, `PIL` chiếm **240.0 MB**. Vì vậy mục tiêu cài đặt phụ thuộc dưới 150 MB **chưa đạt** dù không có torch, sentence-transformers hay spaCy; không được mô tả bản cài là <150 MB.
- Python 3.13 nằm trong ma trận CI, nhưng chưa chạy trong lượt local này. CI/GitHub Actions và Docker build cần xem kết quả workflow riêng.

## Cập nhật khóa phụ thuộc

Sau khi thay đổi dependency trực tiếp, chạy lại resolver cho đúng phiên bản Python mục tiêu:

```powershell
uv pip compile requirements.txt --python-version 3.12 --generate-hashes --output-file requirements.lock
uv pip compile requirements-dev.txt --python-version 3.12 --generate-hashes --output-file requirements-dev.lock
```

Chỉ ghi nhận cài sạch thành công khi lệnh cài hash trên venv mới và toàn bộ lệnh test kết thúc thành công; resolver thành công riêng lẻ không phải bằng chứng app đã chạy.

## Kiểm tra trực tiếp ZIP ứng viên ngày 26-10-2026

Gói `dist/ai-career-coach-0.4.0-candidate.zip` được giải nén vào `dist/cleancheck/source/ai-career-coach-0.4.0-candidate`. Một venv Python 3.12.15 riêng, ban đầu chưa có dependency dự án, được tạo ở `dist/cleancheck/venv`. Lệnh `python -m pip install --require-hashes -r requirements.lock` chạy **thành công** từ tệp lock trong ZIP, tải gói từ PyPI; đây không phải thử cài offline. Sandbox chặn thư mục temp mặc định nên `TEMP`/`TMP` được trỏ vào thư mục tạm trong workspace. Launcher `py.exe` của WindowsApps không truy cập được trong sandbox; việc tạo venv dùng executable CPython 3.12.15 đã cài trên máy.

Trong chính thư mục giải nén, venv mới chạy `scripts/smoke.py` **PASS**, `scripts/validate_question_bank.py` báo **752 câu/131 role, 0 lỗi cấu trúc**, và `scripts/audit_data_readiness.py` pass cổng nhất quán. Streamlit khởi động từ source giải nén trên `127.0.0.1:8505`, endpoint `/_stcore/health` trả **HTTP 200**; tiến trình thử này đã dừng sau kiểm tra. ZIP/tar.gz đều được đối chiếu byte với source và manifest tại thời điểm đóng gói, `SHA256SUMS` khớp. Vòng **466 core/AppTest + 5 Chromium browser** chạy trên workspace cùng mã ứng dụng trước khi bổ sung dòng tài liệu này, không chạy lại toàn bộ test trong venv runtime của ZIP vì test/browser dependencies không nằm trong `requirements.lock`.

Điều này xác nhận đường cài và khởi động sạch trên **Windows/Python 3.12.15 của máy hiện tại**. Linux/macOS, Docker local và GitHub Actions trên chính SHA phát hành vẫn cần bằng chứng riêng.

## Gói lại sau vòng review dữ liệu ngày 26-10-2026

Sau khi thu hẹp Level của chín học liệu và thêm cổng kiểm kê role×skill, source hiện tại đạt **470/470 core/AppTest** (166,66 giây), **5/5 Chromium browser** (49,91 giây), module sweep **131/131 role**. ZIP/tar.gz `0.4.0-candidate` được tạo lại từ 134 tệp nguồn cùng `MANIFEST.sha256`; so sánh từng byte với source và kiểm tra `SHA256SUMS` đều pass. Từ ZIP giải nén, venv runtime đã cài sạch ở lượt trước chạy validator **752 câu/131 role, 0 lỗi**, cổng inventory có fingerprint 165 URL pass, và smoke tuần tự pass. Trong lần kiểm tra gói trung gian, một lần smoke chạy đồng thời với inventory vượt ngưỡng thời gian 2 giây (2,096 giây); chạy riêng hoàn thành 0,873 giây. Đây là ngưỡng hiệu năng phụ thuộc tải máy, không phải lỗi kết nối dữ liệu.

Vòng này **không tạo venv mới hoặc cài lại dependency**, nên bằng chứng cài sạch thuộc gói trước đó với cùng bộ lock. Các số 429 test và 89/408/751 ô Level ở phần trên là snapshot trước vòng review dữ liệu, không phải kết quả nguồn hiện tại.
