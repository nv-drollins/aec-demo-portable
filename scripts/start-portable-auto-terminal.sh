#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v gnome-terminal >/dev/null 2>&1; then
    echo "gnome-terminal is unavailable; run $ROOT/scripts/start-portable-auto-demo.sh in the current terminal." >&2
    exit 1
fi

exec gnome-terminal \
    --title="AEC Portable Autoplay Monitor" \
    --geometry=150x42 \
    -- bash -lc '
script=$1
shift
"$script" "$@"
status=$?
printf "\nAEC autoplay exited with status %s. The terminal is staying open for review.\n" "$status"
exec bash
' bash "$ROOT/scripts/start-portable-auto-demo.sh" "$@"
