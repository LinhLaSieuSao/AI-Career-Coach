"""Run a safe, offline end-to-end demo through Streamlit's UI test harness.

Run from the repository root with: python scripts/demo_smoke.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]

SAMPLE_CV = """\
NGUYỄN MINH AN
Email: minh.an.demo@example.com
Hồ sơ giả lập phục vụ demo

MỤC TIÊU NGHỀ NGHIỆP
Ứng tuyển vị trí Data Analyst, tập trung phân tích dữ liệu và xây dựng báo cáo.

KỸ NĂNG
SQL, Python, Excel, Power BI, làm sạch dữ liệu, trực quan hóa dữ liệu,
phân tích chỉ số kinh doanh, giao tiếp và trình bày kết quả.

KINH NGHIỆM
Thực tập sinh phân tích dữ liệu | Công ty bán lẻ giả lập | 2025
- Dùng SQL tổng hợp dữ liệu đơn hàng và doanh thu theo tháng.
- Dùng Python và pandas xử lý dữ liệu thiếu, kiểm tra bản ghi trùng.
- Dùng Excel đối chiếu số liệu và lập bảng tổng hợp.
- Xây dashboard Power BI theo dõi doanh thu theo sản phẩm và khu vực.
- Trao đổi với nhóm kinh doanh để xác nhận định nghĩa chỉ số trước khi chia sẻ.

DỰ ÁN
Phân tích doanh số bán hàng | Dự án cá nhân
- Phân tích dữ liệu đơn hàng giả lập bằng SQL và Python.
- Trình bày xu hướng doanh thu bằng biểu đồ và dashboard Power BI.
- Ghi lại giả định và giới hạn của dữ liệu trong phần kết luận.

HỌC VẤN
Cử nhân Hệ thống thông tin | Trường Đại học giả lập | 2022–2026
"""

SAMPLE_JD = """\
Data Analyst

Yêu cầu bắt buộc:
SQL
Python
Excel
Power BI

Ưu tiên:
Tableau
Thống kê
Giao tiếp
"""

SAMPLE_ANSWER = (
    "Em kiểm tra kiểu dữ liệu và số dòng bị thiếu trước khi phân tích. "
    "Em dùng SQL tổng hợp theo kênh, tạo dashboard Power BI có bộ lọc, "
    "đối chiếu tổng với dữ liệu nguồn và ghi rõ cách xử lý dữ liệu thiếu. "
    "Trước khi chia sẻ, em xác nhận định nghĩa KPI với người phụ trách."
)


def _text_area(app: AppTest, key: str):
    return next(widget for widget in app.text_area if widget.key == key)


def _run_demo() -> tuple[AppTest, int]:
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    if app.exception:
        raise RuntimeError(f"App không khởi động được: {app.exception[0].message}")

    _text_area(app, "skills_input").input("SQL, Python, Excel, Power BI")
    _text_area(app, "pasted_cv_input").input(SAMPLE_CV)
    _text_area(app, "experience_input").input(
        "Thực tập phân tích dữ liệu bán lẻ; làm báo cáo và dashboard."
    )
    _text_area(app, "job_description_input").input(SAMPLE_JD)
    app.session_state["career_role_picker"] = "data_analyst"
    next(button for button in app.button if button.key == "profile_continue").click().run()
    if app.exception:
        raise RuntimeError(f"Bước nhập hồ sơ bị lỗi: {app.exception[0].message}")
    if app.session_state.get("profile_step") != 2:
        raise RuntimeError("App không chuyển sang bước rà soát kỹ năng.")

    for widget in app.selectbox:
        if not widget.label.startswith("Level · "):
            continue
        skill = widget.label.partition("·")[2].strip().casefold()
        level = {"sql": 2, "python": 2, "excel": 2, "power bi": 1}.get(skill)
        if level is not None:
            widget.select(level)

    next(button for button in app.button if button.label == "Xác nhận hồ sơ và xem kết quả").click().run()
    if app.exception:
        raise RuntimeError(f"Bước xác nhận hồ sơ bị lỗi: {app.exception[0].message}")

    profile = app.session_state.get("profile_result", {})
    expected_skills = {"sql", "python", "excel", "power bi"}
    if not expected_skills.issubset(set(profile.get("skills", []))):
        raise AssertionError(f"Kỹ năng trong CV chưa được nhận diện đủ: {profile.get('skills')}")
    if app.session_state.get("career_role_id") != "data_analyst":
        raise AssertionError("Vị trí Data Analyst chưa được lưu.")
    jd_result = app.session_state.get("cv_jd_result")
    if not jd_result or not jd_result.get("must_have"):
        raise AssertionError("Chưa tạo được kết quả đối chiếu JD.")
    if not any(item.value == "Lộ trình học" for item in app.subheader):
        raise AssertionError("Tab lộ trình chưa tạo nội dung.")

    app.button(key="start_interview_data_analyst").click().run()
    if app.exception:
        raise RuntimeError(f"Không tạo được câu hỏi phỏng vấn: {app.exception[0].message}")
    _text_area(app, next(widget.key for widget in app.text_area if widget.label == "Câu trả lời của bạn")).input(SAMPLE_ANSWER)
    next(button for button in app.button if button.label == "Gửi câu trả lời").click().run()
    if app.exception:
        raise RuntimeError(f"Không gửi được câu trả lời mẫu: {app.exception[0].message}")

    reviews = app.session_state["interview_session"].get("reviews", {})
    review = next(iter(reviews.values()), None)
    if not review or review.get("source") != "offline_rubric":
        raise AssertionError("Không nhận được kết quả chấm offline theo rubric.")
    return app, review["score"]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    network_attempts: list[str] = []

    def deny_network(url: str, *args, **kwargs):
        network_attempts.append(url)
        raise RuntimeError("Demo smoke test chặn mọi request ra ngoài.")

    with patch.dict(os.environ, {"LLM_API_KEY": "", "LLM_BASE_URL": "https://api.groq.com/openai/v1"}), patch(
        "requests.post", side_effect=deny_network
    ):
        app, score = _run_demo()

    if network_attempts:
        raise AssertionError(
            "Đã phát hiện cấu hình LLM cố gọi mạng; request đã bị chặn. "
            "Hãy bỏ key khỏi Streamlit secrets để chạy demo offline."
        )

    profile = app.session_state["profile_result"]
    jd_result = app.session_state["cv_jd_result"]
    print("PASS: Streamlit khởi động và hoàn tất luồng demo.")
    print(f"Vị trí: Data Analyst | Kỹ năng nhận diện: {', '.join(profile['skills'])}")
    print(
        "Đối chiếu JD: "
        f"{len(jd_result['must_have']['matched'])}/{len(jd_result['must_have']['matched']) + len(jd_result['must_have']['missing'])} "
        "kỹ năng bắt buộc khớp."
    )
    print(f"Phỏng vấn: rubric {score:.1f}/10, chấm offline; không gửi CV/câu trả lời ra mạng.")


if __name__ == "__main__":
    main()
