# AEC Demo Portable

> Repository note: the heavyweight extracted scenes, textures, models, and renders stay local and are intentionally ignored by ordinary Git. Source scripts, prompts, skills, workflows, and sanitized configuration examples are versioned here.

## DGX Spark control layer

A complete no-interview demo profile is available at
[profiles/delivered_cliff_house_demo/prompt_profile.md](profiles/delivered_cliff_house_demo/prompt_profile.md).

### New Spark quick start

Clone the control repository:

```bash
git clone https://github.com/nv-drollins/aec-demo-portable.git \
  /home/nvidia/AEC_Demo_Portable
cd /home/nvidia/AEC_Demo_Portable
```

The ignored scene payload is transferred separately. On an existing configured
Spark, create the minimal package:

```bash
./scripts/package-portable-payload.sh
```

Copy the generated `.tar.gz` and `.sha256` files to the new Spark, or download
the published payload from Google Drive. Verify the checksum and extract the
archive into the clone. See
[docs/DGX_SPARK_PORT.md](docs/DGX_SPARK_PORT.md#google-drive-download)
for download links and exact commands.

Then install and verify:

```bash
./scripts/install-portable-runtime.sh
./scripts/restart-portable-demo.sh
```

Choose the human-gated or unattended looping presentation:

```bash
./scripts/start-portable-manual-demo.sh
./scripts/start-portable-auto-demo.sh
```

The complete tested operating procedure is
[docs/SPARK_RUNBOOK.md](docs/SPARK_RUNBOOK.md).

This delivered package targets Windows, Claude Desktop, Rhino 8, Blender 5.1, and Flux.2 Klein. On the DGX Spark, start with [docs/DGX_SPARK_PORT.md](docs/DGX_SPARK_PORT.md) and the guarded service controller:

```bash
cp config/runtime.env.example config/runtime.env
./scripts/status-portable-demo.sh
./scripts/preflight-portable-demo.sh
./scripts/start-portable-demo.sh
```

The strict preflight prevents partial startup when Blender or ComfyUI is incompatible. The original Windows workflow below is preserved as supplied.

**AI-assisted architectural visualization using Claude, Blender, Rhino, and ComfyUI**

This package contains everything needed to run the AEC (Architectural, Engineering, Construction) AI visualization demo on a new Windows system.

---

## What It Does

The demo shows how an AI agent (Claude) can:
- Model and refine 3D architecture in Rhino via MCP
- Set up lighting, materials, and cameras in Blender via MCP
- Render photorealistic beauty, depth, and segmentation passes
- Submit renders to ComfyUI (Flux.2 Klein) for AI material/environment transformation
- Generate three simultaneous variations: Make Real, Change Environment, Time of Day

All of this is driven by natural language commands in Claude Desktop — no scripts to type manually.

---

## Quick Start

**First time? Follow these steps in order:**

```
1. setup\setup_windows.bat     ← Run as Administrator (sets env vars, firewall)
2. Copy config\user_config.example.yaml to config\user_config.yaml, then edit it ← Set your paths and API key
3. python setup\system_check.py ← Verify everything is installed
4. docs\INSTALL_GUIDE.md       ← Full installation walkthrough
5. QUICK_START_GUIDE.md        ← Run the demo
```

---

## Requirements

| Component | Version | Required |
|-----------|---------|----------|
| Windows | 10 or 11 | ✅ |
| NVIDIA GPU | 16+ GB VRAM | ✅ |
| Python | 3.10+ | ✅ |
| Node.js | 18+ | ✅ |
| Blender | 5.1 | ✅ |
| ComfyUI | 0.16+ | ✅ |
| Rhino | 8 | Optional |
| OBS Studio | Any | Optional |
| Claude Desktop | Latest | ✅ |

**GPU VRAM:** The Flux.2 Klein model requires ~16 GB at 1024×1024.

---

## Package Contents

```
AEC_Demo_Portable/
├── README.md                    ← This file
├── QUICK_START_GUIDE.md         ← Start here after install
├── prompts/
│   ├── comfyui/
│   │   └── generation_prompts.yaml  ← AI prompts (Make Real / Env / Time of Day) + alternates
│   ├── master_workflow/             ← 17 workflow phase prompts (site → final render)
│   │   ├── 01_user_prompt.md
│   │   ├── 02_demo_prompt.md
│   │   ├── ... (17 files)
│   │   └── aec_skills.md
│   └── project_template/
│       └── project_design_brief_template.md  ← Fill this in to start a new project
├── config/
│   └── user_config.yaml         ← ⚠️ EDIT THIS FIRST
├── setup/
│   ├── system_check.py          ← Verify installation
│   └── setup_windows.bat        ← First-time Windows setup
├── scripts/
│   ├── config_loader.py         ← Path/config utilities
│   ├── render_passes.py         ← Blender render pipeline
│   └── submit_comfyui.py        ← ComfyUI submission
├── blender/
│   └── auto_comfy.py            ← Blender startup script
├── comfyui/
│   ├── workflows/
│   │   ├── AEC_Transform_Pipeline.json       ← Load this ONCE in the ComfyUI
│   │   │                                        browser to seed history (UI format)
│   │   └── AEC_last_submitted_workflow.json  ← Verified full-link API-format
│   │                                            graph (136 nodes). submit_comfyui.py
│   │                                            falls back to this automatically if
│   │                                            there's no ComfyUI history yet.
│   ├── custom_nodes/
│   │   └── aec_utility_nodes/   ← Custom ComfyUI nodes
│   └── models/
│       └── MODEL_MANIFEST.md    ← Model download links (~23 GB)
├── claude/
│   └── claude_desktop_config_template.json
├── assets/
│   └── hdri/
│       └── qwantani_puresky_2k.hdr
├── sample_project/
│   ├── blender_assets/
│   │   ├── cliff_house_act2_textured_v3.blend ← Scene A (default) — SoCal coastal
│   │   │                                          cliff house, fully customized for
│   │   │                                          the live video demo (per-material
│   │   │                                          seg tags + hand-written prompts)
│   │   └── cliff_house_v17.blend               ← Scene B (alternative) — the earlier,
│   │                                              simpler house that was already
│   │                                              working before the customization
│   │                                              pass. Uses coarser wall/window/
│   │                                              roof/glass_railing tags.
│   ├── rhino_assets/            ← (optional — not included in this drop)
│   └── renders/                 ← Sample render outputs
└── docs/
    └── INSTALL_GUIDE.md         ← Full installation guide
```

---

## Two Sample Scenes — Which One to Open

This package ships **two versions of the same house**, both compatible with the
same `scripts/submit_comfyui.py` and the same bundled ComfyUI workflow — pick
whichever fits what you're doing:

| | `cliff_house_act2_textured_v3.blend` (Scene A, default) | `cliff_house_v17.blend` (Scene B, alternative) |
|---|---|---|
| **What it is** | The current, fully customized version used for the live video demo | The earlier version that was already working *before* that customization pass |
| **Materials** | 83 materials, fine-grained per-material seg tags (`travertine_white`, `wood_walnut`, `aluminum_dark`, ...) | 16 materials, coarser tags (`wall`, `window`, `roof`, `glass_railing`) |
| **Prompts** | Hand-written, scene-specific (Santa Barbara cliff, infinity pool, tinted glass, etc.) | Generic — pairs naturally with the workflow's built-in "Design Guidance" auto-prompt system prompt (currently unused by Scene A's script path, but still present in the graph) |
| **Use when** | You want the exact polished demo look | You want a simpler, faster starting point, or to verify the pipeline still works on a lighter scene before layering customization back on |

Both scenes' object tags are recognized by the same `SEG_COLORS` dict in
`submit_comfyui.py` (it keeps the coarse `wall`/`window`/`roof` tags specifically
for backward compatibility with scenes like this one), so no script changes are
needed to switch — just open the other `.blend` file in Step 1 of the Quick
Start and run through the same steps.

---

## Security Notes

- `config/user_config.yaml` contains your API key — **do not share or commit this file**
- All services run on localhost only — no external network exposure
- The `claude_desktop_config_template.json` contains no real credentials

---

## Download Links

| Software | URL |
|----------|-----|
| Blender 5.1 | https://www.blender.org/download/ |
| ComfyUI | https://github.com/comfyanonymous/ComfyUI/releases |
| Rhino 8 | https://www.rhino3d.com/download/ |
| Claude Desktop | https://claude.ai/download |
| OBS Studio | https://obsproject.com/download |
| Python 3.11 | https://www.python.org/downloads/ |
| Node.js 18 LTS | https://nodejs.org/en/download |
| NVIDIA CUDA 12 | https://developer.nvidia.com/cuda-downloads |

---

## License

Sample project files are for demonstration purposes only.
Flux.2 Klein and associated models are subject to their respective licenses.
