#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/runtime/cad-tools"
PYTHON="$VENV/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    python3 -m venv "$VENV"
fi
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install "rhino3dm==8.17.0"
"$PYTHON" -c "import rhino3dm; assert rhino3dm.__version__ == '8.17.0'; print('CAD_TOOLS_RHINO3DM_OK', rhino3dm.__version__)"
echo "CAD_TOOLS_RUNTIME_OK=$VENV"
