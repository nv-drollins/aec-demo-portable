#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HERMES_BIN="${HERMES_BIN:-$HOME/.local/bin/hermes}"

if [[ ! -x "$HERMES_BIN" ]]; then
  echo "Hermes was not found at: $HERMES_BIN" >&2
  echo "Set HERMES_BIN to the installed Hermes executable and retry." >&2
  exit 1
fi

if [[ ! -f "$ROOT/AGENTS.md" ]]; then
  echo "Required Hermes guardrails are missing: $ROOT/AGENTS.md" >&2
  exit 1
fi

python3 "$ROOT/scripts/prompt_profile.py" validate \
  "$ROOT/profiles/delivered_cliff_house_demo/prompt_profile.md"
python3 "$ROOT/scripts/portable_stack.py" start

echo
echo "Opening the interactive Hermes chat in $ROOT"
echo "Paste the recorded-demo opening instruction from docs/SPARK_RUNBOOK.md."
echo "Hermes must stop at WAITING_FOR_HUMAN_APPROVAL before any phase mutation."
echo

cd "$ROOT"
exec "$HERMES_BIN" chat "$@"
