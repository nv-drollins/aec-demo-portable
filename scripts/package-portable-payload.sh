#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="demo"
OUTPUT=""

usage() {
  cat <<'EOF'
Package the non-Git AEC demo payload for transfer to another Spark.

Usage:
  ./scripts/package-portable-payload.sh [--mode demo|full] [--output FILE.tar.gz]

Modes:
  demo  Canonical scene, Rhino template, required HDRI, and Blender MCP add-on.
        This is sufficient for the checked manual and unattended demos.
  full  Entire sample_project, assets, and setup/blender_addons directories.

The script also writes FILE.tar.gz.sha256 and FILE.tar.gz.contents.txt.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
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

if [[ "$MODE" != "demo" && "$MODE" != "full" ]]; then
  echo "--mode must be demo or full" >&2
  exit 2
fi

if [[ -z "$OUTPUT" ]]; then
  STAMP="$(date -u +%Y%m%d_%H%M%S)"
  OUTPUT="$ROOT/transfer/aec-demo-portable-payload-${MODE}-${STAMP}.tar.gz"
elif [[ "$OUTPUT" != /* ]]; then
  OUTPUT="$PWD/$OUTPUT"
fi

mkdir -p "$(dirname "$OUTPUT")"

if [[ "$MODE" == "demo" ]]; then
  FILES=(
    "sample_project/blender_assets/cliff_house_act2_textured_v3.blend"
    "sample_project/rhino_assets/beach_house_02.3dm"
    "assets/hdri/qwantani_puresky_2k.hdr"
    "setup/blender_addons/BlenderMCP_addon.py"
  )
else
  FILES=(
    "sample_project"
    "assets"
    "setup/blender_addons"
  )
fi

for relative in "${FILES[@]}"; do
  if [[ ! -e "$ROOT/$relative" ]]; then
    echo "Required payload path is missing: $ROOT/$relative" >&2
    exit 1
  fi
done

case "$OUTPUT" in
  "$ROOT/sample_project"/*|"$ROOT/assets"/*|"$ROOT/setup/blender_addons"/*)
    echo "Output cannot be placed inside a packaged directory: $OUTPUT" >&2
    exit 2
    ;;
esac

echo "PAYLOAD_PACKAGE_BEGIN mode=$MODE output=$OUTPUT"
echo "Included paths:"
printf '  %s\n' "${FILES[@]}"
du -ch "${FILES[@]/#/$ROOT/}" | tail -1

if command -v pigz >/dev/null 2>&1; then
  COMPRESSOR="pigz -1"
else
  COMPRESSOR="gzip -1"
fi

tar \
  --create \
  --file "$OUTPUT" \
  --use-compress-program "$COMPRESSOR" \
  --directory "$ROOT" \
  "${FILES[@]}"

tar --list --gzip --file "$OUTPUT" >"$OUTPUT.contents.txt"
OUTPUT_DIR="$(dirname "$OUTPUT")"
OUTPUT_NAME="$(basename "$OUTPUT")"
(
  cd "$OUTPUT_DIR"
  sha256sum "$OUTPUT_NAME" >"$OUTPUT_NAME.sha256"
)

ARCHIVE_BYTES="$(stat --format '%s' "$OUTPUT")"
ARCHIVE_SHA256="$(sha256sum "$OUTPUT" | awk '{print $1}')"
echo "PAYLOAD_PACKAGE_OK mode=$MODE archive=$OUTPUT bytes=$ARCHIVE_BYTES sha256=$ARCHIVE_SHA256"
echo "PAYLOAD_CHECKSUM=$OUTPUT.sha256"
echo "PAYLOAD_CONTENTS=$OUTPUT.contents.txt"
