#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/platform-lib.sh
source "$ROOT/scripts/platform-lib.sh"
RUNTIME="$ROOT/runtime/blender"
DOWNLOADS="$ROOT/runtime/downloads"
PACKAGES="$ROOT/runtime/packages"
ARCHIVE="$DOWNLOADS/$AEC_BLENDER_ARCHIVE"
URL="$AEC_BLENDER_URL"
SHA256="$AEC_BLENDER_SHA256"

BLENDER_BIN="$RUNTIME/$AEC_BLENDER_BIN_SUBPATH"

mkdir -p "$RUNTIME" "$DOWNLOADS" "$PACKAGES"
if [[ -f "$ARCHIVE" ]] && ! echo "$SHA256  $ARCHIVE" | sha256sum -c - >/dev/null 2>&1; then
    mv "$ARCHIVE" "$ARCHIVE.bad.$(date +%s)"
fi
if [[ ! -f "$ARCHIVE" ]]; then
    curl -fL --retry 3 -C - -o "$ARCHIVE" "$URL"
fi
echo "$SHA256  $ARCHIVE" | sha256sum -c -

if [[ ! -x "$BLENDER_BIN" ]]; then
    tar -xJf "$ARCHIVE" -C "$RUNTIME" --strip-components="$AEC_BLENDER_STRIP"
fi
if [[ ! -x "$BLENDER_BIN" ]]; then
    echo "BLENDER_BINARY_NOT_FOUND=$BLENDER_BIN arch=$AEC_ARCH" >&2
    exit 1
fi

mkdir -p "$RUNTIME/libExt"

if [[ "$AEC_BLENDER_NEEDS_PRIVATE_LIBS" == "1" ]]; then
    # The community ARM64 build links against system libraries that Ubuntu
    # 24.04 does not install by default. Stage private copies under libExt.
    download_package() {
        local package=$1
        local found
        found="$(find "$DOWNLOADS" -maxdepth 1 -type f -name "${package}_*${AEC_ARCH}.deb" -print -quit)"
        if [[ -z "$found" ]]; then
            (cd "$DOWNLOADS" && apt download "$package")
            found="$(find "$DOWNLOADS" -maxdepth 1 -type f -name "${package}_*${AEC_ARCH}.deb" -print -quit)"
        fi
        mkdir -p "$PACKAGES/$package"
        dpkg-deb -x "$found" "$PACKAGES/$package"
    }

    download_package libgoogle-glog0v6t64
    download_package libgflags2.2
    download_package libmetis5
    download_package libspnav0
    find "$PACKAGES" -type f \( -name 'libglog.so*' -o -name 'libgflags.so*' -o -name 'libmetis.so*' -o -name 'libspnav.so*' \) -exec cp -a {} "$RUNTIME/libExt/" \;
    find "$PACKAGES" -type l \( -name 'libglog.so*' -o -name 'libgflags.so*' -o -name 'libmetis.so*' -o -name 'libspnav.so*' \) -exec cp -a {} "$RUNTIME/libExt/" \;
else
    echo "BLENDER_PRIVATE_LIBRARIES_SKIPPED=official_build_bundles_its_own arch=$AEC_ARCH"
fi

chmod +x "$ROOT/scripts/blender-portable.sh"

missing_libraries() {
    LD_LIBRARY_PATH="$RUNTIME/libExt${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
        ldd "$BLENDER_BIN" |
        awk '/not found/ {print $1}' |
        sort -u
}

MISSING_LIBS="$(missing_libraries)"
if [[ -n "$MISSING_LIBS" ]]; then
    SYSTEM_PACKAGES=(
        libavcodec60
        libavdevice60
        libavformat60
        libavutil58
        libswscale7
        libblosc1
        libfftw3-double3
        libopenexr-3-1-30
        libimath-3-1-29t64
        libosdcpu3.5.0t64
        libosdgpu3.5.0t64
        libpotrace0
        libpugixml1v5
        libpystring0
        libyaml-cpp0.8
    )
    if ! command -v sudo >/dev/null 2>&1; then
        echo "BLENDER_SYSTEM_DEPENDENCIES_REQUIRE_SUDO" >&2
        printf 'REQUIRED_PACKAGE=%s\n' "${SYSTEM_PACKAGES[@]}" >&2
        exit 1
    fi
    echo "BLENDER_SYSTEM_DEPENDENCIES_INSTALLING packages=${SYSTEM_PACKAGES[*]}"
    sudo apt-get install -y --no-install-recommends "${SYSTEM_PACKAGES[@]}"
    MISSING_LIBS="$(missing_libraries)"
fi

if [[ -n "$MISSING_LIBS" ]]; then
    echo "BLENDER_PORTABLE_LIBRARIES_MISSING" >&2
    printf 'MISSING_LIBRARY=%s\n' $MISSING_LIBS >&2
    exit 1
fi
echo "BLENDER_PORTABLE_LIBRARIES_OK arch=$AEC_ARCH"

"$ROOT/scripts/blender-portable.sh" --version
echo "BLENDER_SPARK_RUNTIME_OK=$RUNTIME"
