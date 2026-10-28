#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export AEC_PORTABLE_ROOT="$ROOT"
# shellcheck source=scripts/runtime-env-lib.sh
source "$ROOT/scripts/runtime-env-lib.sh"
aec_load_runtime_env "$ROOT"
# Booth demos run unattended: a dangerous-command approval prompt stalls the
# whole presentation behind a keypress nobody is watching for. Default to
# bypassing approvals, and keep an opt-out for rehearsals.
#
#   AEC_HERMES_UNATTENDED=0 ./scripts/<launcher>.sh   # restore the prompts
AEC_HERMES_UNATTENDED="${AEC_HERMES_UNATTENDED:-1}"
HERMES_APPROVAL_FLAGS=()
if [[ "$AEC_HERMES_UNATTENDED" == "1" ]]; then
    HERMES_APPROVAL_FLAGS+=(--yolo --accept-hooks)
fi
HERMES_BIN="${HERMES_BIN:-$HOME/.local/bin/hermes}"
HERMES_MODEL="${AEC_HERMES_MODEL:-ollama/nemotron-3.5-lightning:30b}"
PROMPT_PATH="$ROOT/prompts/auto/hermes_authorized_cycle.md"
RUNNER="$ROOT/scripts/run-portable-hermes-authorized-cycle.py"
AUTO_WORKSPACE="$ROOT/profiles/hermes_auto"
AUTO_HOME="$ROOT/runtime/hermes-auto-home"
AUTO_HOME_CONFIGURATOR="$ROOT/scripts/configure-hermes-auto-home.py"
POLL_SECONDS="${AEC_HERMES_AUTO_POLL_SECONDS:-10}"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"
AUTO_LOG="${AEC_HERMES_AUTO_LOG:-$LOG_DIR/auto-hermes-$(date -u +%Y%m%dT%H%M%SZ)-$$.log}"
export AEC_HERMES_AUTO_LOG="$AUTO_LOG"
exec > >(tee -a "$AUTO_LOG") 2>&1

if ! [[ "$POLL_SECONDS" =~ ^[0-9]+$ ]] || (( POLL_SECONDS < 5 || POLL_SECONDS > 60 )); then
    echo "AEC_HERMES_AUTO_POLL_SECONDS must be an integer from 5 through 60." >&2
    exit 1
fi

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
QUERY="${QUERY//__POLL_SECONDS__/$POLL_SECONDS}"

echo "HERMES_AUTO_LAUNCH_AUTHORIZED id=$AUTHORIZATION_ID scope=one_cycle phases=2-12"
echo "Hermes model: $HERMES_MODEL"
echo "Verbose progress refresh: ${POLL_SECONDS}s"
echo "Hermes auto transcript: $AUTO_LOG"
if [[ "$AEC_HERMES_UNATTENDED" == "1" ]]; then
    echo "Command approval prompts: BYPASSED (--yolo) for unattended playback."
    echo "Set AEC_HERMES_UNATTENDED=0 to restore interactive approvals."
else
    echo "This isolated session retains normal Hermes command safety controls."
fi

cd "$AUTO_WORKSPACE"
export AEC_HERMES_AUTO_AUTHORIZED=1
export AEC_HERMES_AUTO_AUTHORIZATION_ID="$AUTHORIZATION_ID"
export HERMES_HOME="$AUTO_HOME"

HERMES_PYTHON="${HERMES_PYTHON:-$HOME/.hermes/hermes-agent/venv/bin/python}"
if [[ "$HERMES_BIN" == "$HOME/.local/bin/hermes" && -x "$HERMES_PYTHON" ]]; then
    exec "$HERMES_PYTHON" -c '
import os, sys
import cli
from tools.process_registry import process_registry
from hermes_cli.main import main

_orig_chat = cli.HermesCLI.chat
poll_seconds = int(os.environ.get("AEC_HERMES_AUTO_POLL_SECONDS", "10"))

def _auto_chat(self, message, images=None):
    response = _orig_chat(self, message, images=images)
    continuations = 0
    while (
        not getattr(self, "_last_turn_interrupted", False)
        and continuations < 24
        and process_registry.has_any_active()
    ):
        continuations += 1
        active = [s for s in process_registry._running.values() if not s.exited]
        if not active:
            break
        sid = active[0].id
        nudge = (
            f"The authorized background runner ({sid}) is still running. "
            f"Immediately call the process tool with action=\"wait\", "
            f"session_id=\"{sid}\", and timeout={poll_seconds}, then continue "
            f"presenting new markers until status=exited."
        )
        response = _orig_chat(self, nudge)
    return response

cli.HermesCLI.chat = _auto_chat
sys.argv = [os.environ.get("HERMES_BIN", "hermes")] + sys.argv[1:]
main()
' chat \
        "${HERMES_APPROVAL_FLAGS[@]}" \
        --query "$QUERY" \
        --model "$HERMES_MODEL" \
        --toolsets terminal \
        --max-turns "${AEC_HERMES_AUTO_MAX_TURNS:-48}" \
        --source aec-auto \
        --cli
fi

exec "$HERMES_BIN" chat \
    "${HERMES_APPROVAL_FLAGS[@]}" \
    --query "$QUERY" \
    --model "$HERMES_MODEL" \
    --toolsets terminal \
    --max-turns "${AEC_HERMES_AUTO_MAX_TURNS:-48}" \
    --source aec-auto \
    --cli
