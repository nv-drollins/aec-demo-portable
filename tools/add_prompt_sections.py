
inv = r"C:\Users\swags\Documents\AEC_Demo_Portable\docs\PROMPT_INVENTORY.md"

system_section = r"""

---

## Category 5 — System Prompts

System prompts govern how Claude **initiates and manages sessions**. They are
not phase-specific — they are always active, loaded before any phase prompt.
All files live in `prompts/system_prompts/`.

---

### `prompts/system_prompts/00_session_startup.md`
**Read by:** Claude — at the very start of every session  
**What it does:**  
Defines the two session scenarios (New Project and Resume Project) and how Claude
handles each. For a new project: asks one question to understand what is being
built, interviews the user to fill in the design brief template, then initiates
Phase 0. For a resume: reads session_state.md, confirms current phase with the
user, and continues. Also covers mid-session interruption handling and how to
recover from a crash.

---

### `prompts/system_prompts/00b_rhino_scene_protocol.md`
**Read by:** Claude — whenever working in Rhino  
**What it does:**  
The rules for how Claude interacts with the Rhino scene via MCP: when to read
vs write, how to validate before any destructive operation, the required snapshot
protocol (always snapshot before major changes), the layer naming contract, and
the rules for what Claude is and is not allowed to delete. Claude reads this before
any Rhino operation to avoid accidental data loss.

---

### `prompts/system_prompts/00c_references_protocol.md`
**Read by:** Claude — when interpreting reference images or adding new references  
**What it does:**  
Defines how reference images are processed: how to extract design intent from
image content, how to tag and file references into the project structure, how to
write a reference summary, and when reference images override the design brief vs
when the brief takes precedence. Covers both local files and URL references.

---

## Category 6 — Rhino-Specific Claude Skills

These skills are installed in a **separate folder** from the main skills —
they are Rhino-workflow-specific and are loaded by Claude when working
in Rhino, distinct from the Blender-side skills.

**Installation path:** `skills/rhino/` in this package  
**On the original system:** `C:\Users\username\Documents\claude_rhino_skills\`  
**Claude Desktop config note:** The Rhino skills path must be registered in
Claude Desktop's project settings so Claude knows to read them.

---

### `skills/rhino/INDEX.md`
**Read by:** Claude — at the start of any Rhino-specific session  
**What it does:**  
The entry point for the Rhino skills library. Lists all available Rhino skills,
when each one applies, and the operating rules for Rhino-specific work. Distinct
from the main `skills/INDEX.md` — this one focuses specifically on Rhino
construction patterns. Claude reads this whenever the session involves significant
Rhino modeling work.

---

### `skills/rhino/slope_curve_network.md`
**Read by:** Claude — when building or modifying terrain in Rhino  
**What it does:**  
The complete technique for constructing sloped terrain from a curve network in
Rhino. Defines the u-curve / v-curve approach: u-curves define the slope profiles
(typically 3, running north-south), v-curves define the cross sections (typically
2, running east-west). Covers how to loft through the network, how to handle the
edges near the building pad, and how to validate the resulting surface. This is the
authoritative method for all terrain construction in the demo.

---

### `skills/rhino/patio_retaining_wall.md`
**Read by:** Claude — when building or modifying patio elements or retaining walls  
**What it does:**  
The technique for constructing the patio retaining wall as a smooth lofted solid
that follows the patio curve. Defines the wall profile (top always at least 0.5m
above patio surface), the construction sequence (extract terrain profile → offset →
loft → cap), and the validation checks (must be solid, no self-intersections, top
edge continuous). Also covers stair integration: first step top = pad top Z, last
step top = patio surface + one riser.

"""

with open(inv, "a", encoding="utf-8") as f:
    f.write(system_section)

print("System prompts + Rhino skills sections appended to PROMPT_INVENTORY.md")
