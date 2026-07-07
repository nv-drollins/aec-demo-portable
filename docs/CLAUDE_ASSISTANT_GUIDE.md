# Claude Assistant — Blender Addon
# aec_demo_master / claude_config
# Last updated: May 2026

> **HISTORICAL UPSTREAM REFERENCE — not part of the DGX Spark installation.**
> This document describes the delivered Windows/Claude Blender addon. The
> supported Spark port uses Hermes, checked Blender adapters, and
> `scripts/submit_comfyui.py`. Start with
> [INSTALL_GUIDE.md](INSTALL_GUIDE.md).

## WHAT IT DOES

Adds a "Claude" tab to the Blender Text Editor sidebar. Type instructions or
questions in a text block, click "Ask Claude", and get a response directly
inside Blender. If Claude's response contains Python code, you can execute it
with one click (or automatically).

This lets you drive Blender scene changes by typing plain English in the
Text Editor — no need to switch to the chat window for routine tasks.

---

## FILES

  Addon (source of truth / backup):
    C:\Users\swags\Documents\aec_demo_master\claude_config\claude_assistant.py

  Addon (live install location):
    C:\Users\swags\AppData\Roaming\Blender Foundation\Blender\5.1\scripts\addons\claude_assistant.py

  Both files must be identical. After any edits, copy from config → addons.

---

## INSTALL / REINSTALL

### Step 1 — Copy addon file
Copy claude_assistant.py from this folder to:
  C:\Users\swags\AppData\Roaming\Blender Foundation\Blender\5.1\scripts\addons\

### Step 2 — Enable in Blender
Option A (GUI):
  Edit → Preferences → Add-ons → search "Claude Assistant" → enable checkbox

Option B (Scripting tab — faster after a crash):
  import bpy
  bpy.ops.preferences.addon_enable(module='claude_assistant')

### Step 3 — Set API key
Option A (GUI):
  Edit → Preferences → Add-ons → Claude Assistant → paste Anthropic API key

Option B (environment variable — no GUI needed):
  Set ANTHROPIC_API_KEY in Windows environment variables.
  The addon reads it automatically if the prefs field is empty.

Option C (Scripting tab):
  addon = bpy.context.preferences.addons['claude_assistant']
  addon.preferences.api_key = "sk-ant-..."

### Step 4 — Verify
Open Text Editor → press N (sidebar) → look for "Claude" tab.
If the tab is missing, the addon isn't enabled.

---

## DAILY USE

1. Open Text Editor area in Blender
2. Create or select a text block (click "New" in the header)
3. Type your instruction, e.g.:
     "Move the patio 2m north and rotate it 45 degrees"
     "Make the roof material dark grey metallic"
     "What is the current location of PATIO_GROUP?"
4. Press N to open sidebar → click "Claude" tab
5. Click the big "Ask Claude" button
6. Wait a few seconds — response appears in a new "Claude Response" text block
   and the editor switches to show it automatically
7. If there are code blocks:
   - Click "Execute Code" to run them, OR
   - Enable "Auto-Execute" in preferences to run them automatically

---

## PANEL CONTROLS

  Ask Claude        Big green button. Sends active text block to Claude.
                    Greys out with "Thinking…" while waiting.

  Execute Code      Appears when Claude's response contains Python blocks.
                    Click to run all code blocks in sequence.

  History: N turn(s)  Shows how many exchanges are in the current session.
                       Claude remembers context across turns.

  🗑 (trash icon)   Clears conversation history. Use this when starting a
                    new topic or if Claude seems confused by prior context.

---

## PREFERENCES (Edit → Preferences → Add-ons → Claude Assistant)

  API Key           Your Anthropic API key (stored locally, not synced).
                    Falls back to ANTHROPIC_API_KEY environment variable.

  Auto-Execute      If ON, Python code blocks in Claude's response run
                    immediately without clicking "Execute Code".
                    Leave OFF until you trust what Claude is generating.

  Fresh conversation each run
                    If ON, history is cleared before every Ask.
                    Good for unrelated one-off queries.

---

## HOW IT WORKS INTERNALLY

