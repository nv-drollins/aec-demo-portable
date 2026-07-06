#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HERMES_BIN="${HERMES_BIN:-$HOME/.local/bin/hermes}"

if [[ ! -x "$HERMES_BIN" ]]; then
  echo "Hermes was not found at: $HERMES_BIN" >&2
  echo "Set HERMES_BIN to the installed Hermes executable and retry." >&2
  exit 1
fi

python3 "$ROOT/scripts/portable_stack.py" start

echo
echo "Opening the interactive Hermes chat in $ROOT"
echo "Paste the recorded-demo opening instruction from docs/SPARK_RUNBOOK.md."
echo

cd "$ROOT"
exec "$HERMES_BIN" chat "$@"
