"""Summarize an exported WeChat chat JSON into a Markdown report."""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from openai import OpenAI

from proxy_env import normalize_proxy_env


LOG = logging.getLogger(__name__)

API_BASES = {
    "deepseek": "https://api.deepseek.com",
    "newapi": "http://127.0.0.1:3000/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "openai": "https://api.openai.com/v1",
}

DEFAULT_MODELS = {
    "deepseek": "deepseek-chat",
    "newapi": "gpt-4o-mini",
    "qwen": "qwen-plus",
    "openai": "gpt-4o",
}

FILTERED_TYPES = {"system", "sticker"}
FILTERED_CONTENT_PATTERNS = [
    re.compile(r"^\[表情\]$"),
]


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve_config_path(config_path: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return (config_path.parent / path).resolve()


def get_report_config(config: dict, mode: str) -> dict[str, Any]:
    if mode == "personal":
        return config.get("personal_chat", {}) or {}
    return config.get("group_daily", {}) or {}


def resolve_target_date(raw_value: str | None) -> str:
    if not raw_value or raw_value.lower() == "today":
        return datetime.now().strftime("%Y-%m-%d")
    datetime.strptime(raw_value, "%Y-%m-%d")
    return raw_value


def resolve_date_window(
    raw_date: str | None,
    raw_start_date: str | None = None,
    raw_end_date: str | None = None,
) -> tuple[str, str]:
    if raw_start_date or raw_end_date:
        start_date = resolve_target_date(raw_start_date or raw_end_date)
        end_date = resolve_target_date(raw_end_date or raw_start_date)
    else:
        start_date = resolve_target_date(raw_date)
        end_date = start_date

    if start_date > end_date:
        raise ValueError(f"start_date must be <= end_date: {start_date} > {end_date}")
    return start_date, end_date


def format_date_label(start_date: str, end_date: str, *, for_filename: bool = False) -> str:
    if start_date == end_date:
        return start_date
    separator = "_to_" if for_filename else " 至 "
    return f"{start_date}{separator}{end_date}"


def filter_messages(messages: list[dict], start_date: str, end_date: str) -> list[dict]:
    kept: list[dict] = []
    for msg in messages:
        timestamp = msg.get("timestamp")
        if not timestamp:
            continue

        msg_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
        if msg_date < start_date or msg_date > end_date:
            continue

        msg_type = msg.get("type", "text")
        if msg_type in FILTERED_TYPES:
            continue

        content = (msg.get("content") or "").strip()
        if not content:
            continue

        if any(pattern.search(content) for pattern in FILTERED_CONTENT_PATTERNS):
            continue

        kept.append(msg)

    return kept


def build_chat_text(
    chat_name: str,
    date_label: str,
    messages: list[dict],
    max_messages: int,
    mode: str,
    my_nickname: str = "",
    show_message_date: bool = False,
) -> str:
    if len(messages) > max_messages:
        messages = messages[-max_messages:]

    sender_counts = Counter((msg.get("sender") or "匿名成员") for msg in messages)
    top_senders = "，".join(f"{sender}({count})" for sender, count in sender_counts.most_common(12))
    chat_label = "联系人" if mode == "personal" else "群聊"
    sender_label = "发言人" if mode == "personal" else "活跃成员"

    lines = [
        f"{chat_label}: {chat_name}",
        f"日期范围: {date_label}",
        f"消息数: {len(messages)}",
        f"{sender_label}: {top_senders}",
    ]
    if my_nickname:
        lines.append(f"我的昵称: {my_nickname}")

    lines.extend(["", "聊天记录:"])

    for msg in messages:
        sender = (msg.get("sender") or "匿名成员").strip() or "匿名成员"
        content = (msg.get("content") or "").replace("\n", " ").strip()
        if len(content) > 500:
            content = content[:500] + "..."
        time_format = "%m-%d %H:%M" if show_message_date else "%H:%M"
        time_text = datetime.fromtimestamp(msg["timestamp"]).strftime(time_format)
        lines.append(f"[{time_text}] {sender}: {content}")

    return "\n".join(lines)


def build_group_prompt(chat_text: str) -> str:
    return f"""你是一个微信群聊分析助手。请根据下面某个微信群在指定日期的聊天记录，输出一份面向群主/成员都能直接阅读的 Markdown 日报。

要求：
1. 不要使用第一人称“我”，而是站在旁观者视角总结整个群当天发生了什么。
2. 重点提炼真正有信息量的内容，忽略寒暄、刷屏、纯表情、纯图片。
3. 总结群内讨论的主要主题、大家给出的建议、达成的共识、争议点、值得后续跟进的问题。
4. 如果聊天里出现明确的工具名、产品名、仓库名、报错、价格、配置方案，可以点出来。
5. 如果没有明确待办，就写“未见明确群内待办”。
6. 输出必须是 Markdown，格式严格如下：

# {{日期}} {{群名}} 群聊日报

## 今日概览
用 120-220 字概括当天核心讨论。

## 重点话题
- 3 到 6 条，每条尽量具体

## 值得关注的信息
- 列出工具、方案、价格、报错、链接方向、资源推荐等

## 后续待跟进
- 如果有就列出
- 没有就写“未见明确群内待办”

下面是聊天记录：

{chat_text}
"""


def build_personal_prompt(chat_text: str) -> str:
    return f"""你是一个细致、克制的私人聊天分析助手。请根据下面某个联系人和用户在指定日期或时间范围内的聊天记录，输出一份 Markdown 个人关系与信息摘要。

要求：
1. 重点分析这个人对用户的态度、情绪倾向、关注点、提出的建议、明确请求、隐含期待和需要后续回应的事项。
2. 所有判断必须基于聊天文本，避免读心、夸大或给出心理诊断；证据不足时要明确写“不确定”或“证据不足”。
3. 区分“对方明确说了什么”和“可以谨慎推断什么”。
4. 不要把用户自己的表达误判成对方态度；如果 sender 是 me 或用户昵称，视为用户消息。
5. 输出必须是 Markdown，格式严格如下：

# {{日期}} {{联系人}} 个人聊天摘要

## 核心概览
用 100-180 字概括这段对话最重要的信息。

## 对方对用户的态度
- 态度判断：友好 / 支持 / 中立 / 有压力 / 不满 / 暧昧 / 疏离 / 无法判断，可多选
- 依据：列出 2 到 5 条来自聊天内容的具体依据，避免长篇引用
- 不确定性：说明哪些判断证据不足

## 对方的建议
- 列出对方明确提出的建议、提醒、反对意见或推荐方案
- 没有就写“未见明确建议”

## 对方的需求与期待
- 列出对方希望用户做什么、回应什么、避免什么
- 没有就写“未见明确需求”

## 关键信息
- 列出时间、地点、人物、产品、链接方向、价格、承诺、结论等

## 建议回应
- 给出 2 到 4 条用户接下来可以如何回复或跟进的建议

下面是聊天记录：

{chat_text}
"""


def build_prompt(chat_text: str, mode: str) -> str:
    if mode == "personal":
        return build_personal_prompt(chat_text)
    return build_group_prompt(chat_text)


def call_model(config: dict, prompt: str) -> str:
    ai_cfg = config["ai"]
    provider = ai_cfg.get("provider", "deepseek").lower()
    api_key = ai_cfg["api_key"]
    base_url = ai_cfg.get("base_url") or API_BASES.get(provider, API_BASES["deepseek"])
    requested_model = ai_cfg.get("model") or DEFAULT_MODELS.get(provider, DEFAULT_MODELS["deepseek"])
    fallback_models = list(dict.fromkeys([requested_model, DEFAULT_MODELS.get(provider, requested_model)]))

    client = OpenAI(api_key=api_key, base_url=base_url)
    last_error: Exception | None = None

    for model in fallback_models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=ai_cfg.get("max_tokens", 4096),
                temperature=0.3,
            )
            LOG.info("summary generated with model=%s", model)
            return response.choices[0].message.content or ""
        except Exception as exc:  # pragma: no cover - network/API error path
            last_error = exc
            LOG.warning("model=%s failed: %s", model, exc)

    if last_error is not None:
        raise last_error
    raise RuntimeError("no model available")


