"""提醒信息生成模块。"""

from __future__ import annotations


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
