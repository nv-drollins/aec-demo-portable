#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME="$ROOT/runtime/blender"
DOWNLOADS="$ROOT/runtime/downloads"
PACKAGES="$ROOT/runtime/packages"
ARCHIVE="$DOWNLOADS/blender-v10.tar.xz"
URL="https://github.com/CoconutMacaroon/blender-arm64/releases/download/v10-5.1/blender-v10.tar.xz"
SHA256="f8c41e767bfb8e42c0e3190ec5132c3bae413c568a17664388341c67d543ab1a"

mkdir -p "$RUNTIME" "$DOWNLOADS" "$PACKAGES"
if [[ -f "$ARCHIVE" ]] && ! echo "$SHA256  $ARCHIVE" | sha256sum -c - >/dev/null 2>&1; then
    mv "$ARCHIVE" "$ARCHIVE.bad.$(date +%s)"
fi
if [[ ! -f "$ARCHIVE" ]]; then
    curl -fL --retry 3 -C - -o "$ARCHIVE" "$URL"
fi
echo "$SHA256  $ARCHIVE" | sha256sum -c -

if [[ ! -x "$RUNTIME/bin/blender" ]]; then
    tar -xJf "$ARCHIVE" -C "$RUNTIME" --strip-components=2
fi

download_package() {
    local package=$1
    local found
    found="$(find "$DOWNLOADS" -maxdepth 1 -type f -name "${package}_*arm64.deb" -print -quit)"
    if [[ -z "$found" ]]; then
        (cd "$DOWNLOADS" && apt download "$package")
        found="$(find "$DOWNLOADS" -maxdepth 1 -type f -name "${package}_*arm64.deb" -print -quit)"
    fi
    mkdir -p "$PACKAGES/$package"
    dpkg-deb -x "$found" "$PACKAGES/$package"
}

download_package libgoogle-glog0v6t64
download_package libgflags2.2
download_package libmetis5
download_package libspnav0
mkdir -p "$RUNTIME/libExt"
find "$PACKAGES" -type f \( -name 'libglog.so*' -o -name 'libgflags.so*' -o -name 'libmetis.so*' -o -name 'libspnav.so*' \) -exec cp -a {} "$RUNTIME/libExt/" \;
find "$PACKAGES" -type l \( -name 'libglog.so*' -o -name 'libgflags.so*' -o -name 'libmetis.so*' -o -name 'libspnav.so*' \) -exec cp -a {} "$RUNTIME/libExt/" \;

chmod +x "$ROOT/scripts/blender-portable.sh"

MISSING_LIBS="$(
    LD_LIBRARY_PATH="$RUNTIME/libExt${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
        ldd "$RUNTIME/bin/blender" |
        awk '/not found/ {print $1}' |
        sort -u
)"
if [[ -n "$MISSING_LIBS" ]]; then
    echo "BLENDER_PORTABLE_LIBRARIES_MISSING" >&2
    printf 'MISSING_LIBRARY=%s\n' $MISSING_LIBS >&2
    exit 1
fi
echo "BLENDER_PORTABLE_LIBRARIES_OK"

"$ROOT/scripts/blender-portable.sh" --version
echo "BLENDER_SPARK_RUNTIME_OK=$RUNTIME"
