@echo off
REM AEC Demo Portable — Windows Environment Setup
REM Run this once as Administrator to configure your system.
REM Usage: Right-click → Run as Administrator

echo.
echo ============================================================
echo  AEC Demo Portable — Windows Environment Setup
echo ============================================================
echo.

REM ── Set ANTHROPIC_API_KEY ─────────────────────────────────────
echo Step 1: Setting ANTHROPIC_API_KEY
set /p APIKEY="  Enter your Anthropic API key (sk-ant-...): "
setx ANTHROPIC_API_KEY "%APIKEY%" /M
echo  Done.

REM ── Firewall rules ────────────────────────────────────────────
echo.
echo Step 2: Opening firewall ports (loopback only)

netsh advfirewall firewall add rule name="ComfyUI (AEC Demo)" ^
  dir=in action=allow protocol=TCP localport=8188 ^
  remoteip=127.0.0.1 description="ComfyUI local server"

netsh advfirewall firewall add rule name="BlenderMCP (AEC Demo)" ^
  dir=in action=allow protocol=TCP localport=9876 ^
  remoteip=127.0.0.1 description="Blender MCP server"

netsh advfirewall firewall add rule name="RhinoMCP (AEC Demo)" ^
  dir=in action=allow protocol=TCP localport=3001 ^
  remoteip=127.0.0.1 description="Rhino MCP server"

netsh advfirewall firewall add rule name="OBS WebSocket (AEC Demo)" ^
  dir=in action=allow protocol=TCP localport=4455 ^
  remoteip=127.0.0.1 description="OBS WebSocket server"

echo  Ports opened: 8188 (ComfyUI), 9876 (Blender), 3001 (Rhino), 4455 (OBS)

REM ── Install Python packages ───────────────────────────────────
echo.
echo Step 3: Installing required Python packages
pip install pyyaml requests Pillow numpy --quiet
echo  Python packages installed.

REM ── Install Node.js packages ──────────────────────────────────
echo.
echo Step 4: Caching npx packages (first-run only)
call npx --yes mcp-remote --help >nul 2>&1
echo  npx mcp-remote cached.

echo.
echo ============================================================
echo  Setup complete! Next steps:
echo  1. Edit config\user_config.yaml with your paths
echo  2. Run: python setup\system_check.py
echo  3. Follow docs\QUICK_START_GUIDE.md
echo ============================================================
echo.
pause
