#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export AEC_PORTABLE_ROOT="$ROOT"
PHASE_DELAY="${AEC_AUTO_PHASE_DELAY:-5}"
CYCLE_DELAY="${AEC_AUTO_CYCLE_DELAY:-60}"
KEEP_FINAL_SETS="${AEC_AUTO_KEEP_FINAL_SETS:-12}"

exec python3 "$ROOT/scripts/run-portable-demo-loop.py" \
  --cycles 0 \
  --phase-delay "$PHASE_DELAY" \
  --cycle-delay "$CYCLE_DELAY" \
  --keep-final-sets "$KEEP_FINAL_SETS" \
  "$@"
