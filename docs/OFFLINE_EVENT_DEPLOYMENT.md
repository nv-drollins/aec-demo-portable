# Offline Event Deployment

Use this workflow when the destination will not have reliable internet. It
creates a self-contained archive from a fully working Ubuntu 24.04 ARM64 source
machine and restores the demo without downloading applications, Python
packages, ComfyUI models, or Ollama models at the venue.

The destination must already have:

- Ubuntu 24.04 ARM64
- current NVIDIA or DGX drivers
- the desktop user `nvidia` with `sudo` access
- at least 250 GB of free space under `/home/nvidia`
- an attached desktop display for FreeCAD and Blender

The offline runtime is intentionally pinned to
`/home/nvidia/AEC_Demo_Portable`. Python virtual environments contain absolute
interpreter paths and are not supported under a different user or directory.

## 1. Prepare the connected source machine

Finish a normal online installation and confirm that the complete demo works:

```bash
cd /home/nvidia/AEC_Demo_Portable
git pull --ff-only
./scripts/install-portable-runtime.sh
./scripts/restart-portable-demo.sh
./scripts/preflight-portable-demo.sh
```

The installer now prepares FreeCAD MCP inside
`runtime/freecad-mcp/.venv`. Hermes uses the checked
`scripts/run-freecad-mcp.sh` command directly, so it will not invoke an
implicit `uv sync` at the event.

Choose the Ollama model for the destination hardware before packaging:

- GB300 workstation with ample memory: `qwen3.5:122b` is the tested
  high-capability option.
- Standard 128 GB DGX Spark: use the smaller validated model configured for
  that machine unless the larger model has been tested alongside ComfyUI.

Remove models that should not consume USB space:

```bash
ollama list
ollama stop MODEL_NAME
ollama rm UNUSED_MODEL_NAME
```

Pull and test the final model while internet access is still reliable. The
packager copies the complete active Ollama model store. If one model remains,
it becomes the default automatically. If multiple models remain, pass
`--default-model MODEL_NAME`.

## 2. Audit before packaging

The audit writes nothing:

```bash
./scripts/package-portable-offline.sh \
  --audit-only \
  --default-model qwen3.5:122b
```

It verifies the platform, clean Git state, source assets, Blender, FreeCAD,
prepared FreeCAD MCP, CAD tools, ComfyUI, Hermes, Ollama runtime, model store,
and recorded-demo fallback checkpoints.

An actual package refuses a dirty Git working tree so the archived scripts
always correspond to the source commit recorded in its manifest.

## 3. Build the offline archive

The default includes `projects/recorded_demo` so the known-good checkpoints
and final images remain available as an event fallback:

```bash
./scripts/package-portable-offline.sh \
  --default-model qwen3.5:122b
```

The command creates three files under `transfer/`:

```text
aec-demo-portable-offline-TIMESTAMP.tar.gz
aec-demo-portable-offline-TIMESTAMP.tar.gz.sha256
aec-demo-portable-offline-TIMESTAMP.tar.gz.contents.txt
```

Most model and scene files are already compressed. For a fast external SSD,
an uncompressed tar often saves substantial creation and extraction time
without growing dramatically:

```bash
./scripts/package-portable-offline.sh \
  --default-model qwen3.5:122b \
  --compression none
```

Use `--without-projects` only when the 24 GB recorded fallback is not wanted.

The packager:

- exports the tracked repository at the current commit;
- copies the delivered source assets and portable runtime;
- excludes transient ComfyUI output, temporary files, recovery state, and
  partial downloads;
- copies only the Hermes application runtime and its managed Python runtime,
  not authentication, history, memories, pastes, logs, or user configuration;
- copies the Ollama executable, support libraries, manifests, and model blobs;
- downloads a recursive Ubuntu dependency set and builds an isolated local APT
  repository;
- writes a JSON manifest and internal SHA-256 file;
- writes an outer archive checksum and contents listing;
- never copies a GPU UUID or local `config/runtime.env`.

Packaging temporarily stops Ollama while its model store is copied, then starts
the service again.

