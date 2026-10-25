# Đợt 5 — Giao diện, export, demo và chuẩn bị phát hành local

Thực hiện **24/10/2026**, Windows, Python **3.12.14**, nhánh `AI-Specialist`,
HEAD `a430250`. Giữ nguyên thay đổi người dùng và code Đợt 1–4; không đổi nhánh,
stage, commit, push, tag hoặc publish. Không có `AGENTS.md` áp dụng. Đã đọc
README, interface/data quality, progress Đợt 1–4, báo cáo ma trận và code/dữ liệu.

## Nền trước khi sửa

Chạy lại toàn bộ suite từ `.venv`: **362 passed**, xác nhận nền Đợt 1–4 hoạt
động. Loader đọc 131 role; các regression Profile/Matcher/Recommender/Parser,
assessment, AppTest và integrity có trong suite. Integrity sau thay đổi vẫn
**0 lỗi, 5 warning** `recognition_only` cho `.net core`, `english`, `google tag
manager`, `mysql`, `pandas`; catalog 445 resource, 135 URL, 752 câu hỏi.

## Thay đổi Đợt 5

- Chuyển CSS sang `assets/style.css`, đọc từ `Path(__file__)`; bỏ tải Google
  Fonts. Uploader giữ nguyên instructions/button text, không ẩn chữ hay dùng
  `::after`. Điều chỉnh title/form liền khối, bỏ viền cha lồng form phỏng vấn,
  tăng khoảng top ở header tablet và ẩn thẻ nổi trên mobile nhỏ.
- Tổ chức kết quả thành năm tab: Tóm tắt, Khoảng cách, Lộ trình, Tài liệu,
  Phỏng vấn. Hiện completion notice; kết quả ghi rõ role đã lưu. Đổi hồ sơ/demo
  thay snapshot, reset comparison/CV/answer, role và revision cùng nhau. Presence,
  level gap và heuristic suggestions có nhãn/cách tính riêng. Biểu đồ thanh chỉ
  biểu diễn điểm thật từ core; landing không còn số điểm tĩnh.
- Thêm `modules/export.py::export_report(profile, gap, roadmap,
  format="markdown") -> str`. CSV dùng `csv.DictWriter`, Unicode và thứ tự cột
  ổn định; prefix chuỗi có thể thành công thức bằng `'`; giữ numeric fields.
  Markdown/CSV ghi gap, nguồn/giờ known/estimated/unknown, unresolved; không chép
  toàn văn CV. Resource key dùng chung chỉ xuất một lần ở weekly roadmap.
- Thêm 3 hồ sơ tổng hợp trong `Data/demo_profiles.json` cho role thật
  `backend_developer_java`, `data_analyst`, `sales_executive`. Nút nạp mẫu cập
  nhật widget, role, Profile, xóa JD/CV cũ và reset phiên cũ. UI có nhãn tổng
  hợp; không chứa tên/kinh nghiệm người thật hay kết quả tuyển dụng.
- Gỡ lời quảng bá kênh cộng đồng không có URL xác minh; không tạo Issues/
  Discussions. Các thẻ trên landing ghi rõ “Minh họa tổng hợp”.
- Tách `requirements.txt` runtime và `requirements-dev.txt`, bỏ scikit-learn,
  pandas/numpy trực tiếp, matplotlib, seaborn, plotly không dùng; requests chuyển
  sang dev vì link-check script. Pin versions đã cài thử Python 3.12.14.
- Giữ Docker Python 3.12, non-root và healthcheck; CI cài dev requirements,
  chạy pytest-cov trên Python 3.11/3.12, lưu XML coverage và build/chạy health
  Docker trên Ubuntu. CI được cấu hình, chưa có workflow GitHub thực tế.
- Thêm `.gitattributes` auto text, LF cho shell, CRLF cho Windows scripts và
  binary cho assets. Không chuẩn hóa hàng loạt file working tree; giữ ignore
  cache/venv/log/secrets. `.vscode/settings.json` trỏ tới `.venv` chung thay vì
  path Windows riêng.
- Bổ sung README, architecture Mermaid, demo, checklist PoF, CONTRIBUTING,
  CHANGELOG, LICENSES, release notes local, matrix P01–P27 và hợp đồng export.
  Giữ nguyên chủ bản quyền `LinhLaSieuSao` trong `LICENSE`; chưa kết luận quyền
  phân phối role/question/answer/brand khi thiếu provenance.

## Hợp đồng và giới hạn

- API Đợt 1–4 được giữ. `RESULT_TABS` là tuple giao diện cố định; mode level chỉ
  gọi `compute_gap` sau checkbox xác nhận. Không lấy điểm gợi ý làm xác suất.
- `export_report` nhận Presence result, Gap result hoặc `None`; roadmap là timed
  dict, weekly list hoặc list rỗng. Định dạng khác `markdown`/`csv` raise
  `ValueError`; profile không phải mapping raise `TypeError`.
- Nguồn publisher/basis được giữ trong export. Nếu `total_weeks` null thì báo
  “chưa xác định”; estimate tách riêng. CSV formula escaping giảm rủi ro khi mở
  bảng tính nhưng không thay thế xử lý an toàn mọi ứng dụng spreadsheet.
