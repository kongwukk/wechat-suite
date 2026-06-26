#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_CONFIG="$SCRIPT_DIR/config.yaml"
if [[ -f "$SCRIPT_DIR/config.local.yaml" ]]; then
  DEFAULT_CONFIG="$SCRIPT_DIR/config.local.yaml"
fi

CONFIG_PATH="$DEFAULT_CONFIG"
EXTRA_ARGS=()
if [[ $# -gt 0 ]]; then
  if [[ "$1" == "--config" || "$1" == "-c" ]]; then
    EXTRA_ARGS=("$@")
  elif [[ "$1" == --* ]]; then
    EXTRA_ARGS=("$@")
  else
    CONFIG_PATH="$1"
    shift
    EXTRA_ARGS=("$@")
  fi
fi

PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
if [[ ! -x "$PYTHON_BIN" && -x "$SCRIPT_DIR/.venv/Scripts/python.exe" ]]; then
  PYTHON_BIN="$SCRIPT_DIR/.venv/Scripts/python.exe"
fi
if [[ ! -x "$PYTHON_BIN" && -x "$SCRIPT_DIR/venv/bin/python" ]]; then
  PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
fi
if [[ ! -x "$PYTHON_BIN" && -x "$SCRIPT_DIR/venv/Scripts/python.exe" ]]; then
  PYTHON_BIN="$SCRIPT_DIR/venv/Scripts/python.exe"
fi
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

echo "[run_group_daily] using config: $CONFIG_PATH"

exec "$PYTHON_BIN" \
  "$SCRIPT_DIR/run_group_daily_pipeline.py" \
  --config "$CONFIG_PATH" \
  "${EXTRA_ARGS[@]}"
