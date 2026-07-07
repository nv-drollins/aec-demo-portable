#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$ROOT/scripts/portable_stack.py" preflight "$@"
python3 "$ROOT/scripts/run-comfy-demo.py" --check-runtime
