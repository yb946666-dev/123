"""提醒信息和邮件发送模块。

邮件功能使用 SMTP 环境变量配置，不在代码中保存邮箱密码。
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable


REQUIRED_EMAIL_ENV = ["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "EMAIL_TO"]


def build_notification(job: dict) -> str:
    """Build a human-readable reminder for one matched job."""

    company = job.get("company") or job.get("单位") or "待确认单位"
    title = job.get("title") or job.get("岗位") or "待确认岗位"
    deadline = job.get("deadline") or job.get("报名时间") or "待确认"
    score = job.get("match_score") or job.get("匹配评分") or "待评分"
    priority = job.get("priority") or job.get("投递优先级") or "待排序"
    link = job.get("url") or job.get("报名链接") or "待确认"
    reason = job.get("recommend_reason") or job.get("推荐理由") or "需要人工复核公告。"

    return (
        f"【国企校招提醒】{company} - {title}\n"
        f"优先级：{priority}\n"
        f"匹配评分：{score}\n"
        f"报名时间：{deadline}\n"
        f"推荐理由：{reason}\n"
        f"报名链接：{link}\n"
        "注意：最终投递前请人工确认岗位、个人信息、简历版本和提交按钮。"
    )


def build_batch_notifications(jobs: list[dict], min_score: int = 60) -> list[str]:
    """Generate reminders for jobs whose score is high enough."""

    notices = []
    for job in jobs:
        try:
            score = int(job.get("match_score", 0))
        except (TypeError, ValueError):
            score = 0
        if score >= min_score:
            notices.append(build_notification(job))
    return notices


def build_email_body(jobs: list[dict], new_jobs: list[dict] | None = None) -> str:
    """Build the daily digest email body."""

    new_jobs = new_jobs if new_jobs is not None else jobs
    lines = [
        "2027届国企校招每日监控汇总",
        "",
        f"本次发现候选岗位/公告：{len(jobs)} 条",
        f"其中新岗位/公告：{len(new_jobs)} 条",
        "",
    ]

    if not new_jobs:
        lines.append("今天暂未发现新的高匹配岗位。")
    else:
        for index, job in enumerate(new_jobs, start=1):
            company = job.get("company", "待确认单位")
            title = job.get("title", "待确认岗位")
            score = job.get("match_score", "待评分")
            priority = job.get("priority", "待排序")
            url = job.get("url", "待确认")
            reason = job.get("recommend_reason", "需要人工复核公告。")
            lines.extend([
                f"{index}. {company} - {title}",
                f"   匹配评分：{score}",
                f"   投递优先级：{priority}",
                f"   推荐理由：{reason}",
                f"   链接：{url}",
                "",
            ])

    lines.extend([
        "安全提醒：本项目不会自动投递，不会绕过验证码，不会点击最终提交。",
        "请人工确认公告原文、岗位要求、简历版本和报名信息后再投递。",
    ])
    return "\n".join(lines)


def validate_email_env() -> list[str]:
    """Return missing SMTP environment variable names."""

    return [name for name in REQUIRED_EMAIL_ENV if not os.getenv(name)]


def mask_email(value: str) -> str:
    """Mask an email address for logs while keeping enough detail for diagnosis."""

    value = value.strip()
    if "@" not in value:
        return "格式异常：缺少 @"
    local, domain = value.rsplit("@", 1)
    if not local or not domain:
        return "格式异常：邮箱不完整"
    visible = local[:2] if len(local) >= 2 else local[:1]
    return f"{visible}***@{domain}"


def send_email(subject: str, body: str, attachments: Iterable[str | Path] | None = None) -> dict:
    """Send an email through SMTP.

    Required env vars: SMTP_HOST, SMTP_USER, SMTP_PASSWORD, EMAIL_TO.
    Optional env vars: SMTP_PORT, SMTP_USE_SSL, EMAIL_FROM.
    Returns a dict of recipients refused by the SMTP server.
    """

    missing = validate_email_env()
    if missing:
        raise RuntimeError("缺少邮件环境变量：" + ", ".join(missing))

    smtp_host = os.environ["SMTP_HOST"].strip()
    smtp_port = int(os.getenv("SMTP_PORT") or "465")
    smtp_user = os.environ["SMTP_USER"].strip()
    smtp_password = os.environ["SMTP_PASSWORD"]
    email_from = (os.getenv("EMAIL_FROM") or smtp_user).strip()
    email_to = os.environ["EMAIL_TO"].strip()
    use_ssl = os.getenv("SMTP_USE_SSL", "true").lower() not in {"0", "false", "no"}

    print(f"邮件诊断：SMTP_HOST 已配置，端口 {smtp_port}，SSL={use_ssl}")
    print(f"邮件诊断：发件人 {mask_email(email_from)}，收件人 {mask_email(email_to)}")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = email_from
    message["To"] = email_to
    message.set_content(body)

    for attachment in attachments or []:
        path = Path(attachment)
        if not path.exists() or not path.is_file():
            continue
        message.add_attachment(
            path.read_bytes(),
            maintype="application",
            subtype="octet-stream",
            filename=path.name,
        )

    if use_ssl:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            return server.send_message(message)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        return server.send_message(message)
