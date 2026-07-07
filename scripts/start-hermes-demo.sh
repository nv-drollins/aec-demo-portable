#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export AEC_PORTABLE_ROOT="$ROOT"
HERMES_BIN="${HERMES_BIN:-$HOME/.local/bin/hermes}"
HERMES_MODEL="${AEC_HERMES_MODEL:-ollama/qwen3.6:latest}"
HERMES_MAX_TURNS="${AEC_HERMES_MAX_TURNS:-30}"
HERMES_SKILLS="${AEC_HERMES_SKILLS:-prepare-portable-freecad-site,build-portable-freecad-massing,build-portable-freecad-detailing,build-portable-blender-landscaping,build-portable-blender-entourage,build-portable-blender-materials,build-portable-blender-camera,build-portable-blender-lighting,skip-portable-blender-animation,render-portable-blender-test-passes,run-portable-blender-comfy-final}"
MANUAL_HOME="$ROOT/runtime/hermes-manual-home"
MANUAL_HOME_CONFIGURATOR="$ROOT/scripts/configure-hermes-manual-home.py"

if [[ ! -x "$HERMES_BIN" ]]; then
  echo "Hermes was not found at: $HERMES_BIN" >&2
  echo "Set HERMES_BIN to the installed Hermes executable and retry." >&2
  exit 1
fi

if [[ ! -f "$ROOT/AGENTS.md" ]]; then
  echo "Required Hermes guardrails are missing: $ROOT/AGENTS.md" >&2
  exit 1
fi

if [[ ! -x "$MANUAL_HOME_CONFIGURATOR" ]]; then
  echo "Manual Hermes profile configurator is missing: $MANUAL_HOME_CONFIGURATOR" >&2
  exit 1
fi

python3 "$ROOT/scripts/prompt_profile.py" validate \
  "$ROOT/profiles/delivered_cliff_house_demo/prompt_profile.md"
python3 "$MANUAL_HOME_CONFIGURATOR" \
  --home "$MANUAL_HOME" \
  --root "$ROOT" \
  --model "$HERMES_MODEL"
HERMES_HOME="$MANUAL_HOME" AEC_HERMES_MODEL="$HERMES_MODEL" \
  python3 "$ROOT/scripts/register-hermes-skills.py"
python3 "$ROOT/scripts/portable_stack.py" start

echo
echo "Opening the interactive Hermes chat in $ROOT"
echo "Model: $HERMES_MODEL; maximum tool iterations per turn: $HERMES_MAX_TURNS"
echo "Preloaded skills: $HERMES_SKILLS"
echo "Paste the recorded-demo opening instruction from docs/SPARK_RUNBOOK.md."
echo "Hermes must stop at WAITING_FOR_HUMAN_APPROVAL before any phase mutation."
echo "Self-improvement is disabled for this isolated manual-demo session."
echo

cd "$ROOT"
exec "$HERMES_BIN" chat \
  --model "$HERMES_MODEL" \
  --max-turns "$HERMES_MAX_TURNS" \
  --skills "$HERMES_SKILLS" \
  "$@"