def safe_name(value: str) -> str:
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value.strip())
    safe = re.sub(r"\s+", "_", safe)
    return safe.strip("._-") or "chat"


def write_markdown(output_dir: Path, date_label: str, chat_name: str, content: str, mode: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = "personal-summary" if mode == "personal" else "summary"
    path = output_dir / f"{date_label}-{safe_name(chat_name)}-{suffix}.md"
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize exported chat JSON to Markdown.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--input", help="Path to exported chat JSON")
    parser.add_argument("--date", help='Target date in YYYY-MM-DD, or "today"')
    parser.add_argument("--start-date", help='Start date in YYYY-MM-DD, or "today"')
    parser.add_argument("--end-date", help='End date in YYYY-MM-DD, or "today"')
    parser.add_argument("--output-dir", help="Directory for generated markdown")
    parser.add_argument("--chat-name", help="Override chat name shown in the report")
    parser.add_argument("--max-messages", type=int, help="Maximum number of messages sent to the model")
    parser.add_argument("--mode", choices=("group", "personal"), default="group", help="Report type")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    normalize_proxy_env()

    config_path = Path(args.config).resolve()
    config = load_config(str(config_path))
    report_cfg = get_report_config(config, args.mode)

    chat_name = args.chat_name or report_cfg.get("chat_name")
    default_input = f"markdown_exports/{safe_name(chat_name or 'chat')}-export.json"
    default_output = "personal_chat_exports" if args.mode == "personal" else "group_daily_exports"
    input_value = args.input or report_cfg.get("input_json") or default_input
    output_value = args.output_dir or report_cfg.get("output_dir", default_output)
    start_date, end_date = resolve_date_window(
        args.date or report_cfg.get("date"),
        args.start_date or report_cfg.get("start_date"),
        args.end_date or report_cfg.get("end_date"),
    )
    date_label = format_date_label(start_date, end_date)
    filename_date_label = format_date_label(start_date, end_date, for_filename=True)
    max_messages = args.max_messages or int(report_cfg.get("max_messages", 260))
    my_nickname = config.get("wechat", {}).get("my_nickname", "")

    input_path = resolve_config_path(config_path, input_value)
    output_dir = resolve_config_path(config_path, output_value)

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    fallback_chat_name = "联系人" if args.mode == "personal" else "微信群"
    chat_name = chat_name or payload.get("chat", fallback_chat_name)
    messages = filter_messages(payload.get("messages", []), start_date, end_date)
    if not messages:
        raise SystemExit(f"no messages found for {date_label}")

    chat_text = build_chat_text(
        chat_name,
        date_label,
        messages,
        max_messages,
        args.mode,
        my_nickname,
        show_message_date=start_date != end_date,
    )
    prompt = build_prompt(chat_text, args.mode)
    markdown = call_model(config, prompt)
    output_path = write_markdown(output_dir, filename_date_label, chat_name, markdown, args.mode)

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
