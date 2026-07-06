#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
COMFY="$ROOT/runtime/comfyui"
PYTHON="$COMFY/.venv/bin/python"
COMFY_COMMIT="35c1470935044be5610a81d46e57922a8a598c6c"

clone_at() {
    local url=$1 destination=$2 commit=$3
    if [[ ! -d "$destination/.git" ]]; then
        git clone "$url" "$destination"
    fi
    git -C "$destination" fetch --depth 1 origin "$commit"
    git -C "$destination" checkout --detach "$commit"
}

clone_at https://github.com/Comfy-Org/ComfyUI.git "$COMFY" "$COMFY_COMMIT"
if [[ ! -x "$PYTHON" ]]; then
    python3 -m venv "$COMFY/.venv"
fi
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
"$PYTHON" -m pip install -r "$COMFY/requirements.txt"

clone_at https://github.com/Fannovel16/comfyui_controlnet_aux.git     "$COMFY/custom_nodes/comfyui_controlnet_aux" e8b689a513c3e6b63edc44066560ca5919c0576e
clone_at https://github.com/cubiq/ComfyUI_essentials.git     "$COMFY/custom_nodes/ComfyUI_essentials" 9d9f4bedfc9f0321c19faf71855e228c93bd0dc9
clone_at https://github.com/rgthree/rgthree-comfy.git     "$COMFY/custom_nodes/rgthree-comfy" 27b4f4cdcf3b127c29d5d8135ac1536ecbd4c383
clone_at https://github.com/WASasquatch/was-node-suite-comfyui.git     "$COMFY/custom_nodes/was-node-suite-comfyui" ea935d1044ae5a26efa54ebeb18fe9020af49a45

mkdir -p "$COMFY/custom_nodes/aec_utility_nodes"
cp -a "$ROOT/comfyui/custom_nodes/aec_utility_nodes/." "$COMFY/custom_nodes/aec_utility_nodes/"
sed '/^onnxruntime-gpu$/d'     "$COMFY/custom_nodes/comfyui_controlnet_aux/requirements.txt"     > "$ROOT/runtime/controlnet-aux-requirements-arm64.txt"
"$PYTHON" -m pip install     -r "$ROOT/runtime/controlnet-aux-requirements-arm64.txt"     -r "$COMFY/custom_nodes/ComfyUI_essentials/requirements.txt"     -r "$COMFY/custom_nodes/was-node-suite-comfyui/requirements.txt"

download_model() {
    local url=$1 target=$2 sha=$3
    mkdir -p "$(dirname "$target")"
    if [[ -f "$target" ]] && echo "$sha  $target" | sha256sum -c - >/dev/null 2>&1; then
        return
    fi
    if [[ -f "$target" ]]; then
        mv "$target" "$target.bad.$(date +%s)"
    fi
    curl -fL --silent --show-error --retry 5 -C - -o "$target.part" "$url"
    if ! echo "$sha  $target.part" | sha256sum -c -; then
        mv "$target.part" "$target.part.bad.$(date +%s)"
        return 1
    fi
    mv "$target.part" "$target"
}

download_model     https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-kv-fp8/resolve/main/flux-2-klein-9b-kv-fp8.safetensors     "$COMFY/models/diffusion_models/flux/flux-2-klein-9b.safetensors"     33f7da5625a00798349a719742999d3c7dd20c1a7eda14663922c363640728f1
download_model     https://huggingface.co/Comfy-Org/flux2-klein-9B/resolve/main/split_files/text_encoders/qwen_3_8b_fp8mixed.safetensors     "$COMFY/models/text_encoders/klein/qwen_3_8b_fp8mixed.safetensors"     abad16806e0cbabc54e0325d6565847443fe396d5f0be38bb3cd3fe75a1201d6
download_model     https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/vae/flux2-vae.safetensors     "$COMFY/models/vae/flux/flux2-vae.safetensors"     d64f3a68e1cc4f9f4e29b6e0da38a0204fe9a49f2d4053f0ec1fa1ca02f9c4b5

"$PYTHON" -c "import torch; assert torch.cuda.is_available(); print('COMFY_CUDA_OK', torch.__version__, torch.cuda.get_device_name(0))"
echo "COMFY_PORTABLE_RUNTIME_OK=$COMFY"
