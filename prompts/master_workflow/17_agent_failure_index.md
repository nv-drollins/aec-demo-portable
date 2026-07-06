# Agent Reference — Failure Mode Index
### For Claude / AI agent use. Human users: see docs/03_faq.md
*Version 1.0 — May 2026*

---

## Silent Failures (no error shown)

| Symptom | Cause | Fix |
|---|---|---|
| rotation_euler has no effect | rotation_mode = QUATERNION | Set rotation_mode = 'XYZ' first |
| All keyframes same position | scene.frame_set() in loop | Remove frame_set(); use keyframe_insert(frame=N) |
| OBS captures wrong window | Lost window handle after restart | obs-get-source-screenshot to verify each source |
| Material not applied | Object name doesn't match keyword | Check name.lower() matches assignment condition |

## Visual Failures (wrong output)

| Symptom | Cause | Fix |
|---|---|---|
| Depth maps flat mid-grey | Range too wide | Per-frame auto-normalise from actual min/max |
| Depth maps upside-down | Applied np.flipud() | Remove flipud — EXR already top-down |
| Depth maps have shadows | Used Workbench depth mode | Use View Distance emission + zero bounces |
| Segmentation has gradients | Not all bounces zeroed | max/diffuse/glossy/transmission/volume all = 0 |
| Pad floats above terrain | Bottom Z too shallow | Sample terrain, set bottom 50mm below minimum |
| Curtain wall gap at terrain | Used BooleanDifference | Use Rhino Trim with terrain as cutter |
| Patio side faceted | Smooth bleeds to top face | bmesh sharp ring edges + Edge Split modifier |
| Chair faces outward | Wrong rotation formula | Use theta + pi/2 + pi, verify +Y world direction |
| Roof has joints | Modelled as multiple pieces | Rebuild as single solid object |

## API Failures (error thrown)

| Error | Cause | Fix |
|---|---|---|
| PIL mode I;16 deprecated | Pillow 13+ | fromarray(arr.astype(np.int32), mode='I') |
| OPEN_EXR_MULTILAYER not found | Not in render output formats | Use compositor File Output node |
| Action has no fcurves | Blender 5.x layered actions | Access via action.layers[].strips[].channelbag() |
| scene has no node_tree | Blender 5.x compositor | Use scene.compositing_node_group |
| Transmission not found | Blender 5.x input name change | Check b.inputs list for current name |

## Recovery Procedures

**Camera not animating:**
1. Call scene.frame_set(0) → read location
2. Call scene.frame_set(192) → read location
3. If same: loop had frame_set() bug — clear animation, re-run without it

**Blender MCP not connecting:**
1. Blender Scripting tab → run bpy.ops.blendermcp.start_server()
2. Check port 9876 in BlenderMCP panel
3. Verify 'blender' (lowercase) in claude_desktop_config.json mcpServers
4. If Windows: confirm Hyper-V enabled

**Depth maps zero differentiation:**
1. Check one raw EXR pixel range — if all values within 5% of each other: range issue
2. Switch to per-frame min/max normalisation
3. Confirm film_transparent=True (otherwise background pixels have ~200m Z value and dominate the range)
