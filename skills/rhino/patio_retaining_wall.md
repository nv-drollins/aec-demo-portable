# Skill: Patio / Platform Retaining Wall on Sloped Terrain
*Location: C:\Users\swags\Documents\claude_rhino_skills\patio_retaining_wall.md*
*Applies to: any raised or sunken platform on a sloping site*

---

## The Problem

A patio or platform at a fixed Z level on sloping terrain will be partly above grade (downhill side, sticking out of the hill) and partly below grade (uphill side, buried in the hill). A single uniform retaining wall treatment is wrong for both cases. Each side requires a different wall strategy.

---

## The Rule

**Where the platform is ABOVE terrain (downhill side):**
The retaining wall drops DOWN from the platform perimeter edge to the ground.
- Wall top = platform Z
- Wall bottom = terrain Z at each point

**Where the platform is BELOW terrain (uphill side):**
The retaining wall rises UP from the platform perimeter edge to the ground.
- Wall bottom = platform Z
- Wall top = terrain Z at each point

---

## Algorithm

### Step 1 — Find the two intersection points

The platform perimeter curve is at a fixed Z (patioZ). The terrain surface is variable. There are exactly two points along the perimeter where terrain Z = patioZ. These split the perimeter into two arcs: above-terrain and below-terrain.

```csharp
// Project patio_plan to XY for sampling
var flatCurve = Curve.ProjectToPlane(patioPlan, Plane.WorldXY);

// Sample N points along the curve
int N = 300;
double[] zTerrain = new double[N];
double[] tParams  = new double[N];
for (int i = 0; i < N; i++) {
    double t = flatCurve.Domain.ParameterAt(i / (double)(N-1));
    var pt = flatCurve.PointAt(t);
    zTerrain[i] = SampleTerrainZ(terrainBrep, pt.X, pt.Y);
    tParams[i] = t;
}

// Find crossings: where (zTerrain[i] - patioZ) changes sign
var crossings = new List<double>();
for (int i = 0; i < N-1; i++) {
    double a = zTerrain[i] - patioZ;
    double b = zTerrain[i+1] - patioZ;
    if (a * b < 0) {
        // Linear interpolate for exact parameter
        double frac = Math.Abs(a) / (Math.Abs(a) + Math.Abs(b));
        crossings.Add(tParams[i] + frac * (tParams[i+1] - tParams[i]));
    }
}
// crossings should contain exactly 2 values
```

### Step 2 — Split the curve at intersection points

```csharp
var segments = patioPlan.Split(crossings.ToArray());
// Returns 2 curves: one above terrain, one below
```

Classify each segment by sampling a midpoint:
- If terrainZ at midpoint < patioZ → segment is ABOVE terrain (downhill)
- If terrainZ at midpoint > patioZ → segment is BELOW terrain (uphill)

### Step 3 — Offset each segment outward

```csharp
// Positive or negative offset — pick the one with larger BB (outward)
var off1 = seg.Offset(Plane.WorldXY, +wallThickness, tol, CurveOffsetCornerStyle.Round);
var off2 = seg.Offset(Plane.WorldXY, -wallThickness, tol, CurveOffsetCornerStyle.Round);
var outerSeg = (off1[0].GetBoundingBox(false).Diagonal.Length > 
               off2[0].GetBoundingBox(false).GetBoundingBox(false).Diagonal.Length)
               ? off1[0] : off2[0];
```

### Step 4 — Extrude each offset segment into a tall slab

```csharp
double extrBottom = patioZ - 5.0;   // well below terrain
double extrTop    = patioZ + 5.0;   // well above terrain

// Move outer curve to extrBottom
var outerAtBot = outerSeg.DuplicateCurve();
outerAtBot.Transform(Transform.Translation(0, 0, extrBottom - outerSeg.PointAtStart.Z));

// Extrude upward
double extrHeight = extrTop - extrBottom;
var wallSlab = Extrusion.Create(outerAtBot, extrHeight, false).ToBrep();
```

### Step 5 — Trim the slab by terrain

```csharp
// Use terrain as splitting Brep
var pieces = wallSlab.Split(new[] { terrainBrep }, tol);

// For DOWNHILL segment: keep piece whose center is BETWEEN terrain and patioZ
// For UPHILL segment:   keep piece whose center is BETWEEN patioZ and terrain
foreach (var piece in pieces) {
    double cZ = piece.GetBoundingBox(false).Center.Z;
    bool keep = isDownhill ? (cZ > terrainZAtCenter && cZ < patioZ)
                           : (cZ > patioZ && cZ < terrainZAtCenter);
    if (keep) rdoc.Objects.AddBrep(piece, attr);
}
```

### Step 6 — Trim terrain by patio footprint

Project patio_plan onto terrain surface and use as split curve:
```csharp
var projected = Curve.ProjectToBrep(patioPlan_lifted, terrainBrep, -Vector3d.ZAxis, tol);
var terrainPieces = terrainBrep.Split(projected, tol);
// Hide the terrain piece whose center is inside the patio footprint
```

---

## Edge Cases

| Situation | Handling |
|---|---|
| Patio entirely above terrain | All perimeter is downhill, no crossings → full downhill wall |
| Patio entirely below terrain | All perimeter is uphill, no crossings → full uphill wall |
| More than 2 crossings | Complex terrain — handle each pair of crossings as a separate above/below segment |
| Offset produces self-intersecting curve | Reduce wall thickness or simplify source curve |
| Terrain split produces too many pieces | Use tighter bounding box Z test to select correct piece |

---

## Layer convention
- Downhill retaining wall → `Site::patio_walls::downhill`
- Uphill retaining wall  → `Site::patio_walls::uphill`
- Or combine into `Site::patio_walls` with separate objects

---
*Added: May 2026 | Author: Claude (from Sean's design rules)*

## CRITICAL: Selection State and Script Execution

**The bug:** Running a Rhino MCP script clears or changes the active selection.
If you run a QUERY script to inspect selected objects, and then run a separate
MODIFY script to act on them, the selection will have changed between the two calls.
The modify script will act on the WRONG objects.

**The rule:** Always query AND modify selected objects in a SINGLE script call.

```csharp
// CORRECT — one script: inspect then act
foreach (var obj in rdoc.Objects.GetSelectedObjects(false, false)) {
    var bb = obj.Geometry.GetBoundingBox(false);
    // inspect, decide, then modify in the same loop
    var attr = obj.Attributes.Duplicate();
    attr.LayerIndex = targetLyr;
    rdoc.Objects.ModifyAttributes(obj, attr, true);
}

// WRONG — two separate scripts
// Script 1: query selected objects (this changes selection)
// Script 2: try to act on "selected" objects (selection is now different)
```

**Alternative:** If you must query first, store the object IDs as strings,
then pass them into the second script via rdoc.Strings.SetString().
