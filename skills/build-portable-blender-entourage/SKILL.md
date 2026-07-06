---
name: build-portable-blender-entourage
description: "Build canonical Phase 6 outdoor-living entourage in Blender from a checked deterministic layout after validating the Phase 5 landscaping checkpoint. Use only for Phase 6 in AEC_Demo_Portable."
---

# Build the delivered portable entourage checkpoint

This is the only supported canonical Phase 6 procedure. The delivered scene
contains no named furniture, planter, firepit, or vehicle meshes, so this skill
uses a versioned procedural layout matching the upstream entourage prompt. It
saves a new checkpoint and does not overwrite Phase 5 or assign Phase 7 final
materials.

## Read-only readiness check

Before approval, run only:

```bash
python3 scripts/check-portable-entourage-ready.py
```

Require `PORTABLE_ENTOURAGE_READY_OK`, report the exact item-role counts, and
stop with `WAITING_FOR_HUMAN_APPROVAL phase=6 name=entourage_outdoor_living`.
Do not use raw MCP code, generated shell snippets, or direct scene edits.

## Authorization and procedure

- Require a new human approval for canonical Phase 6 under `AGENTS.md`.
- Consume the approval when the runner begins.
- From `ROOT=/home/nvidia/AEC_Demo_Portable`, run exactly:

  ```bash
  python3 scripts/run-portable-entourage.py
  ```

- Require these ordered markers:

  ```text
  PORTABLE_ENTOURAGE_INPUT_OK
  PORTABLE_ENTOURAGE_BUILD_OK
  PORTABLE_ENTOURAGE_LAYOUT_OK
  PORTABLE_ENTOURAGE_PREPARATION_OK
  ```

- Verify ten procedural objects: two pool loungers, one side table, one firepit,
  one dining table, two dining chairs, two planters, and one vehicle.
- Show the Blender material-preview site view and stop with
  `PHASE_REVIEW_REQUIRED phase=6 name=entourage_outdoor_living`.

## Prohibited actions

- Do not overwrite the delivered target or Phase 5 checkpoint.
- Do not download external assets or create people.
- Do not change the established building, site, camera, or lighting.
- Do not perform Phase 7 final material assignment or submit to ComfyUI.
- Do not proceed to Phase 7.
