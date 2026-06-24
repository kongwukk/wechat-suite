#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_CONFIG="$SCRIPT_DIR/config.yaml"
if [[ -f "$SCRIPT_DIR/config.local.yaml" ]]; then
  DEFAULT_CONFIG="$SCRIPT_DIR/config.local.yaml"
fi
CONFIG_PATH="${1:-$DEFAULT_CONFIG}"

echo "[run_group_daily] using config: $CONFIG_PATH"

exec "$SCRIPT_DIR/.venv/bin/python" \
  "$SCRIPT_DIR/run_group_daily_pipeline.py" \
  --config "$CONFIG_PATH"