## 4. Copy to USB storage

Use a 512 GB USB 3.2 external SSD formatted as exFAT or ext4. FAT32 cannot hold
files larger than 4 GB.

Copy the archive, checksum, and contents list, then flush pending writes:

```bash
cp transfer/aec-demo-portable-offline-TIMESTAMP.tar* /media/nvidia/USB_LABEL/
sync
```

Do not remove the drive until `sync` finishes.

## 5. Verify and extract on the destination

Copy the three files from USB to a local directory. Verify the outer archive
before extraction:

```bash
mkdir -p /home/nvidia/offline-deploy
cd /home/nvidia/offline-deploy
cp /media/nvidia/USB_LABEL/aec-demo-portable-offline-TIMESTAMP.tar* .

sha256sum -c aec-demo-portable-offline-TIMESTAMP.tar.gz.sha256
tar -xzf aec-demo-portable-offline-TIMESTAMP.tar.gz
cd aec-demo-portable-offline-TIMESTAMP
```

For an uncompressed `.tar`, use:

```bash
sha256sum -c aec-demo-portable-offline-TIMESTAMP.tar.sha256
tar -xf aec-demo-portable-offline-TIMESTAMP.tar
```

The outer checksum must report `OK`.

## 6. Install without internet

Run the installer as `nvidia`, not with `sudo`:

```bash
./install-portable-offline.sh
```

The installer automatically verifies the expanded bundle, then:

1. uses only the bundled local APT repository for missing libraries;
2. restores the repository, assets, runtime, and fallback checkpoints;
3. generates a fresh machine-local `config/runtime.env`;
4. restores the sanitized Hermes runtime;
5. installs Ollama and its support libraries;
6. restores the bundled Ollama model store with correct ownership;
7. creates the Ollama service without a source-machine GPU selector;
8. sets the bundled default model, context length, and infinite keep-alive;
9. repairs FreeCAD MCP links and registers the direct MCP runner with Hermes;
10. performs static installed-runtime verification.

If the expanded bundle was already checked manually, avoid hashing it twice:

```bash
./verify-portable-offline.sh --bundle .
./install-portable-offline.sh --skip-checksums
```

## 7. Apply optional destination GPU selection

On a single-GPU Spark, leave `CUDA_VISIBLE_DEVICES` unset.

On a workstation with both a GB300 and an RTX PRO GPU, follow the optional
second-GPU instructions in
[INSTALL_GUIDE.md](INSTALL_GUIDE.md#optional-dedicate-a-second-gpu-to-ollama).
Discover and use the destination GB300 UUID. Never copy the UUID from the source
machine.

## 8. Complete desktop verification

With the destination desktop session active:

```bash
cd /home/nvidia/AEC_Demo_Portable
./scripts/verify-portable-offline.sh --installed --start-services
```

This checks Hermes, the bundled Ollama model, Blender, the Rhino reader,
FreeCAD MCP, ComfyUI CUDA, all required model files, service startup, workflow
nodes, and the normal portable preflight.

Preload the event model:

```bash
curl http://127.0.0.1:11434/api/generate \
  -d '{"model":"qwen3.5:122b","keep_alive":-1}'
ollama ps
```

The `UNTIL` column should report `Forever`.

## 9. Perform a disconnected rehearsal

Disable networking or physically disconnect the network, reboot the
destination, and run:

```bash
cd /home/nvidia/AEC_Demo_Portable
./scripts/restart-portable-demo.sh
./scripts/preflight-portable-demo.sh
./scripts/start-portable-manual-demo.sh
```

Run at least one complete Phase 2–12 cycle while disconnected. This is the only
reliable proof that no hidden cache miss or online dependency remains.

## Event-day startup

```bash
cd /home/nvidia/AEC_Demo_Portable
./scripts/restart-portable-demo.sh
./scripts/status-portable-demo.sh
./scripts/start-portable-manual-demo.sh
```

Keep the archive and recorded-demo checkpoints on the external SSD as a
fallback throughout the event.
