# guoqi-job-hunter

2027 届国企校招自动监控与半自动投递助手，面向通信工程学生，先实现招聘公告监控、岗位筛选、Excel 导出和邮件提醒，后续再扩展半自动投递。

## 用户背景

* 学校：四川轻化工大学
* 专业：通信工程
* 年级：大三
* 证书：CET4、计算机二级
* 经历：供电所实习经历
* 目标：国家电网、南方电网、三大运营商、央国企技术岗

## 项目目标

帮助用户持续关注 2027 届国企校招信息，自动整理招聘公告，筛选通信工程相关岗位，生成投递优先级、Excel 清单和每日邮件提醒。

本项目遵守投递安全边界：不绕过验证码，不自动提交最终申请，最终投递前必须由用户人工确认。

## 功能

* 招聘公告监控：读取企业配置，抓取公开招聘入口页面并识别疑似校招公告。
* 岗位匹配评分：根据通信工程、网络运维、信息化、电力通信、云网、技术支持等关键词评分。
* 国企投递优先级排序：结合目标单位、岗位相关度、学历要求、地区和实习经历进行排序。
* Excel 导出：将岗位清单导出为 `.xlsx`，便于筛选、记录和投递跟进。
* 邮件提醒：每天北京时间 8 点汇总新岗位，并发送到指定邮箱。
* 简历优化建议：提示应突出供电所实习、通信网络课程、Office/计算机二级和 CET4。
* 面试准备建议：提示准备电力通信、计算机网络、运营商网络、实习复盘和国企价值观表达。

## 项目结构

```text
guoqi-job-hunter/
├── README.md
├── SKILL.md
├── config/
│   └── companies.yaml
├── docs/
│   └── 投递流程.md
└── src/
    ├── daily_digest.py
    ├── export_excel.py
    ├── matcher.py
    ├── monitor.py
    └── notify.py
```

## 本地运行

安装可选依赖：

```bash
pip install pyyaml openpyxl
```

运行监控：

```bash
cd guoqi-job-hunter
python src/monitor.py
```

运行每日汇总和邮件发送：

```bash
cd guoqi-job-hunter
SMTP_HOST=smtp.example.com \
SMTP_PORT=465 \
SMTP_USER=your_email@example.com \
SMTP_PASSWORD=your_smtp_password \
EMAIL_TO=your_email@example.com \
python src/daily_digest.py
```

Windows PowerShell 示例：

```powershell
cd guoqi-job-hunter
$env:SMTP_HOST="smtp.example.com"
$env:SMTP_PORT="465"
$env:SMTP_USER="your_email@example.com"
$env:SMTP_PASSWORD="your_smtp_password"
$env:EMAIL_TO="your_email@example.com"
python src/daily_digest.py
```

## GitHub Actions 每天 8 点自动提醒

仓库已配置 `.github/workflows/guoqi-job-hunter.yml`：

* 每天 00:00 UTC 运行，即北京时间 08:00。
* 也可以在 GitHub Actions 页面手动点击 `Run workflow`。
* 每次运行会生成 `output/jobs.json` 和 `output/jobs.xlsx` 或 `output/jobs.csv`。
* 邮件会汇总新岗位，并附带岗位清单文件。

需要在 GitHub 仓库中配置 Secrets：

| Secret | 说明 |
|---|---|
| `SMTP_HOST` | SMTP 服务器，例如 `smtp.gmail.com`、`smtp.qq.com` |
| `SMTP_PORT` | SMTP 端口，常用 `465` |
| `SMTP_USER` | 发件邮箱账号 |
| `SMTP_PASSWORD` | 邮箱 SMTP 授权码或应用专用密码 |
| `EMAIL_TO` | 收件邮箱 |
| `EMAIL_FROM` | 可选，发件人地址，默认等于 `SMTP_USER` |
| `SMTP_USE_SSL` | 可选，默认 `true` |

## 输出文件

* `jobs.json`：`monitor.py` 本地运行时生成的候选公告结果。
* `output/jobs.json`：`daily_digest.py` 生成的推荐岗位结果。
* `output/jobs.xlsx`：安装 `openpyxl` 时生成的 Excel 清单。
* `output/jobs.csv`：未安装 `openpyxl` 时的 CSV 兜底文件。
* `data/seen_jobs.json`：记录已提醒过的岗位，用于识别新岗位。

## 安全原则

* 不绕过验证码。
* 不保存招聘网站登录密码。
* 不自动提交最终申请。
* 不替用户确认志愿、岗位或个人信息。
* 最终投递前必须人工检查公告、岗位、简历和报名信息。
