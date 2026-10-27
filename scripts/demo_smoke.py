"""Run project tests and start the local website for manual testing.

Usage: python scripts/demo_smoke.py [--test-only | --web-only] [--no-browser]
"""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser


ROOT = Path(__file__).resolve().parents[1]


def choose_port(start: int) -> int:
    for port in range(start, min(start + 30, 65536)):
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"Không tìm thấy cổng trống từ {start} đến {min(start + 29, 65535)}.")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Kiểm thử dự án và mở website trên máy cá nhân.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--test-only", action="store_true", help="Chỉ chạy bộ kiểm thử.")
    modes.add_argument("--web-only", action="store_true", help="Chỉ mở website để kiểm tra thủ công.")
    parser.add_argument("--no-browser", action="store_true", help="Không tự mở trình duyệt.")
    parser.add_argument("--port", type=int, default=8501, help="Cổng bắt đầu tìm (mặc định: 8501).")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Cổng phải nằm trong khoảng 1–65535.")

    needed = (["pytest"] if not args.web_only else []) + (["streamlit"] if not args.test_only else [])
    missing = [name for name in needed if importlib.util.find_spec(name) is None]
    if missing:
        print("Thiếu thư viện: " + ", ".join(missing))
        print("Hãy cài môi trường Python 3.12 theo README, sau đó cài requirements.lock.")
        return 2

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    test_status = 0
    if not args.web_only:
        print("Đang chạy bộ kiểm thử. Kết quả có thể mất một lúc…", flush=True)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=short", "tests/"],
            cwd=ROOT, env=env, check=False,
        )
        test_status = result.returncode
        if test_status:
            print(f"\nKiểm thử chưa đạt (mã {test_status}); xem chi tiết phía trên.", flush=True)
        else:
            print("\nBộ kiểm thử đã hoàn tất thành công.", flush=True)
        if args.test_only:
            return test_status

    try:
        port = choose_port(args.port)
    except RuntimeError as exc:
        print(exc)
        return 2
    url = f"http://127.0.0.1:{port}"
    print(f"\nĐang khởi động website tại {url}", flush=True)
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(port),
         "--server.address", "127.0.0.1", "--server.headless", "true"],
        cwd=ROOT, env=env,
    )
    try:
        ready = False
        for _ in range(100):
            if process.poll() is not None:
                print("Website dừng trước khi khởi động xong; xem lỗi phía trên.")
                return process.returncode or 1
            try:
                with urllib.request.urlopen(url + "/_stcore/health", timeout=1) as response:
                    ready = response.status == 200
            except (OSError, urllib.error.URLError):
                pass
            if ready:
                break
            time.sleep(0.2)
        if not ready:
            print("Không xác nhận được website đã sẵn sàng. Kiểm tra lỗi phía trên.")
            return 1
        print(f"Website đã sẵn sàng: {url}")
        if test_status:
            print("Lưu ý: có kiểm thử thất bại; vẫn mở web để bạn kiểm tra thủ công.")
        if not args.no_browser and not webbrowser.open(url):
            print("Không mở được trình duyệt tự động; hãy mở địa chỉ trên.")
        print("Giữ cửa sổ này mở khi dùng web; nhấn Ctrl+C để dừng.", flush=True)
        process.wait()
        return process.returncode or test_status
    except KeyboardInterrupt:
        print("\nĐang dừng website…")
        return test_status
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
