"""Offline transport tests; no real HTTP calls in pytest."""

from collections import Counter
import json
import threading
import time

import pytest
import requests

from scripts import check_links as links


@pytest.mark.parametrize("response,status,verification", [
    (links.LinkResponse(200, "https://example.org"), "reachable", "transport_only"),
    (links.LinkResponse(200, "https://new.example.org", 2), "redirect", "transport_only"),
    (links.LinkResponse(302, "https://example.org"), "redirect", "unverified"),
    (links.LinkResponse(404, "https://example.org"), "error", "unverified"),
    (links.LinkResponse(500, "https://example.org"), "error", "unverified"),
    (links.LinkResponse(403, "https://example.org"), "blocked", "unverified"),
    (links.LinkResponse(429, "https://example.org"), "blocked", "unverified"),
    (links.LinkResponse(200, "https://example.org", sample="Just a moment... Verify you are human"), "blocked", "unverified"),
])
def test_status_classification(response, status, verification):
    result = links.check_url("https://example.org", transport=lambda url, timeout: response)
    assert result["status"] == status
    assert result["verification"] == verification
    assert result["status_code"] == response.status_code
    assert result["final_url"] == response.final_url
    assert result["redirects"] == response.redirects


@pytest.mark.parametrize("error,status", [(requests.Timeout("wait"), "timeout"), (TimeoutError("wait"), "timeout"), (requests.ConnectionError("DNS"), "error")])
def test_transport_exceptions_are_reported(error, status):
    def transport(*args):
        raise error
    assert links.check_url("https://example.org", transport=transport)["status"] == status


def test_invalid_url_does_not_call_transport():
    def forbidden(*args):
        raise AssertionError("must not call transport")
    result = links.check_url("file:///local", transport=forbidden)
    assert result["status"] == "error"
    assert "HTTP" in result["detail"]


def test_unique_urls_checked_once_and_concurrency_is_bounded():
    calls, active, peak = [], 0, 0
    lock = threading.Lock()
    def transport(url, timeout):
        nonlocal active, peak
        with lock:
            calls.append(url)
            active += 1
            peak = max(peak, active)
        time.sleep(0.01)
        with lock:
            active -= 1
        assert timeout == 2
        return links.LinkResponse(200, url)
    urls = [f"https://example.org/{i}" for i in range(8)]
    report = links.check_urls([*urls, *urls, "https://EXAMPLE.org/0/#part"], workers=2, timeout=2, transport=transport)
    assert Counter(calls) == Counter(urls)
    assert report["unique_urls"] == 8
    assert 1 < peak <= 2
    assert report["summary"] == {"reachable": 8}


@pytest.mark.parametrize("kwargs", [{"workers": 0}, {"workers": 9}, {"workers": True}, {"timeout": 0}, {"timeout": float("inf")}, {"timeout": float("nan")}])
def test_invalid_limits_are_rejected(kwargs):
    with pytest.raises(ValueError):
        links.check_urls([], **kwargs)


def test_cli_report_never_modifies_source_flags(tmp_path, monkeypatch):
    path = tmp_path / "resources.json"
    content = json.dumps({"python": {"resources": [{"url": "https://example.org", "verified": False}]}})
    path.write_text(content, encoding="utf-8")
    output = tmp_path / "report.json"
    def offline(urls, **kwargs):
        return {"unique_urls": 1, "summary": {"reachable": 1}, "results": []}
    monkeypatch.setattr(links, "check_urls", offline)
    assert links.main(["--resources", str(path), "--output", str(output)]) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["summary"] == {"reachable": 1}
    assert path.read_text(encoding="utf-8") == content


def test_cli_cannot_overwrite_the_catalog_even_with_explicit_output(tmp_path):
    path = tmp_path / "resources.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        links.main(["--resources", str(path), "--output", str(path)])
    assert exc.value.code == 2
    assert path.read_text(encoding="utf-8") == "{}"


def test_redirect_loop_is_reported_without_retries():
    calls = []
    def transport(url, timeout):
        calls.append(url)
        raise requests.TooManyRedirects("Exceeded 5 redirects")
    report = links.check_urls(["https://example.org", "https://example.org/"], transport=transport)
    assert len(calls) == 1
    assert report["results"][0]["status"] == "error"
    assert report["results"][0]["verification"] == "unverified"
