# AEC Demo Portable — DGX Spark Installation Guide

This is the supported clean-install procedure for the public
`nv-drollins/aec-demo-portable` repository. It installs the current
Hermes/FreeCAD/Blender/ComfyUI workflow on NVIDIA DGX Spark.

This guide does not install the original Windows, Rhino, Claude Desktop, or OBS
workflow. Those files are retained only as upstream reference material.

Estimated time is 45 minutes to several hours, depending primarily on model
download speed. The installer is idempotent and can be rerun safely.

## 1. Requirements

Use a DGX Spark with:

- Ubuntu 24.04 ARM64 and current NVIDIA/DGX OS updates
- An attached desktop display for FreeCAD and Blender
- Internet access for GitHub, model, and runtime downloads
- A user with `sudo` access
- At least 80 GB of free disk space under `/home/nvidia`
- The separately distributed AEC payload archive

The workflow is local. It does not require an Anthropic key, OpenRouter key,
Nous Portal account, Rhino license, or Docker.

The installer provides:

- Hermes Agent
- Ollama and local `qwen3.6:latest`
- FreeCAD 1.1.1 ARM64 and FreeCAD MCP
- Blender 5.1 ARM64 and Blender MCP
- Isolated ComfyUI, required custom nodes, and Flux.2 Klein models
- The `rhino3dm` helper used to read the delivered `.3dm` source without Rhino

## 2. Prepare the Spark

Install current OS updates before starting:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

After reboot, open a terminal. The remaining commands assume the standard
`nvidia` account and `/home/nvidia/AEC_Demo_Portable` install location.

## 3. Clone the control repository

```bash
cd /home/nvidia
git clone https://github.com/nv-drollins/aec-demo-portable.git \
  AEC_Demo_Portable
cd /home/nvidia/AEC_Demo_Portable
```

Do not clone into `/home/nvidia/aec-demo`; that was an earlier development path.
The portable installer migrates that old path when possible, but new installs
should use `/home/nvidia/AEC_Demo_Portable`.

## 4. Download and extract the demo payload

Large source scenes and assets are not stored in ordinary Git.

Download these files through a browser into `/home/nvidia`:

