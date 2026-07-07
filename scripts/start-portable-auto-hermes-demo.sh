#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
HERMES_BIN="${HERMES_BIN:-$HOME/.local/bin/hermes}"
HERMES_MODEL="${AEC_HERMES_MODEL:-ollama/qwen3.6:latest}"
PROMPT_PATH="$ROOT/prompts/auto/hermes_authorized_cycle.md"
RUNNER="$ROOT/scripts/run-portable-hermes-authorized-cycle.py"
AUTO_WORKSPACE="$ROOT/profiles/hermes_auto"
AUTO_HOME="$ROOT/runtime/hermes-auto-home"
AUTO_HOME_CONFIGURATOR="$ROOT/scripts/configure-hermes-auto-home.py"

if [[ ! -x "$HERMES_BIN" ]]; then
    echo "Hermes was not found at: $HERMES_BIN" >&2
    echo "Run $ROOT/scripts/install-hermes-spark.sh and retry." >&2
    exit 1
fi
if [[ ! -f "$PROMPT_PATH" ]]; then
    echo "Hermes auto-cycle prompt is missing: $PROMPT_PATH" >&2
    exit 1
fi
if [[ ! -f "$RUNNER" ]]; then
    echo "Hermes authorized-cycle runner is missing: $RUNNER" >&2
    exit 1
fi
if [[ ! -f "$AUTO_WORKSPACE/AGENTS.md" ]]; then
    echo "Hermes auto workspace policy is missing: $AUTO_WORKSPACE/AGENTS.md" >&2
    exit 1
fi
if [[ ! -f "$AUTO_HOME_CONFIGURATOR" ]]; then
    echo "Hermes auto profile configurator is missing: $AUTO_HOME_CONFIGURATOR" >&2
    exit 1
fi

python3 "$AUTO_HOME_CONFIGURATOR" \
    --home "$AUTO_HOME" \
    --root "$ROOT" \
    --model "$HERMES_MODEL" \
    --timeout "${AEC_HERMES_AUTO_TERMINAL_TIMEOUT:-7200}" \
    --lifetime "${AEC_HERMES_AUTO_TERMINAL_LIFETIME:-7500}"

AUTHORIZATION_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
PROMPT="$(<"$PROMPT_PATH")"
printf -v RUNNER_COMMAND 'python3 %q' "$RUNNER"
QUERY="${PROMPT//__AUTHORIZED_RUNNER__/$RUNNER_COMMAND}"

echo "HERMES_AUTO_LAUNCH_AUTHORIZED id=$AUTHORIZATION_ID scope=one_cycle phases=2-12"
echo "Hermes model: $HERMES_MODEL"
echo "This isolated session retains normal Hermes command safety controls."

cd "$AUTO_WORKSPACE"
export AEC_HERMES_AUTO_AUTHORIZED=1
export AEC_HERMES_AUTO_AUTHORIZATION_ID="$AUTHORIZATION_ID"
export HERMES_HOME="$AUTO_HOME"

exec "$HERMES_BIN" chat \
    --query "$QUERY" \
    --model "$HERMES_MODEL" \
    --toolsets terminal \
    --max-turns "${AEC_HERMES_AUTO_MAX_TURNS:-5}" \
    --source aec-auto \
    --cli
