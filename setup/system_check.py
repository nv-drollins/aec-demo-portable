#!/usr/bin/env python3
"""
AEC Demo Portable — System Check
Run this FIRST before attempting the demo.
Usage: python setup/system_check.py
"""

import sys, os, subprocess, importlib, json, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config" / "user_config.yaml"

PASS  = "\033[92m[PASS]\033[0m"
FAIL  = "\033[91m[FAIL]\033[0m"
WARN  = "\033[93m[WARN]\033[0m"
INFO  = "\033[94m[INFO]\033[0m"

results = {"passed": 0, "failed": 0, "warnings": 0}

def ok(msg):
    print(f"  {PASS} {msg}")
    results["passed"] += 1

def fail(msg, fix=""):
    print(f"  {FAIL} {msg}")
    if fix: print(f"         FIX: {fix}")
    results["failed"] += 1

def warn(msg, fix=""):
    print(f"  {WARN} {msg}")
    if fix: print(f"         TIP: {fix}")
    results["warnings"] += 1

def info(msg):
    print(f"  {INFO} {msg}")

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ── Load config ────────────────────────────────────────────────
try:
    import yaml
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    ok(f"Config loaded: {CONFIG_PATH}")
except ImportError:
    fail("PyYAML not installed", "pip install pyyaml")
    cfg = {}
except FileNotFoundError:
    fail(f"user_config.yaml not found at {CONFIG_PATH}",
         "Copy config/user_config.example.yaml to config/user_config.yaml and fill in the local copy")
    cfg = {}

# ── 1. Python ──────────────────────────────────────────────────
section("1. Python Environment")
pv = sys.version_info
if pv >= (3, 10):
    ok(f"Python {pv.major}.{pv.minor}.{pv.micro}")
else:
    fail(f"Python {pv.major}.{pv.minor} — need 3.10+",
         "https://python.org/downloads")

for pkg in ["yaml", "requests", "PIL", "numpy"]:
    try:
        importlib.import_module(pkg if pkg != "PIL" else "PIL.Image")
        ok(f"Package: {pkg}")
    except ImportError:
        real = {"yaml":"pyyaml","PIL":"Pillow"}.get(pkg, pkg)
        fail(f"Package missing: {pkg}", f"pip install {real}")

# ── 2. Node.js ─────────────────────────────────────────────────
section("2. Node.js (required for MCP servers)")
try:
    r = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
    ver = r.stdout.strip()
    major = int(ver.lstrip("v").split(".")[0])
    if major >= 18:
        ok(f"Node.js {ver}")
    else:
        fail(f"Node.js {ver} — need v18+", "https://nodejs.org/en/download")
except:
    fail("Node.js not found", "https://nodejs.org/en/download")

try:
    r = subprocess.run(["npx", "--version"], capture_output=True, text=True, timeout=5)
    ok(f"npx {r.stdout.strip()}")
except:
    fail("npx not found", "Installed with Node.js — check PATH")

# ── 3. Blender ─────────────────────────────────────────────────
section("3. Blender")
blender_exe = cfg.get("blender", {}).get("exe", "")
if blender_exe and Path(blender_exe).exists():
    ok(f"Blender found: {blender_exe}")
else:
    fail(f"Blender not found at: {blender_exe}",
         "Download: https://www.blender.org/download/ — set path in user_config.yaml")

mcp_port = cfg.get("blender", {}).get("mcp_port", 9876)
try:
    import socket
    with socket.create_connection(("127.0.0.1", mcp_port), timeout=2):
        ok(f"BlenderMCP running on port {mcp_port}")
except:
    warn(f"BlenderMCP not running on port {mcp_port}",
         "Open Blender and enable the BlenderMCP addon (N panel → MCP → Start Server)")

# ── 4. ComfyUI ─────────────────────────────────────────────────
section("4. ComfyUI")
comfy_path = cfg.get("comfyui", {}).get("install_path", "")
comfy_url  = cfg.get("comfyui", {}).get("url", "http://127.0.0.1:8188")

if comfy_path and Path(comfy_path).exists():
    ok(f"ComfyUI install found: {comfy_path}")
    python_exe = Path(comfy_path) / cfg.get("comfyui",{}).get("python_exe","python_embeded/python.exe")
    if python_exe.exists():
        ok(f"ComfyUI Python: {python_exe}")
    else:
        fail(f"ComfyUI Python not found at {python_exe}")
else:
    fail(f"ComfyUI not found at: {comfy_path}",
         "Download: https://github.com/comfyanonymous/ComfyUI — set path in user_config.yaml")

try:
    with urllib.request.urlopen(f"{comfy_url}/system_stats", timeout=3) as r:
        ok(f"ComfyUI server running at {comfy_url}")
except:
    warn(f"ComfyUI not running at {comfy_url}",
         "Start ComfyUI — see docs/COMFYUI_SETUP.md for startup command")