1. "Ask Claude" reads the active text block contents
2. Builds a system prompt with the current scene state (all visible objects,
   their locations, scales, and materials — up to 40 objects)
3. Appends the message to the conversation history
4. Calls https://api.anthropic.com/v1/messages in a background thread
   (so Blender's UI doesn't freeze)
5. A timer polls every 0.4s until the response arrives
6. Response is written to "Claude Response" text block
7. The Text Editor switches to show it
8. Any ```python ... ``` fences are extracted as executable code blocks

Model: claude-sonnet-4-20250514
Max tokens: 4096
Timeout: 90 seconds

---

## TROUBLESHOOTING

### "Claude" tab not visible in sidebar
  → Addon not enabled. Run: bpy.ops.preferences.addon_enable(module='claude_assistant')
  → Or check Edit → Preferences → Add-ons

### "No API key" error
  → Set key in preferences or ANTHROPIC_API_KEY environment variable

### "Text block is empty" error
  → Make sure the active text block in the Text Editor has content
  → The dropdown in the Text Editor header shows which block is active

### Response never appears / "Thinking…" forever
  → Network issue or API timeout (90s limit)
  → Check Windows firewall isn't blocking Python outbound connections
  → Try a simpler query to verify connectivity

### Code block executes but errors in Blender
  → Check the Blender System Console (Window → Toggle System Console)
    for the full Python traceback
  → The error is also shown in the Blender status bar

### Addon causes Blender crash on enable
  → Syntax error in addon file. Open claude_assistant.py in a text editor
    and check for issues, or re-copy from this config directory.

### After Blender crash — reinstall steps
  1. Open Blender, open Scripting tab
  2. Run: bpy.ops.preferences.addon_enable(module='claude_assistant')
  3. If that fails, re-copy the .py file from this directory first
  4. Set API key if preferences were reset

---

## KNOWN LIMITATIONS

- Scene context is capped at 40 objects. Scenes with more objects will
  have some omitted from the context sent to Claude.
- Claude in the addon doesn't share conversation history with the main
  Claude chat window (claude.ai). They are separate sessions.
- The addon does not stream responses — you wait for the full reply.
- Auto-Execute runs code with full bpy access. Only enable it if you
  trust the source of instructions.

---

## WRITING GOOD INSTRUCTIONS

The addon sends your full text block as the user message. Claude already knows
the scene context (objects, locations, materials), so you don't need to repeat
it. Just be direct:

  GOOD: "Move PATIO_GROUP 3m east and level its top with building_pad"
  GOOD: "Make the roof slab material glossy dark grey"
  GOOD: "What material is on the curtain wall right now?"
  GOOD: "Scale fire_core XY by 1.25 and set its Z scale to 0.5"

  LESS GOOD: "Can you please move the patio thing over to the right side a bit"
  LESS GOOD: Vague references — use the exact object name from the outliner

Multi-step instructions work fine in one block:
  "Move patio 2m north. Rotate it 30 degrees around Z. Apply M_Patio_Stone
   to the building_pad. Then tell me the new world location of PATIO_GROUP."

For follow-up, just type a new message — Claude remembers prior turns in the
session (shown as "History: N turn(s)"). Click trash to start fresh.

---

## SYSTEM PROMPT (what Claude sees in every request)

Every request is prefixed with this context block, built dynamically:

  - Project name and .blend file path
  - Render engine and current frame number
  - All visible scene objects with:
      name, type, world location (x,y,z), scale (x,y,z), material names
  - Rules: return Python in ```python fences, be concise, don't ask
    unnecessary questions

Context is rebuilt fresh on every request — always reflects latest scene state.

---

## KNOWN LIMITATIONS

- Scene context is capped at 40 objects. Scenes with more objects will
  have some omitted from the context sent to Claude.
- Claude in the addon does not share conversation history with claude.ai.
  They are completely separate sessions.
- The addon does not stream responses — you wait for the full reply.
- Auto-Execute runs code with full bpy access. Only enable it once you
  trust what Claude is generating.
- API key is stored in Blender preferences which may reset on crash.
  Use the ANTHROPIC_API_KEY environment variable for persistence.

---
