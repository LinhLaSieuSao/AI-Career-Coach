"""Check unique resource URLs without changing any catalog verification flags."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time
from typing import Callable
from urllib.parse import urlsplit, urlunsplit

import requests


ROOT = Path(__file__).resolve().parents[1]
BLOCK_MARKERS = ("cf-chl-", "verify you are human", "just a moment...", "access denied", "captcha", "automated access")


@dataclass
class LinkResponse:
    status_code: int
    final_url: str
    redirects: int = 0
    sample: str = ""


def http_get(url: str, timeout: float) -> LinkResponse:
    """One GET per seed; finite connect/read timeouts, <=5 redirects, no retry.

    Requests timeouts are per connection/read, not a total wall-clock deadline.
    Only an 8 KiB HTML sample is read; PDFs and downloads are not consumed.
    """
    with requests.Session() as session:
        session.max_redirects = 5
        with session.get(url, timeout=(min(timeout, 5), timeout), allow_redirects=True,
                         stream=True, headers={"User-Agent": "AI-Career-Coach-LinkCheck/1.0"}) as response:
            content_type = response.headers.get("Content-Type", "").lower()
            sample = response.raw.read(8192, decode_content=True) if "html" in content_type else b""
            return LinkResponse(response.status_code, response.url, len(response.history), sample.decode("utf-8", errors="replace"))


def normalize_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must use HTTP(S) and include a hostname")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), parsed.query, ""))


def check_url(url: str, *, timeout: float = 10, transport: Callable = http_get) -> dict:
    start = time.monotonic()
    row = {"url": url, "checked_at": datetime.now(timezone.utc).isoformat(),
           "status_code": None, "final_url": None, "redirects": 0}
    try:
        normalized = normalize_url(url)
        response = transport(normalized, timeout)
        row.update(status_code=response.status_code, final_url=response.final_url, redirects=response.redirects)
        if response.status_code in {401, 403, 429, 451} or any(marker in response.sample.lower() for marker in BLOCK_MARKERS):
            status = "blocked"
        elif 200 <= response.status_code < 300:
            status = "redirect" if response.redirects else "reachable"
        elif 300 <= response.status_code < 400:
            status = "redirect"
        else:
            status = "error"
        row["status"] = status
    except (requests.Timeout, TimeoutError) as exc:
        row.update(status="timeout", detail=str(exc))
    except Exception as exc:  # network errors and injected transports are report data
        row.update(status="timeout" if "timed out" in str(exc).lower() else "error", detail=str(exc))
    row["verification"] = "transport_only" if row["status"] in {"reachable", "redirect"} and row["status_code"] and 200 <= row["status_code"] < 300 else "unverified"
    row["elapsed_seconds"] = round(time.monotonic() - start, 3)
    return row


def check_urls(urls, *, timeout: float = 10, workers: int = 4, transport: Callable = http_get) -> dict:
    if isinstance(workers, bool) or not isinstance(workers, int) or not 1 <= workers <= 8:
        raise ValueError("workers must be an integer from 1 to 8")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a positive finite number")
    unique = {}
    for url in urls:
        try:
            key = normalize_url(url)
        except ValueError:
            key = url
        unique.setdefault(key, url)
    seeds = sorted(unique.values())
    started = datetime.now(timezone.utc).isoformat()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(lambda url: check_url(url, timeout=timeout, transport=transport), seeds))
    return {"started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
            "timeout_seconds": timeout, "workers": workers,
            "note": "HTTP reachability is not content suitability. Blocked URLs remain unverified; this command does not edit resources.json.",
            "summary": dict(Counter(row["status"] for row in rows)), "unique_urls": len(rows), "results": rows}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources", type=Path, default=ROOT / "data/resources.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args(argv)
    output = args.output or ROOT / "dist" / f"links_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    if output.resolve() == args.resources.resolve():
        parser.error("report output must differ from the resource catalog")
    if isinstance(args.workers, bool) or not 1 <= args.workers <= 8 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("use workers 1..8 and a positive finite timeout")
    resources = json.loads(args.resources.read_text(encoding="utf-8"))
    report = check_urls([r["url"] for group in resources.values() for r in group["resources"]], timeout=args.timeout, workers=args.workers)
    report["source"] = str(args.resources.resolve())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(output), "unique_urls": report["unique_urls"], "summary": report["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
