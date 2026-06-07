"""每日监控汇总入口。

运行流程：监控公告 -> 识别新岗位 -> 导出 Excel/CSV -> 发送邮件汇总。
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from export_excel import export_jobs
from monitor import monitor
from notify import build_email_body, send_email, validate_email_env


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
SEEN_PATH = DATA_DIR / "seen_jobs.json"
JOBS_PATH = OUTPUT_DIR / "jobs.json"


def job_key(job: dict) -> str:
    """Build a stable key for de-duplicating jobs across daily runs."""

    raw = "|".join([
        str(job.get("company", "")),
        str(job.get("title", "")),
        str(job.get("url", "")),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_seen() -> set[str]:
    if not SEEN_PATH.exists():
        return set()
    try:
        data = json.loads(SEEN_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    return set(data.get("seen", []))


def save_seen(keys: set[str]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "seen": sorted(keys),
    }
    SEEN_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def filter_recommended(jobs: list[dict], min_score: int) -> list[dict]:
    filtered: list[dict] = []
    for job in jobs:
        try:
            score = int(job.get("match_score", 0))
        except (TypeError, ValueError):
            score = 0
        if score >= min_score:
            filtered.append(job)
    return filtered


def main() -> int:
    min_score = int(os.getenv("MIN_NOTIFY_SCORE", "60"))
    send_empty_digest = os.getenv("SEND_EMPTY_DIGEST", "true").lower() not in {"0", "false", "no"}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    jobs = monitor(PROJECT_ROOT / "config" / "companies.yaml")
    recommended_jobs = filter_recommended(jobs, min_score)

    seen = load_seen()
    current_keys = {job_key(job) for job in recommended_jobs}
    new_jobs = [job for job in recommended_jobs if job_key(job) not in seen]
    save_seen(seen | current_keys)

    JOBS_PATH.write_text(json.dumps(recommended_jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    export_path = export_jobs(recommended_jobs, str(OUTPUT_DIR / "jobs.xlsx"))

    if new_jobs or send_empty_digest:
        missing = validate_email_env()
        if missing:
            print("邮件未发送，缺少环境变量：" + ", ".join(missing))
            return 2
        today = datetime.now().strftime("%Y-%m-%d")
        subject = f"国企校招每日汇总 {today}：新岗位 {len(new_jobs)} 条"
        body = build_email_body(recommended_jobs, new_jobs)
        send_email(subject, body, attachments=[export_path])
        print(f"邮件已发送：新岗位 {len(new_jobs)} 条，附件 {export_path}")
    else:
        print("没有新岗位，且 SEND_EMPTY_DIGEST=false，跳过邮件发送。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
