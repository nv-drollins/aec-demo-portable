#!/usr/bin/env bash
# Shared platform resolution for AEC Demo Portable.
#
# The supported reference platform is DGX Spark / GB10 (Ubuntu 24.04 arm64).
# A second supported platform is an Ubuntu 24.04 amd64 workstation with
# discrete NVIDIA GPUs. Source this file to resolve the per-architecture
# runtime downloads; it sets variables only and starts nothing.

aec_resolve_platform() {
    AEC_ARCH="$(dpkg --print-architecture)"
    case "$AEC_ARCH" in
    arm64)
        AEC_FREECAD_APPIMAGE="FreeCAD_1.1.1-Linux-aarch64-py311.AppImage"
        AEC_FREECAD_SHA256="8004e166dc5c516cc8e8d85a5f58b5d56c3836cf8652301c2e6b9e4b1fd27827"
        # Community ARM64 build; no official Blender arm64 Linux release exists.
        AEC_BLENDER_URL="https://github.com/CoconutMacaroon/blender-arm64/releases/download/v10-5.1/blender-v10.tar.xz"
        AEC_BLENDER_ARCHIVE="blender-v10.tar.xz"
        AEC_BLENDER_SHA256="f8c41e767bfb8e42c0e3190ec5132c3bae413c568a17664388341c67d543ab1a"
        AEC_BLENDER_STRIP=2
        AEC_BLENDER_NEEDS_PRIVATE_LIBS=1
        # The community ARM64 archive nests the binary under bin/.
        AEC_BLENDER_BIN_SUBPATH="bin/blender"
        ;;
    amd64)
        AEC_FREECAD_APPIMAGE="FreeCAD_1.1.1-Linux-x86_64-py311.AppImage"
        AEC_FREECAD_SHA256="e2006138400b2fa85fa2e160e872d00767eb32964e85075830f7e198a3a876e1"
        # Official upstream Blender build; it ships its own bundled libraries.
        AEC_BLENDER_URL="https://mirrors.dotsrc.org/blender/release/Blender5.1/blender-5.1.2-linux-x64.tar.xz"
        AEC_BLENDER_ARCHIVE="blender-5.1.2-linux-x64.tar.xz"
        AEC_BLENDER_SHA256="aaccb355f50183979b698bcce7467103a76261b5fa59f4972295842662a285fb"
        AEC_BLENDER_STRIP=1
        AEC_BLENDER_NEEDS_PRIVATE_LIBS=0
        # The official upstream archive puts the binary at the root.
        AEC_BLENDER_BIN_SUBPATH="blender"
        ;;
    *)
        echo "UNSUPPORTED_ARCHITECTURE=$AEC_ARCH" >&2
        echo "Supported: arm64 (DGX Spark) and amd64 (workstation)." >&2
        return 1
        ;;
    esac
    AEC_FREECAD_URL="https://github.com/FreeCAD/FreeCAD/releases/download/1.1.1/$AEC_FREECAD_APPIMAGE"
    export AEC_ARCH AEC_FREECAD_APPIMAGE AEC_FREECAD_SHA256 AEC_FREECAD_URL
    export AEC_BLENDER_URL AEC_BLENDER_ARCHIVE AEC_BLENDER_SHA256
    export AEC_BLENDER_STRIP AEC_BLENDER_NEEDS_PRIVATE_LIBS AEC_BLENDER_BIN_SUBPATH
}

aec_resolve_platform
