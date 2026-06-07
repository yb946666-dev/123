"""招聘公告监控模块。

v1 只监控公开招聘入口页面，提取疑似校招公告链接，不登录、不处理验证码、不提交申请。
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

try:
    from matcher import enrich_job
except ImportError:  # pragma: no cover
    from .matcher import enrich_job


ANNOUNCEMENT_KEYWORDS = ["2027", "校招", "校园招聘", "应届", "毕业生", "招聘公告", "春招", "秋招"]
LINK_RE = re.compile(r'<a[^>]+href=["\'](?P<href>[^"\']+)["\'][^>]*>(?P<title>.*?)</a>', re.I | re.S)


def load_companies(path: str | Path) -> list[dict[str, Any]]:
    """Load companies.yaml with PyYAML when available, otherwise use a small fallback parser."""

    text = Path(path).read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError:
        return _parse_companies_fallback(text)

    data = yaml.safe_load(text) or {}
    return data.get("companies", [])


def _parse_companies_fallback(text: str) -> list[dict[str, Any]]:
    companies: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_keywords = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "companies:":
            continue
        if stripped.startswith("- name:"):
            if current:
                companies.append(current)
            current = {"name": stripped.split(":", 1)[1].strip(), "keywords": []}
            in_keywords = False
        elif current and ":" in stripped and not stripped.startswith("-"):
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key == "keywords":
                in_keywords = True
                current.setdefault("keywords", [])
            else:
                current[key] = value
                in_keywords = False
        elif current and in_keywords and stripped.startswith("-"):
            current.setdefault("keywords", []).append(stripped[1:].strip())

    if current:
        companies.append(current)
    return companies


def fetch_page(url: str, timeout: int = 12) -> str:
    request = Request(url, headers={"User-Agent": "guoqi-job-hunter/0.1"})
    with urlopen(request, timeout=timeout) as response:
        raw = response.read()
    for encoding in ["utf-8", "gb18030"]:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _clean_title(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _absolute_url(base: str, href: str) -> str:
    if href.startswith(("http://", "https://")):
        return href
    if href.startswith("/"):
        match = re.match(r"(https?://[^/]+)", base)
        return f"{match.group(1)}{href}" if match else href
    return base.rstrip("/") + "/" + href.lstrip("/")


def extract_announcements(company: dict[str, Any], page_text: str) -> list[dict[str, Any]]:
    base_url = company.get("career_url", "")
    company_keywords = company.get("keywords", []) or []
    candidates: list[dict[str, Any]] = []

    for match in LINK_RE.finditer(page_text):
        title = _clean_title(match.group("title"))
        href = match.group("href")
        combined = f"{title} {' '.join(company_keywords)}"
        if not title:
            continue
        if not any(keyword in combined for keyword in ANNOUNCEMENT_KEYWORDS + company_keywords):
            continue

        job = {
            "company": company.get("name", ""),
            "group": company.get("group", ""),
            "title": title,
            "location": "待确认",
            "deadline": "待确认",
            "major_requirement": "待确认",
            "education_requirement": "待确认",
            "description": title,
            "url": _absolute_url(base_url, href),
        }
        candidates.append(enrich_job(job))

    return candidates


def monitor(config_path: str = "config/companies.yaml") -> list[dict[str, Any]]:
    companies = load_companies(config_path)
    results: list[dict[str, Any]] = []

    for company in companies:
        url = company.get("career_url")
        if not url:
            continue
        try:
            page_text = fetch_page(url)
        except (URLError, TimeoutError, OSError) as exc:
            results.append({
                "company": company.get("name", ""),
                "group": company.get("group", ""),
                "title": "监控失败",
                "location": "待确认",
                "deadline": "待确认",
                "major_requirement": "待确认",
                "education_requirement": "待确认",
                "match_score": 0,
                "recommended": "不推荐",
                "priority": "低",
                "recommend_reason": f"招聘入口暂时无法访问：{exc}",
                "resume_tips": "待公告可访问后再分析",
                "interview_tips": "待公告可访问后再准备",
                "url": url,
            })
            continue
        results.extend(extract_announcements(company, page_text))

    return sorted(results, key=lambda item: int(item.get("match_score", 0)), reverse=True)


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    config_path = project_root / "config" / "companies.yaml"
    output_path = project_root / "jobs.json"
    jobs = monitor(config_path)
    output_path.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"监控完成，发现 {len(jobs)} 条候选公告：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
