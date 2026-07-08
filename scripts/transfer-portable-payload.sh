#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="demo"
REMOTE_USER="nvidia"
REMOTE_HOST=""
REMOTE_DIR="/home/nvidia"
PORT="22"
IDENTITY=""
OUTPUT=""
DRY_RUN=false

usage() {
  cat <<'EOF'
Package the portable AEC payload and copy it to another machine over SSH.

Usage:
  ./scripts/transfer-portable-payload.sh --host HOST [options]

Required:
  --host HOST             Destination hostname or IP address.

Options:
  --user USER             Destination SSH user (default: nvidia).
  --remote-dir DIRECTORY  Existing destination directory (default: /home/nvidia).
  --mode demo|full        Payload mode passed to package-portable-payload.sh
                          (default: demo).
  --output FILE.tar.gz    Local archive path. Defaults to transfer/ with a
                          timestamped name.
  --port PORT             SSH port (default: 22).
  --identity FILE         SSH private key passed to scp with -i.
  --dry-run               Print the package and copy operations without running.
  -h, --help              Show this help.

Modes:
  demo  Canonical assets required by the checked demo.
  full  Entire sample_project, assets, and Blender add-on payload.

This transfers the payload archive, SHA-256 file, and contents list. It does
not transfer runtime/, projects/, Ollama's system model store, the Git history,
or machine-specific system configuration. Clone the control repository and run
the portable installer on the destination machine.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      [[ $# -ge 2 ]] || { echo "Missing value for --host" >&2; exit 2; }
      REMOTE_HOST="$2"
      shift 2
      ;;
    --user)
      [[ $# -ge 2 ]] || { echo "Missing value for --user" >&2; exit 2; }
      REMOTE_USER="$2"
      shift 2
      ;;
    --remote-dir)
      [[ $# -ge 2 ]] || { echo "Missing value for --remote-dir" >&2; exit 2; }
      REMOTE_DIR="$2"
      shift 2
      ;;
    --mode)
      [[ $# -ge 2 ]] || { echo "Missing value for --mode" >&2; exit 2; }
      MODE="$2"
      shift 2
      ;;
    --output)
      [[ $# -ge 2 ]] || { echo "Missing value for --output" >&2; exit 2; }
      OUTPUT="$2"
      shift 2
      ;;
    --port)
      [[ $# -ge 2 ]] || { echo "Missing value for --port" >&2; exit 2; }
      PORT="$2"
      shift 2
      ;;
    --identity)
      [[ $# -ge 2 ]] || { echo "Missing value for --identity" >&2; exit 2; }
      IDENTITY="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

[[ -n "$REMOTE_HOST" ]] || {
  echo "--host is required" >&2
  usage >&2
  exit 2
}

if [[ "$MODE" != "demo" && "$MODE" != "full" ]]; then
  echo "--mode must be demo or full" >&2
  exit 2
fi

if [[ ! "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1 || PORT > 65535 )); then
  echo "--port must be an integer from 1 through 65535" >&2
  exit 2
fi

if [[ -n "$IDENTITY" && ! -f "$IDENTITY" ]]; then
  echo "SSH identity file is missing: $IDENTITY" >&2
  exit 2
fi

if [[ -z "$OUTPUT" ]]; then
  STAMP="$(date -u +%Y%m%d_%H%M%S)"
  OUTPUT="$ROOT/transfer/aec-demo-portable-payload-${MODE}-${STAMP}.tar.gz"
elif [[ "$OUTPUT" != /* ]]; then
  OUTPUT="$PWD/$OUTPUT"
fi

REMOTE="${REMOTE_USER}@${REMOTE_HOST}"
REMOTE_DEST="${REMOTE}:${REMOTE_DIR%/}/"
PACKAGE_COMMAND=(
  "$ROOT/scripts/package-portable-payload.sh"
  --mode "$MODE"
  --output "$OUTPUT"
)
SCP_COMMAND=(scp -P "$PORT")
if [[ -n "$IDENTITY" ]]; then
  SCP_COMMAND+=(-i "$IDENTITY")
fi
SCP_COMMAND+=(
  "$OUTPUT"
  "$OUTPUT.sha256"
  "$OUTPUT.contents.txt"
  "$REMOTE_DEST"
)

if [[ "$DRY_RUN" == true ]]; then
  printf 'DRY_RUN_PACKAGE='
  printf '%q ' "${PACKAGE_COMMAND[@]}"
  printf '\nDRY_RUN_COPY='
  printf '%q ' "${SCP_COMMAND[@]}"
  printf '\n'
  exit 0
fi

command -v scp >/dev/null 2>&1 || {
  echo "scp is required but was not found" >&2
  exit 1
}

"${PACKAGE_COMMAND[@]}"

for path in "$OUTPUT" "$OUTPUT.sha256" "$OUTPUT.contents.txt"; do
  [[ -f "$path" ]] || {
    echo "Expected package output is missing: $path" >&2
    exit 1
  }
done

echo "PAYLOAD_TRANSFER_BEGIN destination=$REMOTE_DEST"
"${SCP_COMMAND[@]}"
echo "PAYLOAD_TRANSFER_OK destination=$REMOTE_DEST"

OUTPUT_NAME="$(basename "$OUTPUT")"
cat <<EOF

On the destination machine:

  cd $REMOTE_DIR
  sha256sum -c $OUTPUT_NAME.sha256
  tar -xzf $OUTPUT_NAME -C /home/nvidia/AEC_Demo_Portable

The destination control repository must already be cloned at:
  /home/nvidia/AEC_Demo_Portable
EOF
