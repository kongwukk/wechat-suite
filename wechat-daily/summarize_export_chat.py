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


def get_group_daily_config(config: dict) -> dict[str, Any]:
    return config.get("group_daily", {}) or {}


def resolve_target_date(raw_value: str | None) -> str:
    if not raw_value or raw_value.lower() == "today":
        return datetime.now().strftime("%Y-%m-%d")
    datetime.strptime(raw_value, "%Y-%m-%d")
    return raw_value


def filter_messages(messages: list[dict], target_date: str) -> list[dict]:
    kept: list[dict] = []
    for msg in messages:
        timestamp = msg.get("timestamp")
        if not timestamp:
            continue

        msg_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
        if msg_date != target_date:
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


def build_chat_text(chat_name: str, target_date: str, messages: list[dict], max_messages: int) -> str:
    if len(messages) > max_messages:
        messages = messages[-max_messages:]

    sender_counts = Counter((msg.get("sender") or "匿名成员") for msg in messages)
    top_senders = "，".join(f"{sender}({count})" for sender, count in sender_counts.most_common(12))

    lines = [
        f"群聊: {chat_name}",
        f"日期: {target_date}",
        f"消息数: {len(messages)}",
        f"活跃成员: {top_senders}",
        "",
        "聊天记录:",
    ]

    for msg in messages:
        sender = (msg.get("sender") or "匿名成员").strip() or "匿名成员"
        content = (msg.get("content") or "").replace("\n", " ").strip()
        if len(content) > 500:
            content = content[:500] + "..."
        time_text = datetime.fromtimestamp(msg["timestamp"]).strftime("%H:%M")
        lines.append(f"[{time_text}] {sender}: {content}")

    return "\n".join(lines)


def build_prompt(chat_text: str) -> str:
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
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-") or "chat"


def write_markdown(output_dir: Path, target_date: str, chat_name: str, content: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{target_date}-{safe_name(chat_name)}-summary.md"
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize exported chat JSON to Markdown.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--input", help="Path to exported chat JSON")
    parser.add_argument("--date", help='Target date in YYYY-MM-DD, or "today"')
    parser.add_argument("--output-dir", help="Directory for generated markdown")
    parser.add_argument("--chat-name", help="Override chat name shown in the report")
    parser.add_argument("--max-messages", type=int, help="Maximum number of messages sent to the model")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    normalize_proxy_env()

    config_path = Path(args.config).resolve()
    config = load_config(str(config_path))
    group_daily_cfg = get_group_daily_config(config)

    chat_name = args.chat_name or group_daily_cfg.get("chat_name")
    default_input = f"markdown_exports/{safe_name(chat_name or 'chat')}-export.json"
    input_value = args.input or group_daily_cfg.get("input_json") or default_input
    output_value = args.output_dir or group_daily_cfg.get("output_dir", "group_daily_exports")
    target_date = resolve_target_date(args.date or group_daily_cfg.get("date"))
    max_messages = args.max_messages or int(group_daily_cfg.get("max_messages", 260))

    input_path = resolve_config_path(config_path, input_value)
    output_dir = resolve_config_path(config_path, output_value)

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    chat_name = chat_name or payload.get("chat", "微信群")
    messages = filter_messages(payload.get("messages", []), target_date)
    if not messages:
        raise SystemExit(f"no messages found for {target_date}")

    chat_text = build_chat_text(chat_name, target_date, messages, max_messages)
    prompt = build_prompt(chat_text)
    markdown = call_model(config, prompt)
    output_path = write_markdown(output_dir, target_date, chat_name, markdown)

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
