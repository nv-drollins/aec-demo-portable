# Skill: Slope Modeling with NetworkSrf

**Command:** `NetworkSrf`  
**Use when:** Modeling terrain, slopes, or any compound-curvature surface that follows a U/V grid of guide curves — analogous to topo lines on a map.

---

## ⚠️ CRITICAL RULE — Tolerance = Resolution

**The single most important thing to get right.**

The tolerance values in the NetworkSrf dialog directly control surface resolution. **Small tolerance = high resolution = smooth rendering.** Large tolerance = coarse, blocky, jaggy surface that cannot hold material or lighting detail in Blender or any renderer.

| Tolerance Setting | Result |
|---|---|
| `1` or `-1` (Rhino default) | Very low resolution — NEVER USE for terrain |
| `0.1` | Still too coarse for architectural site work |
| `0.01` | Marginal — acceptable only for very flat, simple slopes |
| `0.001` | ✅ Good starting point for architectural terrain in meters |
| `0.0001` | Higher precision — use for steep or highly detailed slopes |

**Always set both Edge curves and Interior curves to `0.001` or smaller.**  
The Rhino default is system tolerance × 10, which in a meters-based document is far too coarse.

---

## Layer Setup

Organize curves into two layers before running the command:

- **uCurves** — curves running in one direction (e.g. east–west)  
- **vCurves** — curves running perpendicular (e.g. north–south)

This is not strictly required by Rhino, but makes selection reliable and the model auditable.

---

## Curve Requirements — Non-negotiable

NetworkSrf is very sensitive to curve quality. If any of these fail, the result will be unpredictable or Rhino will reject the input:

1. **All curves in one direction must cross all curves in the other direction** — no exceptions
2. **Curves cannot cross each other within the same direction** (no U-curve crossing another U-curve)
3. **Endpoint joins must be clean** — use `End` osnap; verify with `SelOpenCrv` after joining. A gap of even 0.001m can cause a bad surface.
4. **No stacked or duplicate curves** — run `SelDupAll` before starting
5. **Curve direction consistency** — run `Dir` to verify all U curves point the same way and all V curves point the same way. Use `Flip` to correct.

**Recommended curve preparation workflow:**
```
InterpCrv        → draw curves through elevation points
Rebuild          → even out parameterization (reduce wiggly spans)
Dir              → unify direction per axis
Intersect        → verify all crossings exist
Join / End osnap → ensure clean endpoint connections
```

---

## Running NetworkSrf — Step by Step

1. Select all curves (or use window selection if layers are isolated)
2. Type `NetworkSrf` → press Enter
3. Rhino may prompt: *"Select curves in first direction"* — select all U curves, Enter; then all V curves, Enter. Or use `NoAutoSort` if the auto-sort produces wrong results.
4. The **Surface From Curve Network** dialog appears

### Dialog Settings

```
Tolerances
  Edge curves:     0.001      ← SET THIS. Never leave at default.
  Interior curves: 0.001      ← SET THIS. Never leave at default.
  Angle:           1          ← leave at default unless matching adjacent surfaces

Edge matching (A / B / C / D corners)
  Position: ● (selected for all four)   ← standard for terrain
  Tangency: ○
  Curvature: ○
```

5. Click **OK**
6. Inspect result — zoom in and check for:
   - Smooth surface flow (no creases unless intended)
   - Edge alignment with input boundary curves
   - No self-intersections

---

## Quality Check After Creation

```
ZebraAnalysis      → look for sharp bands = kink in surface
CurvatureAnalysis  → look for spikes = overfitting or bad input curve
ShowEdges          → check for naked edges if surface will join others
```

If the surface looks blocky or faceted **in Rhino shaded view**, the tolerance is still too coarse — delete and redo with smaller values.

---

## ⚠️ CRITICAL — Render Mesh Settings for Blender Export

NURBS surfaces in Rhino have two separate representations:
1. The **NURBS surface** — mathematically precise, controlled by NetworkSrf tolerances
2. The **render mesh** — a polygon mesh auto-generated from the NURBS, used for rendering and export

**Both must be high resolution.** A perfect NURBS surface with a coarse render mesh will still look blocky in Blender.

### How to Access Per-Object Render Mesh Settings

```
Select the surface
→ Properties panel (right side)
→ Render Mesh Settings section
→ Check "Custom Mesh" checkbox
→ Click "Adjust" button
→ Click "Detailed Controls" in the dialog
```

### What You Can Control

The Detailed Mesh Options dialog exposes these parameters — adjust as needed based on the visual result:

- **Density** — overall mesh density slider
- **Maximum angle** — lower values = smoother curves. Default (20°) is too coarse for terrain; reduce if the mesh looks faceted
- **Maximum aspect ratio** — controls triangle shape; 0 = disabled
- **Minimum / Maximum edge length** — clamps polygon size; useful for very large or very small surfaces
- **Maximum edge to surface distance** — how closely the mesh hugs the NURBS surface; lower = tighter fit
- **Minimum initial grid quads** — baseline subdivision before refinement
- **Refine mesh** ✅ — should be ON; allows Rhino to add polygons where curvature demands it
- **Jagged seams** — leave OFF for watertight meshes
- **Pack textures** — leave ON for UV integrity on export

**The key principle:** if the exported mesh looks blocky or faceted in Blender, come back here and tighten the relevant parameters. Use the **Preview** button to evaluate before committing. There is no single correct value — adjust until the visual result is acceptable.

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| NetworkSrf tolerance at default (`-1` or `1`) | Blocky surface even in Rhino shaded view | Redo NetworkSrf with `0.001` |
| Render mesh left at Rhino defaults | Smooth NURBS looks faceted in Blender | Access Custom Mesh settings, reduce Maximum angle |
| Curves don't cross cleanly | Rhino error or twisted surface | Use `Intersect` to verify, fix gaps |
| Mixed curve directions | Wavy, unpredictable surface | Run `Dir`, unify with `Flip` |
| Too many interior curves | Surface overfits, heavy file | Remove redundant curves, keep a clean grid |
| Fixed NURBS but not render mesh | Still looks bad after export | They are independent — both must be addressed |

---

## Reference Images

- `img/slope_curve_network/networksrf_dialog.png` — NetworkSrf dialog with correct tolerance values
- `img/slope_curve_network/render_mesh_dialog.png` — Detailed Mesh Options dialog
- `img/slope_curve_network/result_bad.png` — rendered output with coarse settings (jaggy terrain)
- `img/slope_curve_network/result_good.png` — rendered output with fine settings (smooth terrain)
