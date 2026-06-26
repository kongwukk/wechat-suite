"""Export a configured WeChat chat and generate a Markdown report."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from summarize_export_chat import (
    format_date_label,
    get_report_config,
    load_config,
    resolve_date_window,
    resolve_config_path,
    safe_name,
)


def _python_candidates(project_dir: Path) -> list[Path]:
    return [
        project_dir / ".venv" / "Scripts" / "python.exe",
        project_dir / ".venv" / "Scripts" / "python",
        project_dir / ".venv" / "bin" / "python",
        project_dir / ".venv" / "bin" / "python3",
        project_dir / "venv" / "Scripts" / "python.exe",
        project_dir / "venv" / "Scripts" / "python",
        project_dir / "venv" / "bin" / "python",
        project_dir / "venv" / "bin" / "python3",
    ]


def resolve_python_command(project_dir: Path) -> list[str]:
    for candidate in _python_candidates(project_dir):
        if candidate.exists():
            return [str(candidate)]

    if os.name == "nt":
        py_launcher = shutil.which("py")
        if py_launcher:
            return [py_launcher, "-3"]

    for executable in ("python", "python3"):
        found = shutil.which(executable)
        if found:
            return [found]

    if sys.executable:
        return [sys.executable]

    raise SystemExit(
        "missing Python for wechat-decrypt. On Windows, run setup_win11.bat "
        "from the repository root to create .venv environments."
    )


def run_export(decrypt_repo: Path, chat_name: str, export_json: Path) -> None:
    decrypt_python = resolve_python_command(decrypt_repo)
    export_script = decrypt_repo / "export_chat.py"

    if not export_script.exists():
        raise SystemExit(f"missing export script: {export_script}")

    export_json.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    subprocess.run(
        [*decrypt_python, str(export_script), chat_name, str(export_json)],
        cwd=str(decrypt_repo),
        env=env,
        check=True,
    )


def run_summary(
    project_dir: Path,
    config_path: Path,
    chat_name: str,
    start_date: str,
    end_date: str,
    export_json: Path,
    mode: str,
) -> None:
    summarize_script = project_dir / "summarize_export_chat.py"
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    subprocess.run(
        [
            sys.executable,
            str(summarize_script),
            "--config",
            str(config_path),
            "--input",
            str(export_json),
            "--start-date",
            start_date,
            "--end-date",
            end_date,
            "--chat-name",
            chat_name,
            "--mode",
            mode,
        ],
        cwd=str(project_dir),
        env=env,
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Export WeChat chat and generate daily markdown.")
    parser.add_argument("-c", "--config", default="config.yaml")
    parser.add_argument("--mode", choices=("group", "personal"), default="group", help="Report type")
    parser.add_argument("--chat-name", help="Override configured chat_name")
    parser.add_argument("--date", help='Override configured date, format YYYY-MM-DD or "today"')
    parser.add_argument("--start-date", help='Override configured start_date, format YYYY-MM-DD or "today"')
    parser.add_argument("--end-date", help='Override configured end_date, format YYYY-MM-DD or "today"')
    parser.add_argument("--input", help="Override configured input_json")
    parser.add_argument("--decrypt-repo", help="Override configured decrypt_repo")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    project_dir = config_path.parent
    config = load_config(str(config_path))
    report_cfg = get_report_config(config, args.mode)

    chat_name = args.chat_name or report_cfg.get("chat_name")
    if not chat_name:
        config_key = "personal_chat.chat_name" if args.mode == "personal" else "group_daily.chat_name"
        raise SystemExit(f"missing chat name: set {config_key} in config.yaml or pass --chat-name")

    start_date, end_date = resolve_date_window(
        args.date or report_cfg.get("date"),
        args.start_date or report_cfg.get("start_date"),
        args.end_date or report_cfg.get("end_date"),
    )
    date_label = format_date_label(start_date, end_date)
    input_value = args.input or report_cfg.get("input_json") or f"markdown_exports/{safe_name(chat_name)}-export.json"
    decrypt_repo_value = args.decrypt_repo or report_cfg.get("decrypt_repo") or "../wechat-decrypt"

    export_json = resolve_config_path(config_path, input_value)
    decrypt_repo = resolve_config_path(config_path, decrypt_repo_value)

    label = "personal_chat" if args.mode == "personal" else "group_daily"
    print(f"[{label}] config={config_path}")
    print(f"[{label}] chat_name={chat_name}")
    print(f"[{label}] date={date_label}")

    run_export(decrypt_repo, chat_name, export_json)
    run_summary(project_dir, config_path, chat_name, start_date, end_date, export_json, args.mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
