"""Export a configured WeChat group chat and generate the daily Markdown report."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from summarize_export_chat import (
    load_config,
    resolve_config_path,
    resolve_target_date,
    safe_name,
)


def run_export(decrypt_repo: Path, chat_name: str, export_json: Path) -> None:
    decrypt_python = decrypt_repo / ".venv" / "bin" / "python"
    export_script = decrypt_repo / "export_chat.py"

    if not decrypt_python.exists():
        raise SystemExit(f"missing decrypt python: {decrypt_python}")
    if not export_script.exists():
        raise SystemExit(f"missing export script: {export_script}")

    export_json.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(decrypt_python), str(export_script), chat_name, str(export_json)],
        cwd=str(decrypt_repo),
        check=True,
    )


def run_summary(project_dir: Path, config_path: Path, chat_name: str, target_date: str, export_json: Path) -> None:
    summarize_script = project_dir / "summarize_export_chat.py"
    subprocess.run(
        [
            sys.executable,
            str(summarize_script),
            "--config",
            str(config_path),
            "--input",
            str(export_json),
            "--date",
            target_date,
            "--chat-name",
            chat_name,
        ],
        cwd=str(project_dir),
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Export WeChat chat and generate daily markdown.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--chat-name", help="Override group_daily.chat_name")
    parser.add_argument("--date", help='Override group_daily.date, format YYYY-MM-DD or "today"')
    parser.add_argument("--input", help="Override group_daily.input_json")
    parser.add_argument("--decrypt-repo", help="Override group_daily.decrypt_repo")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    project_dir = config_path.parent
    config = load_config(str(config_path))
    group_daily_cfg = config.get("group_daily", {}) or {}

    chat_name = args.chat_name or group_daily_cfg.get("chat_name")
    if not chat_name:
        raise SystemExit("missing chat name: set group_daily.chat_name in config.yaml or pass --chat-name")

    target_date = resolve_target_date(args.date or group_daily_cfg.get("date"))
    input_value = args.input or group_daily_cfg.get("input_json") or f"markdown_exports/{safe_name(chat_name)}-export.json"
    decrypt_repo_value = args.decrypt_repo or group_daily_cfg.get("decrypt_repo") or "../wechat-decrypt"

    export_json = resolve_config_path(config_path, input_value)
    decrypt_repo = resolve_config_path(config_path, decrypt_repo_value)

    print(f"[group_daily] config={config_path}")
    print(f"[group_daily] chat_name={chat_name}")
    print(f"[group_daily] date={target_date}")

    run_export(decrypt_repo, chat_name, export_json)
    run_summary(project_dir, config_path, chat_name, target_date, export_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
