"""岗位匹配评分模块。

根据通信工程学生背景，对招聘公告或岗位文本进行初步评分。
这是规则型 v1，不编造公告信息，也不替代人工判断。
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass
class MatchResult:
    score: int
    recommended: str
    priority: str
    reasons: list[str]
    resume_tips: list[str]
    interview_tips: list[str]


PROFILE_KEYWORDS = {
    "major": ["通信工程", "通信", "信息通信", "电子信息", "计算机网络", "网络工程", "电力通信"],
    "skills": ["网络", "运维", "TCP/IP", "IPv4", "IPv6", "VLAN", "云网", "网络安全", "信息化", "弱电"],
    "experience": ["供电所", "电网", "变电站", "通信运维", "故障处理", "应急保电", "数据统计"],
    "certificates": ["CET4", "英语四级", "计算机二级", "WPS", "Office"],
}

NEGATIVE_KEYWORDS = ["博士", "硕士研究生", "仅限硕士", "法学", "会计", "临床医学", "土木工程"]
HIGH_VALUE_UNITS = ["国家电网", "南方电网", "中国移动", "中国电信", "中国联通", "中国铁塔", "中国电科"]


def _contains_any(text: str, keywords: Iterable[str]) -> list[str]:
    return [keyword for keyword in keywords if keyword.lower() in text.lower()]


def match_job(job: dict) -> MatchResult:
    """Return a rule-based match result for one job dict.

    Expected keys: company, title, location, major_requirement, education_requirement, description.
    Missing keys are treated as empty strings.
    """

    text = " ".join(str(job.get(key, "")) for key in [
        "company", "group", "title", "location", "major_requirement", "education_requirement", "description"
    ])

    score = 40
    reasons: list[str] = []

    major_hits = _contains_any(text, PROFILE_KEYWORDS["major"])
    if major_hits:
        score += 22
        reasons.append(f"专业方向匹配：{', '.join(major_hits[:4])}")

    skill_hits = _contains_any(text, PROFILE_KEYWORDS["skills"])
    if skill_hits:
        score += 16
        reasons.append(f"技能关键词匹配：{', '.join(skill_hits[:5])}")

    experience_hits = _contains_any(text, PROFILE_KEYWORDS["experience"])
    if experience_hits:
        score += 12
        reasons.append("供电所/电网/运维经历可迁移")

    cert_hits = _contains_any(text, PROFILE_KEYWORDS["certificates"])
    if cert_hits:
        score += 5
        reasons.append("CET4 或计算机二级等证书有帮助")

    if _contains_any(text, HIGH_VALUE_UNITS):
        score += 8
        reasons.append("属于重点目标央国企或高度相关单位")

    negative_hits = _contains_any(text, NEGATIVE_KEYWORDS)
    if negative_hits:
        score -= 25
        reasons.append(f"存在限制或弱相关关键词：{', '.join(negative_hits[:3])}")

    if "本科" in text or "本科及以上" in text:
        score += 8
        reasons.append("学历要求对本科较友好")

    score = max(0, min(100, score))

    if score >= 80:
        recommended = "推荐"
        priority = "高"
    elif score >= 60:
        recommended = "谨慎推荐"
        priority = "中"
    else:
        recommended = "不推荐"
        priority = "低"

    resume_tips = [
        "突出供电所实习中的通信、运维、故障处理、数据整理或现场协作经历。",
        "突出通信原理、计算机网络、信号与系统、微波技术与天线等课程。",
        "写清 CET4、计算机二级和 Office/WPS 文档处理能力。",
    ]
    interview_tips = [
        "准备 TCP/IP、VLAN、传输网、5G/云网、电力通信基础问题。",
        "用 STAR 法复盘供电所实习经历，强调责任心、执行力和现场沟通。",
        "提前了解单位主营业务、子公司定位和岗位工作场景。",
    ]

    if not reasons:
        reasons.append("公告信息较少，需要人工确认岗位职责和专业要求")

    return MatchResult(score, recommended, priority, reasons, resume_tips, interview_tips)


def enrich_job(job: dict) -> dict:
    """Attach matching fields to one job dict."""

    result = match_job(job)
    enriched = dict(job)
    enriched.update({
        "match_score": result.score,
        "recommended": result.recommended,
        "priority": result.priority,
        "recommend_reason": "；".join(result.reasons),
        "resume_tips": "；".join(result.resume_tips),
        "interview_tips": "；".join(result.interview_tips),
    })
    return enriched


def to_dict(result: MatchResult) -> dict:
    return asdict(result)