- Hồ sơ mẫu được dựng từ catalog, không phải candidate nghiên cứu. Không tạo
  slide deck/video/screenshot giả; `docs/demo.md` chứa outline và lời dẫn đọc.
- CSS/uploader chưa nghiệm thu trực quan: in-app browser chặn origin
  `http://127.0.0.1:8765` vì origin approval gate ghi “user declined permission”.
  Không dùng browser khác/raw CDP để vượt gate. Docker CLI cũng không cài; mục
  này được báo riêng, không xem là pass.
- Data quality vẫn có 5 warning thiếu tài liệu cho vocabulary nhận diện độc lập.
  334 mapping resources còn unreviewed, 432 record duration null theo tài liệu
  quality; không thêm giờ giả.

## Kiểm thử và môi trường

Tạo env riêng `.venv/dot05-clean` bằng Python 3.12.14 runtime đi kèm Codex; không
thay Python toàn máy. Cài sạch `requirements-dev.txt`. Direct pins:
Streamlit 1.66.0, pdfplumber 0.11.10, python-docx 1.2.0, pytest 9.1.1,
pytest-cov 6.2.1, coverage 7.17.0, requests 2.34.2. `pip check`:
**No broken requirements found**.

Lệnh full suite cuối cùng:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
$env:TEMP=(Resolve-Path '.venv\tmp').Path
$env:TMP=$env:TEMP
.\.venv\dot05-clean\Scripts\python.exe -X utf8 -m pytest -q -p no:cacheprovider `
  --basetemp=.venv\tmp\pytest-dot05-verified `
  --cov=app --cov=modules --cov-report=term-missing `
  --cov-report=xml:coverage.xml --tb=short
```

Kết quả: **369 passed in 47.34s**, không skip/xfail; statement coverage **96%**
(1768 statements, 74 missed), `app.py` 96%, `modules/export.py` 97%. Không đặt
ngưỡng pass tùy ý. AppTest kiểm tra startup/form validation/demo buttons/đổi
role/tab names/undo/interview/export; parser upload có fixture tổng hợp.

`audit_project()` trên data thật: 0 lỗi, 5 warning nêu trên, 131 role, 445
resource records, 752 câu hỏi. `git diff --check` không báo whitespace error.
`py -0p` chỉ thấy Python 3.10.6 hệ thống; Python 3.11 không có local.

Docker probe:

```powershell
docker version
```

Lỗi: `The term 'docker' is not recognized as a name of a cmdlet, function,
script file, or executable program.` Không chạy build hoặc healthcheck local.
`.github/workflows/ci.yml` đã có job để chạy khi push/PR sau này.

Server Streamlit khởi chạy trên cổng 8765 và in URL; browser origin gate chặn
việc mở trang trong phiên. Do đó không có screenshot desktop/mobile và chưa xác
nhận upload widget trực quan trước/sau file. AppTest pass không được coi là
thay thế xác nhận layout.

## Trạng thái P-ID

Ma trận đầy đủ P01–P27, bằng chứng và việc còn lại nằm ở
[`matrix_status.md`](../matrix_status.md). P13–P18/P20–P23/P25–P27 được hoàn
thiện một phần/local theo đó; P15/P19/P24 xử lý trong phạm vi code/test. P05/P06/
P09/P18 và UI visual vẫn còn nguồn hoặc nghiệm thu bên ngoài.

## File Đợt 5 cần review/commit

- `app.py`, `assets/style.css`, `modules/export.py`, `modules/__init__.py`.
- `Data/demo_profiles.json`.
- `tests/test_export.py`, `tests/test_app.py`, `tests/test_app_assessment.py`.
- `requirements.txt`, `requirements-dev.txt`, `.gitattributes`,
  `.vscode/settings.json`, `Dockerfile`, `.github/workflows/ci.yml`.
- `README.md`, `LICENSES.md`, `CONTRIBUTING.md`, `CHANGELOG.md`.
- `docs/interface.md`, `docs/data_quality.md`, `docs/architecture.md`,
  `docs/demo.md`, `docs/pof-checklist.md`, `docs/matrix_status.md`,
  `docs/progress/dot_05.md`, `docs/release-notes/dot_05.md`.

Các thay đổi chưa commit từ Đợt 1–4 vẫn nằm trong working tree và được giữ
nguyên; xem `git status --short` để chọn commit theo đợt hoặc gộp. Không commit
file `.venv`, `coverage.xml`, temp/cache hoặc screenshot vì không có screenshot
thật.

Commit message gợi ý sau khi người dùng review: `feat: complete local career coach demo and export`.

## Điều kiện trước bước phát hành

Maintainer xác nhận chủ thể copyright, provenance/license role và question
banks, brand ownership; cung cấp rubric PoF có thẩm quyền; chạy CI và Docker
healthcheck; kiểm tra uploader/mobile trên browser được phép; review release
notes/phiên bản; sau đó mới tự quyết định tag/publish. Không có bước nào trong số
đó được tự thực hiện trong Đợt 5.