# Check required models
section("4b. ComfyUI Models")
REQUIRED_MODELS = {
    "diffusion_models/klein/flux-2-klein-4b.safetensors": {
        "size_gb": 7.22,
        "source": "https://huggingface.co/ostris/ai-toolkit — search 'flux2-klein'"
    },
    "text_encoders/klein/qwen_3_4b.safetensors": {
        "size_gb": 7.49,
        "source": "https://huggingface.co/Qwen/Qwen3-4B — GGUF/safetensors"
    },
    "vae/flux2-vae.safetensors": {
        "size_gb": 0.31,
        "source": "https://huggingface.co/black-forest-labs/FLUX.1-dev — vae folder"
    },
}
if comfy_path:
    models_root = Path(comfy_path) / "ComfyUI" / "models"
    for rel_path, meta in REQUIRED_MODELS.items():
        full = models_root / rel_path
        if full.exists():
            size_gb = full.stat().st_size / 1e9
            ok(f"Model found ({size_gb:.1f} GB): {rel_path}")
        else:
            fail(f"Model missing: {rel_path}", f"Download from: {meta['source']}")

# Check custom nodes
section("4c. ComfyUI Custom Nodes")
REQUIRED_NODES = [
    ("aec_utility_nodes",          "Bundled in this package — copy to custom_nodes/"),
    ("ComfyUI-Easy-Use",           "https://github.com/yolain/ComfyUI-Easy-Use"),
    ("ComfyUI-Impact-Pack",        "https://github.com/ltdrdata/ComfyUI-Impact-Pack"),
    ("was-node-suite-comfyui",     "https://github.com/WASasquatch/was-node-suite-comfyui"),
    ("ComfyUI-Custom-Scripts",     "https://github.com/pythongosssss/ComfyUI-Custom-Scripts"),
    ("ComfyUI-Inpaint-CropAndStitch", "https://github.com/lquesada/ComfyUI-Inpaint-CropAndStitch"),
]
if comfy_path:
    nodes_root = Path(comfy_path) / "ComfyUI" / "custom_nodes"
    for node_name, source in REQUIRED_NODES:
        if (nodes_root / node_name).exists():
            ok(f"Custom node: {node_name}")
        else:
            fail(f"Missing node: {node_name}", source)

# ── 5. Rhino ───────────────────────────────────────────────────
section("5. Rhino 8")
rhino_exe = cfg.get("rhino", {}).get("exe", "")
if rhino_exe and Path(rhino_exe).exists():
    ok(f"Rhino found: {rhino_exe}")
else:
    warn(f"Rhino not found at: {rhino_exe}",
         "Download: https://www.rhino3d.com/download/ (license required) — set path in user_config.yaml")

rhino_port = cfg.get("rhino", {}).get("mcp_port", 3001)
try:
    import socket
    with socket.create_connection(("127.0.0.1", rhino_port), timeout=2):
        ok(f"RhinoMCP running on port {rhino_port}")
except:
    warn(f"RhinoMCP not running on port {rhino_port}",
         "Open Rhino and run: mcp_server_start (see docs/RHINO_SETUP.md)")

# ── 6. Claude Desktop ──────────────────────────────────────────
section("6. Claude Desktop & MCP")
claude_config_paths = [
    Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
    Path("/Users") / os.environ.get("USER","") / "Library/Application Support/Claude/claude_desktop_config.json",
]
found_claude_config = False
for p in claude_config_paths:
    if p.exists():
        ok(f"Claude Desktop config found: {p}")
        try:
            with open(p) as f:
                config = json.load(f)
            servers = list(config.get("mcpServers", {}).keys())
            if servers:
                ok(f"MCP servers configured: {', '.join(servers)}")
            else:
                warn("No MCP servers configured in Claude Desktop",
                     "See claude/claude_desktop_config_template.json in this package")
        except Exception as e:
            warn(f"Could not parse Claude config: {e}")
        found_claude_config = True
        break
if not found_claude_config:
    fail("Claude Desktop config not found",
         "Install Claude Desktop from https://claude.ai/download")

api_key = cfg.get("anthropic", {}).get("api_key", "")
if api_key and not api_key.startswith("sk-ant-REPLACE"):
    ok("Anthropic API key configured")
else:
    fail("Anthropic API key not set",
         "Add your key to config/user_config.yaml — get one at https://console.anthropic.com")

# ── 7. Environment Variables ───────────────────────────────────
section("7. Environment Variables")
if os.environ.get("ANTHROPIC_API_KEY"):
    ok("ANTHROPIC_API_KEY environment variable set")
else:
    warn("ANTHROPIC_API_KEY not set as env var",
         "Run: setx ANTHROPIC_API_KEY \"sk-ant-...\" (Windows) or add to ~/.bashrc")

# ── Summary ────────────────────────────────────────────────────
section("SUMMARY")
total = results["passed"] + results["failed"] + results["warnings"]
print(f"  Total checks:  {total}")
print(f"  Passed:        {results['passed']}")
print(f"  Warnings:      {results['warnings']}")
print(f"  Failed:        {results['failed']}")
print()
if results["failed"] == 0:
    print("  ✅ System ready! Proceed to QUICK_START_GUIDE.md")
elif results["failed"] <= 3:
    print("  ⚠️  Fix the FAIL items above, then re-run this check.")
else:
    print("  ❌ Multiple issues found. Work through docs/INSTALL_GUIDE.md first.")
print()
