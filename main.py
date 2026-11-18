import datetime
import html
import os
import re
import smtplib
import ssl
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

from google import genai
from google.genai import types


def build_prompt(today_str: str) -> str:
    return f"""今天是 {today_str}（北京时间）。请通过 Google 搜索获取当日及前一日最新的全球金融与财政信息（重点覆盖亚洲、欧洲和美国市场），使用简体中文整理并输出一份内容详实、数据具体的《全球金融与财政每日简报》。

简报必须包含以下四个核心板块：
1. **美、欧、亚太股市与板块动态**：列出美股三大指数（道琼斯、标普500、纳斯达克）、欧洲 STOXX 600、日韩（日经225、KOSPI）及 A 股/港股（上证、深证、创业板、科创50、恒生指数、恒生科技）等核心指数的最新点位、涨跌幅、成交特征及主要驱动因素。
2. **主要央行货币政策动态**：详细追踪美联储（Fed）、欧洲央行（ECB）、中国人民银行（PBOC）及日本央行（BOJ）的最新利率路径、前瞻指引与结构性货币工具。
3. **中、美、欧重点政策与债券市场深度追踪**：
   - **【中国政策】（需最为详尽）**：涵盖财政预算/专项债/结存限额/特别国债、货币利率机制改革、房地产（按揭贴息/收储等）与消费“两新”配套、科技创新产业扶持及资本市场开放政策；
   - **【美国政策】**：涵盖联邦财政赤字与债务上限、关税与贸易政策、AI芯片/科技出口管制等最新政策及其对全球供应链与美债收益率、投资级企业债的影响；
   - **【欧洲政策】**：涵盖欧元区财政赤字、国防/能源开支与法德等国主权信用利差动态。
4. **汇率与大宗商品走势**：涵盖美元指数（DXY）、欧元、人民币、日元汇率以及现货黄金、国际原油（WTI、布伦特）的最新价位区间与核心驱动。

写作要求：
- 所有数据与新闻必须基于最新检索到的真实信息，注明日期与具体数值，严禁编造数据。
- 对文中出现的所有重要专业金融与财政名词，用 `> **【名词解释】...**` 或行内注释的形式，通俗说明其定义及对市场/资产价格的实际影响。
- 直接输出完整的 Markdown 格式简报正文，不要输出多余的寒暄语。"""


def generate_briefing(today_str: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("环境变量 GEMINI_API_KEY 未设置。")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=build_prompt(today_str),
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.2,
        ),
    )
    if not response.text:
        raise RuntimeError("Gemini API 返回内容为空。")
    return response.text.strip()


def md_to_html(md_text: str) -> str:
    """将简报 Markdown 转换为适合邮件客户端阅读的简洁 HTML。"""
    lines = md_text.splitlines()
    html_parts = [
        "<html><body style=\"font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif; line-height: 1.65; color: #1f2937; max-width: 780px; margin: 0 auto; padding: 16px;\">"
    ]
    in_list = False

    def format_inline(text: str) -> str:
        escaped = html.escape(text)
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
        escaped = re.sub(
            r"`(.+?)`",
            r"<code style=\"background:#f3f4f6;padding:2px 5px;border-radius:4px;font-size:0.9em;\">\1</code>",
            escaped,
        )
        return escaped

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue

        if line == "---":
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append("<hr style=\"border:none;border-top:1px solid #e5e7eb;margin:18px 0;\">")
            continue

        if line.startswith("# "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(
                f"<h1 style=\"font-size:20px;color:#111827;border-bottom:2px solid #2563eb;padding-bottom:6px;margin-top:8px;\">{format_inline(line[2:])}</h1>"
            )
        elif line.startswith("## "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(
                f"<h2 style=\"font-size:17px;color:#1e40af;margin-top:20px;margin-bottom:8px;\">{format_inline(line[3:])}</h2>"
            )
        elif line.startswith("### "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(
                f"<h3 style=\"font-size:15px;color:#374151;margin-top:14px;margin-bottom:6px;\">{format_inline(line[4:])}</h3>"
            )
        elif line.startswith("> "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(
                f"<blockquote style=\"border-left:4px solid #3b82f6;background:#eff6ff;padding:8px 12px;margin:8px 0;color:#1e3a8a;border-radius:0 6px 6px 0;font-size:14px;\">{format_inline(line[2:])}</blockquote>"
            )
        elif line.startswith("* ") or line.startswith("- "):
            if not in_list:
                html_parts.append("<ul style=\"padding-left:20px;margin:6px 0;\">")
                in_list = True
            html_parts.append(f"<li style=\"margin:4px 0;\">{format_inline(line[2:])}</li>")
        else:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f"<p style=\"margin:8px 0;\">{format_inline(line)}</p>")

    if in_list:
        html_parts.append("</ul>")
    html_parts.append("</body></html>")
    return "\n".join(html_parts)


def send_email(subject: str, md_body: str) -> None:
    sender = os.environ["SENDER_EMAIL"].strip()
    recipient = os.environ["RECIPIENT_EMAIL"].strip()
    password = os.environ["SMTP_PASSWORD"].strip()
    server_host = os.environ.get("SMTP_SERVER", "").strip() or "smtp.gmail.com"
    server_port = int(os.environ.get("SMTP_PORT", "").strip() or "465")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    msg.attach(MIMEText(md_body, "plain", "utf-8"))
    msg.attach(MIMEText(md_to_html(md_body), "html", "utf-8"))

    context = ssl.create_default_context()
    if server_port == 465:
        with smtplib.SMTP_SSL(server_host, server_port, context=context, timeout=30) as server:
            server.login(sender, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(server_host, server_port, timeout=30) as server:
            server.starttls(context=context)
            server.login(sender, password)
            server.send_message(msg)


def main() -> int:
    now_cn = datetime.datetime.now(ZoneInfo("Asia/Shanghai"))
    today_str = now_cn.strftime("%Y-%m-%d")
    print(f"[{today_str}] Generating global finance briefing...")

    md_body = generate_briefing(today_str)
    subject = f"全球金融与财政每日简报 {today_str}"

    send_email(subject, md_body)
    print(f"[{today_str}] Successfully sent email to {os.environ['RECIPIENT_EMAIL']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
