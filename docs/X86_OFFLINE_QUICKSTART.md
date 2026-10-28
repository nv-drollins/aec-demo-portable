# x86 Workstation Quick Build & Offline USB Guide

This is the single end-to-end runbook for an **x86_64 (`amd64`) Ubuntu 24.04
workstation** (single or dual NVIDIA GPUs, such as dual RTX PRO 6000 / 5000
Blackwell):

1. Build from a fresh Ubuntu 24.04 install (online)
2. Package the self-contained offline USB archive
3. Install and verify from that USB archive on a wiped/offline Ubuntu 24.04 machine

---

## Part 1: Fresh Ubuntu 24.04 Build (Connected Source Machine)

### 1. OS, NVIDIA driver, and Xorg prerequisites

- Install Ubuntu 24.04 Desktop (`amd64`) with username **`nvidia`** (`/home/nvidia`).
- Ensure the NVIDIA driver is installed and `nvidia-smi` lists the GPU(s).
- Force **Xorg** (FreeCAD and Blender MCP target `DISPLAY=:1` under Xorg, not Wayland):

```bash
sudo sed -i 's/^#\?WaylandEnable=.*/WaylandEnable=false/' /etc/gdm3/custom.conf
```

- Install the build-machine packages (`git`, `curl`, `python3-venv` for fetching the repo/payload; `dpkg-dev` and `pigz` for building the offline bundle):

```bash
sudo apt update
sudo apt install -y git curl python3-venv dpkg-dev pigz openssh-server
```

Log into the desktop session on the monitor (or reboot if you changed `WaylandEnable=false` and log in).

### 2. Clone `x86-dual-gpu` and extract the payload

```bash
cd /home/nvidia
git clone -b x86-dual-gpu https://github.com/nv-drollins/aec-demo-portable.git AEC_Demo_Portable

python3 -m venv ~/.venvs/gdown
~/.venvs/gdown/bin/pip install -q --upgrade gdown

~/.venvs/gdown/bin/gdown --continue 1BmZM-zApyu2sGcPgJuk2EFLibAwjoWE- \
  -O aec-demo-portable-payload-demo-20260707_130002.tar.gz
~/.venvs/gdown/bin/gdown 1cSwuquJ5L4xXVeJEGEHgZ5Q6OinK3_wv \
  -O aec-demo-portable-payload-demo-20260707_130002.tar.gz.sha256

sha256sum -c aec-demo-portable-payload-demo-*.tar.gz.sha256   # must report OK
tar -xzf aec-demo-portable-payload-demo-*.tar.gz -C /home/nvidia/AEC_Demo_Portable
```

### 3. Install the portable runtime

```bash
cd /home/nvidia/AEC_Demo_Portable
./scripts/install-portable-runtime.sh
```

This installs CAD tools, FreeCAD 1.1.1 (`x86_64` AppImage), Hermes Agent,
Ollama `0.40.4`, pulls the default `nemotron-3.5-lightning:30b` model, installs
FreeCAD MCP, Blender 5.1.2 (`linux-x64`), ComfyUI + Flux.2 Klein models, and
resolves the per-service GPU split (`config/gpu-assignment.env`).

### 4. Run one full cycle to populate fallback checkpoints

Running one full cycle before packaging validates the stack and populates
`projects/recorded_demo/` so the offline bundle includes fresh fallback
checkpoints:

```bash
cd /home/nvidia/AEC_Demo_Portable
./scripts/restart-portable-demo.sh
./scripts/start-portable-auto-hermes-demo.sh
```

Wait for `AUTOPLAY_COMPLETE cycles=1` and the final Hermes summary.

---

## Part 2: Build the Offline USB Archive

The Ollama installer adds `nvidia` to the `ollama` group so the packager can
read `/usr/share/ollama/.ollama/models`, but shells opened before the install do
not carry that group yet. Use `newgrp ollama` (or open a fresh login session)
and stop the resident model before packaging:

```bash
cd /home/nvidia/AEC_Demo_Portable
ollama stop nemotron-3.5-lightning:30b

newgrp ollama <<'EOF'
./scripts/package-portable-offline.sh \
  --audit-only \
  --default-model nemotron-3.5-lightning:30b

./scripts/package-portable-offline.sh \
  --default-model nemotron-3.5-lightning:30b \
  --compression none
EOF
```

*(Omit `--compression none` if you prefer a `.tar.gz` over a faster uncompressed `.tar`.)*

Copy the generated archive, checksum, and contents list to your exFAT/ext4 USB SSD:

```bash
cp transfer/aec-demo-portable-offline-*.tar* /media/nvidia/USB_LABEL/
sync
```

---

## Part 3: Clean Offline Install from USB (Destination Machine)

On a freshly imaged Ubuntu 24.04 `amd64` machine with the NVIDIA driver
installed, `WaylandEnable=false` in `/etc/gdm3/custom.conf`, and user `nvidia`
logged into the desktop:

### 1. Copy from USB, verify, and extract

```bash
mkdir -p /home/nvidia/offline-deploy
cd /home/nvidia/offline-deploy
cp /media/nvidia/USB_LABEL/aec-demo-portable-offline-*.tar* .

# For uncompressed .tar:
sha256sum -c aec-demo-portable-offline-*.tar.sha256
tar -xf aec-demo-portable-offline-*.tar

# (Or for compressed .tar.gz: sha256sum -c *.tar.gz.sha256 && tar -xzf *.tar.gz)
cd aec-demo-portable-offline-*/
```

### 2. Run the offline installer

```bash
./install-portable-offline.sh --skip-checksums
```

*(We pass `--skip-checksums` because `sha256sum -c` on the outer archive just verified every byte.)*

Expect:
```text
OFFLINE_APT_INSTALL_OK requested=20
OFFLINE_RUNTIME_FREECAD_ARCH_SET=FreeCAD_1.1.1-Linux-x86_64-py311.AppImage
OFFLINE_INSTALL_OK=/home/nvidia/AEC_Demo_Portable
```

### 3. Start services, preload the model, and run the demo

```bash
cd /home/nvidia/AEC_Demo_Portable
./scripts/verify-portable-offline.sh --installed --start-services
ollama run nemotron-3.5-lightning:30b "ready" --keepalive -1m
ollama ps
```

Then launch the demo:

```bash
# Automatic Hermes presenter mode (one full Phase 2-12 cycle):
./scripts/start-portable-auto-hermes-demo.sh

# Manual per-phase human-approval mode:
./scripts/start-portable-manual-demo.sh

# Unattended continuous kiosk loop:
./scripts/start-portable-auto-demo.sh
```