- [Payload archive](https://drive.google.com/file/d/1BmZM-zApyu2sGcPgJuk2EFLibAwjoWE-/view?usp=sharing)
- [SHA-256 checksum](https://drive.google.com/file/d/1cSwuquJ5L4xXVeJEGEHgZ5Q6OinK3_wv/view?usp=sharing)
- [Archive contents list](https://drive.google.com/file/d/1vCgAOfh6D2UKSt_hAJYPBEGDMI9hmZYV/view?usp=sharing) — optional

### Optional command-line download

On a workstation with command-line access only, use
[`gdown`](https://github.com/wkentaro/gdown). It handles Google Drive's
large-file confirmation flow and can resume an interrupted archive download.

Install it in an isolated Python environment:

```bash
sudo apt update
sudo apt install -y python3-venv
python3 -m venv ~/.venvs/gdown
~/.venvs/gdown/bin/pip install --upgrade gdown
```

Download the required archive and checksum with their expected filenames:

```bash
cd /home/nvidia
GDOWN="$HOME/.venvs/gdown/bin/gdown"

"$GDOWN" --continue 1BmZM-zApyu2sGcPgJuk2EFLibAwjoWE- \
  -O aec-demo-portable-payload-demo-20260707_130002.tar.gz

"$GDOWN" 1cSwuquJ5L4xXVeJEGEHgZ5Q6OinK3_wv \
  -O aec-demo-portable-payload-demo-20260707_130002.tar.gz.sha256
```

Optionally download the archive contents listing:

```bash
"$GDOWN" 1vCgAOfh6D2UKSt_hAJYPBEGDMI9hmZYV \
  -O aec-demo-portable-payload-demo-20260707_130002.tar.gz.contents.txt
```

If the archive transfer is interrupted, rerun its `gdown --continue` command.

The published archive name is:

```text
aec-demo-portable-payload-demo-20260707_130002.tar.gz
```

Its expected SHA-256 is:

```text
15f2dfc6227e3665845886e0d9f6fb224c4040aa7a12b269abe7e36d2dae2dbd
```

Verify and extract it:

```bash
cd /home/nvidia
sha256sum -c aec-demo-portable-payload-demo-*.tar.gz.sha256
tar -xzf aec-demo-portable-payload-demo-*.tar.gz \
  -C /home/nvidia/AEC_Demo_Portable
```

The checksum command must report `OK`. Do not continue with a failed checksum.

If transferring from another Spark instead, create and copy a minimal payload:

```bash
# Source Spark
cd /home/nvidia/AEC_Demo_Portable
./scripts/package-portable-payload.sh
scp transfer/aec-demo-portable-payload-demo-*.tar.gz* \
  nvidia@NEW_SPARK:/home/nvidia/
```
Or package, checksum, and copy the payload in one command:

```bash
./scripts/transfer-portable-payload.sh --host NEW_SPARK
```

Add `--mode full` to transfer the entire delivered asset bundle instead of
the canonical demo subset. Use `--dry-run` to inspect the local package and
`scp` commands without creating or transferring the archive. The destination
repository must already be cloned at `/home/nvidia/AEC_Demo_Portable`.

Then run the same verification and extraction commands on the destination.

## 5. Install the portable runtime

```bash
cd /home/nvidia/AEC_Demo_Portable
./scripts/install-portable-runtime.sh
```

The installer downloads large files, including the local Hermes model and
ComfyUI model weights. Long pauses after Python package installation or while a
`.safetensors.part` file is downloading are normal. Leave the terminal open.
Completed downloads report checksum lines ending in `OK`.

A successful installation ends with:

```text
COMFY_CUDA_OK
COMFY_PORTABLE_RUNTIME_OK=...
BLENDER_VERSION=Blender 5.1.0
PORTABLE_PREFLIGHT_OK
COMFY_CONTROLLER_RUNTIME_OK root=/home/nvidia/AEC_Demo_Portable/runtime/comfyui url=http://127.0.0.1:8188
```

The installer creates `config/runtime.env` from the checked example when it is
missing. Runtime files and model weights remain under `runtime/` and are not
committed to Git.

### Optional staged installation

To test infrastructure before downloading the approximately 23 GB Ollama model:

```bash
AEC_SKIP_OLLAMA_MODEL_DOWNLOAD=1 \
  ./scripts/install-portable-runtime.sh
```

The complete demo remains blocked until this finishes:

```bash
ollama pull qwen3.6:latest
./scripts/preflight-portable-demo.sh
```

### Optional: dedicate a second GPU to Ollama

Skip this section on a standard DGX Spark or any system with only one NVIDIA
GPU. Leave `CUDA_VISIBLE_DEVICES` unset in that case; Ollama will select the
available GPU automatically.

On a workstation that has both a GB300 and a second NVIDIA GPU, the recommended
split is to reserve the GB300 for Ollama while Blender, ComfyUI, and the desktop
continue using the discrete RTX GPU. First identify the physical devices and
copy the complete GB300 UUID:

```bash
nvidia-smi -L
```

Edit the existing Ollama systemd override:

```bash
sudo systemctl edit ollama
```

Merge these settings into its `[Service]` section, replacing the example value
with the GB300 UUID reported by `nvidia-smi -L`. Never copy a UUID from another
machine.

```ini
[Service]
Environment="CUDA_DEVICE_ORDER=PCI_BUS_ID"
Environment="CUDA_VISIBLE_DEVICES=GPU-REPLACE-WITH-THIS-MACHINE-GB300-UUID"
Environment="OLLAMA_CONTEXT_LENGTH=262144"
Environment="OLLAMA_KEEP_ALIVE=-1"
Environment="OLLAMA_VULKAN=0"
```

Apply the override:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Confirm that the selector reached the Ollama server:

```bash
sudo systemctl show ollama -p Environment --value \
  | tr ' ' '\n' \
  | grep -E 'CUDA_VISIBLE_DEVICES|CUDA_DEVICE_ORDER|OLLAMA_CONTEXT|OLLAMA_KEEP_ALIVE|OLLAMA_VULKAN'
```

After loading the selected model, use `nvidia-smi` to verify that the Ollama
runner occupies the intended physical GPU. Ollama may call that device
`CUDA0` internally because the selected physical GPU becomes its only visible
logical device. With `OLLAMA_KEEP_ALIVE=-1`, `ollama ps` should report
`Forever`; explicitly run `ollama stop MODEL_NAME` before switching to a
different large model.

## 6. Start and verify the services

```bash
cd /home/nvidia/AEC_Demo_Portable
./scripts/restart-portable-demo.sh
./scripts/status-portable-demo.sh
```

The controller starts:

| Service | Local endpoint |
|---|---|
| FreeCAD MCP RPC | `127.0.0.1:9875` |
| Blender MCP | `127.0.0.1:9876` |
| ComfyUI | `127.0.0.1:8188` |

The required healthy state is:

```text
FREECAD_MCP=healthy
BLENDER_MCP=healthy ... version=5.1.0
COMFYUI=healthy
FLUX_MODELS_MISSING=0
WORKFLOW_NODES_MISSING=0
PORTABLE_STACK_OK
```

You may also run the strict check directly:

```bash
./scripts/preflight-portable-demo.sh
```

FreeCAD and Blender should appear on the desktop. ComfyUI is available at
`http://127.0.0.1:8188`.

### Blender Python warning

The checked launcher enables automatic Python execution for the trusted
delivered scene. If Blender was opened manually and displays an auto-execution
warning, close it and use `restart-portable-demo.sh`. Only enable automatic
execution manually for files you trust.

## 7. Choose a demonstration mode

### Manual Hermes walkthrough

```bash
./scripts/start-portable-manual-demo.sh
```

This opens an interactive Hermes terminal. Paste the opening instruction from
[SPARK_RUNBOOK.md](SPARK_RUNBOOK.md#manual-mode-open-hermes-and-enter-the-prompt).
Hermes prepares each phase and stops for a human approval before executing it.

### One automatic Hermes-supervised cycle

```bash
./scripts/start-portable-auto-hermes-demo.sh
```

Use this mode when Hermes should be visibly involved but repeated manual
approvals would slow the presentation. Launching it authorizes exactly one
checked Phase 2–12 cycle. Hermes narrates progress and does not modify the
manual workflow's approval policy.

For denser terminal narration:

```bash
AEC_HERMES_AUTO_POLL_SECONDS=5 \
  ./scripts/start-portable-auto-hermes-demo.sh
```

### Unattended looping presentation

Run in the current terminal:

```bash
./scripts/start-portable-auto-demo.sh
```

Or open a dedicated visible terminal:

```bash
./scripts/start-portable-auto-terminal.sh
```

Stop the loop with `Ctrl+C`. To stop the demo services afterward:

```bash
./scripts/stop-portable-demo.sh
```

## 8. Confirm the final result

The complete workflow produces FreeCAD and Blender checkpoints plus three final
ComfyUI images:

```text
projects/recorded_demo/freecad/
projects/recorded_demo/blender/
projects/recorded_demo/test_renders/
projects/recorded_demo/final_outputs/
```

Phase 12 must report:

```text
PORTABLE_FINAL_CAMERA_OK
PORTABLE_FINAL_STRUCTURE_OK
PORTABLE_FINAL_SUBMISSION_OK
PORTABLE_FINAL_IMAGES_OK count=3
PORTABLE_FINAL_PREPARATION_OK
```

The current structural contract reports camera-v3, exact rendered camera depth,
strength `0.98`, and `required_visible_levels=3`.

## 9. After a reboot or power loss

No reinstall is required:

```bash
cd /home/nvidia/AEC_Demo_Portable
./scripts/restart-portable-demo.sh
```

The restart controller clears stale service state and archives FreeCAD recovery
files that could otherwise open a modal recovery dialog.

## 10. Updating an installed Spark

```bash
cd /home/nvidia/AEC_Demo_Portable
git pull --ff-only origin main
./scripts/install-portable-runtime.sh
./scripts/restart-portable-demo.sh
```

Rerunning the installer applies new dependencies and configuration migrations
without redownloading verified files unnecessarily.

## Troubleshooting

### `libspnav.so.0` or other Blender libraries are missing

Update the repository and rerun the installer. The current installer resolves
and verifies the ARM64 shared-library set:

```bash
git pull --ff-only origin main
./scripts/install-portable-runtime.sh
```

### Preflight references `/home/nvidia/aec-demo`

This is stale configuration from an early development checkout. Rerun the
current installer; it migrates `config/runtime.env` to the current root:

```bash
./scripts/install-portable-runtime.sh
```

### FreeCAD MCP reports connection refused

```bash
./scripts/restart-portable-demo.sh
./scripts/status-portable-demo.sh
```

Do not launch FreeCAD from an unrelated desktop shortcut; the checked launcher
loads the MCP bootstrap and starts RPC on port 9875.

### Blender MCP reports connection refused

Close manually launched Blender instances and run:

```bash
./scripts/restart-portable-demo.sh
```

The controller rejects stale or incompatible Blender servers on port 9876.

### ComfyUI appears stuck during installation

Model files are large. Check the installer terminal for a growing `.part` file
or wait for its checksum line. Do not interrupt while a model is downloading.

### `PORTABLE_PREFLIGHT_BLOCKED`

Run:

```bash
./scripts/status-portable-demo.sh
./scripts/preflight-portable-demo.sh
```

Resolve the specific `ERROR=` or `MISSING_...` line. Do not bypass preflight for
a recorded or public demonstration.

### Hermes compacts repeatedly or is slow

The default tested model is `ollama/qwen3.6:latest`. Confirm it is installed:

```bash
ollama list
```

Start a fresh Hermes session between long rehearsals. Within the manual demo,
do not use `/new` between a phase proposal and its approval; use it only before
restarting the walkthrough from Phase 1.

## Historical Windows instructions

Older revisions of this file described Windows, Rhino 8, Claude Desktop, OBS,
and manually installed ComfyUI. Those instructions do not apply to the Spark
port. The relevant upstream details remain available through Git history and in
clearly historical reference documents such as `REBUILD_GUIDE.md` and
`CLAUDE_ASSISTANT_GUIDE.md`.
