"""Run inside FreeCAD to build checked target-derived architectural detailing."""

from collections import Counter
import json
import os
from pathlib import Path
import re

import FreeCAD as App
import FreeCADGui as Gui
import Part


FORMAT = "aec-portable-detailing-target-v1"
ADAPTER_ID = "aec-portable-detailing-v1"
MANIFEST_PATH = Path(os.environ["AEC_PORTABLE_DETAILING_MANIFEST"])
OUTPUT_PATH = Path(os.environ["AEC_PORTABLE_DETAILING_FCSTD"])
SITE_NAME = os.environ.get("AEC_PORTABLE_SITE_DOCUMENT", "PortableCliffHouseSite")
MASSING_NAME = os.environ.get(
    "AEC_PORTABLE_MASSING_DOCUMENT", "PortableCliffHouseMassing"
)
DETAILING_NAME = os.environ.get(
    "AEC_PORTABLE_DETAILING_DOCUMENT", "PortableCliffHouseDetailing"
)


def safe_name(value):
    value = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    if not value or value[0].isdigit():
        value = "Detail_" + value
    return value[:120]


def add_string(obj, name, value):
    if name not in obj.PropertiesList:
        obj.addProperty("App::PropertyString", name, "AEC Portable Detailing")
    setattr(obj, name, str(value))


def add_string_list(obj, name, values):
    if name not in obj.PropertiesList:
        obj.addProperty("App::PropertyStringList", name, "AEC Portable Detailing")
    setattr(obj, name, [str(value) for value in values])


def triplet(value, label):
    if not isinstance(value, list) or len(value) != 3:
        raise RuntimeError(f"{label} must contain three numbers")
    return [float(item) for item in value]


def expanded_box(shape, clearance):
    box = shape.BoundBox
    return Part.makeBox(
        box.XLength + 2.0 * clearance,
        box.YLength + 2.0 * clearance,
        box.ZLength + 2.0 * clearance,
        App.Vector(
            box.XMin - clearance,
            box.YMin - clearance,
            box.ZMin - clearance,
        ),
    )


manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
if manifest.get("format") != FORMAT:
    raise RuntimeError(f"Unexpected detailing manifest: {manifest.get('format')!r}")
records = manifest.get("records", [])
if len(records) != int(manifest.get("record_count", -1)):
    raise RuntimeError("Detailing manifest record count mismatch")
scale = float(manifest["blender_units_to_mm"])
translation = triplet(manifest["translation_mm"], "translation_mm")
styles = manifest["role_style"]
groups = manifest["groups"]

for required in (SITE_NAME, MASSING_NAME):
    if required not in App.listDocuments():
        raise RuntimeError(f"Required approved document is not open: {required}")
site = App.getDocument(SITE_NAME)
massing = App.getDocument(MASSING_NAME)
if getattr(site.getObject("BuildingPad"), "AdapterId", "") != "aec-portable-site-preparation-v1":
    raise RuntimeError("Approved portable site is invalid")
if getattr(massing.getObject("PortableCliffHouseMassing"), "AdapterId", "") != "aec-portable-massing-v1":
    raise RuntimeError("Approved portable massing is invalid")

if DETAILING_NAME in App.listDocuments():
    previous = App.getDocument(DETAILING_NAME)
    foreign = [
        obj.Name
        for obj in previous.Objects
        if getattr(obj, "AdapterId", "") != ADAPTER_ID
    ]
    if foreign:
        raise RuntimeError(
            f"Refusing to replace detailing document with foreign objects: {foreign}"
        )
    App.closeDocument(DETAILING_NAME)

document = App.newDocument(DETAILING_NAME)
document.Label = "Delivered Cliff House — Target Detailing Reconstruction"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
document.saveAs(str(OUTPUT_PATH))

parent = document.addObject("App::DocumentObjectGroup", "PortableCliffHouseDetailing")
parent.Label = "Portable Cliff House Detailing"
add_string(parent, "AdapterId", ADAPTER_ID)
add_string(parent, "DetailingSpecId", manifest["spec_id"])
add_string(parent, "TargetScene", manifest["scene"])
add_string(parent, "Representation", manifest["representation"])
add_string(parent, "Provenance", manifest["provenance_note"])

context_group = document.addObject("App::DocumentObjectGroup", "SiteContext")
context_group.Label = "Validated Site Context (linked)"
add_string(context_group, "AdapterId", ADAPTER_ID)
add_string(context_group, "SourceDocument", SITE_NAME)
parent.addObject(context_group)
context_links = []
for source in site.Objects:
    link = document.addObject("App::Link", "Site_" + source.Name)
    link.Label = "Site / " + source.Label
    add_string(link, "AdapterId", ADAPTER_ID)
    add_string(link, "SourceDocument", SITE_NAME)
    add_string(link, "SourceObject", source.Name)
    link.LinkedObject = source
    context_group.addObject(link)
    context_links.append(link)

created_groups = {}
for group_spec in groups:
    group = document.addObject("App::DocumentObjectGroup", group_spec["name"])
    group.Label = group_spec["label"]
    add_string(group, "AdapterId", ADAPTER_ID)
    add_string(group, "DetailingSpecId", manifest["spec_id"])
    parent.addObject(group)
    created_groups[group.Name] = group

planned = []
for record in records:
    raw_min = triplet(record["bounds"]["min"], f"{record['name']} min")
    raw_max = triplet(record["bounds"]["max"], f"{record['name']} max")
    built_min = [raw_min[i] * scale + translation[i] for i in range(3)]
    built_max = [raw_max[i] * scale + translation[i] for i in range(3)]
    size = [built_max[i] - built_min[i] for i in range(3)]
    if any(value < 5.0 for value in size):
        raise RuntimeError(f"Detail envelope is too thin for {record['name']}: {size}")
    role = record["role"]
    if role not in styles:
        raise RuntimeError(f"Missing style for role {role!r}")
    if record["group"] not in created_groups:
        raise RuntimeError(f"Missing group for {record['name']}")
    shape = Part.makeBox(size[0], size[1], size[2], App.Vector(*built_min))
    if shape.isNull() or len(shape.Solids) != 1:
        raise RuntimeError(f"Failed to build detail solid {record['name']}")
    planned.append({"record": record, "role": role, "shape": shape})

# The target wall meshes already contain openings. Their axis-aligned envelopes
# do not, so subtract the approved glazing and door envelopes with clearance.
opening_shapes = [
    item["shape"]
    for item in planned
    if item["role"] in {"glazing", "door"}
]
wall_opening_cuts = 0
for item in planned:
    if item["role"] != "wall":
        continue
    shape = item["shape"]
    for opening in opening_shapes:
        if not shape.BoundBox.intersect(opening.BoundBox):
            continue
        before = float(shape.Volume)
        shape = shape.cut(expanded_box(opening, 2.0))
        if before - float(shape.Volume) > 1.0:
            wall_opening_cuts += 1
    if shape.isNull() or not shape.Solids:
        raise RuntimeError(
            f"Wall opening cuts invalidated {item['record']['name']}"
        )
    item["shape"] = shape

# Split large target glass envelopes around mullions/frames so glazing is not
# buried inside frame solids. A 1 mm clearance keeps boolean faces distinct.
frame_shapes = [
    item["shape"]
    for item in planned
    if item["role"] in {"mullion", "frame", "entry_frame"}
]
glazing_frame_cuts = 0
for item in planned:
    if item["role"] != "glazing":
        continue
    shape = item["shape"]
    for frame in frame_shapes:
        if not shape.BoundBox.intersect(frame.BoundBox):
            continue
        before = float(shape.Volume)
        shape = shape.cut(expanded_box(frame, 1.0))
        if before - float(shape.Volume) > 1.0:
            glazing_frame_cuts += 1
    if shape.isNull() or not shape.Solids:
        raise RuntimeError(
            f"Frame clearances invalidated {item['record']['name']}"
        )
    item["shape"] = shape

created = []
role_counts = Counter()
for item in planned:
    record = item["record"]
    role = item["role"]
    shape = item["shape"]
    obj = document.addObject("Part::Feature", safe_name(record["name"]))
    obj.Label = record["name"]
    obj.Shape = shape
    add_string(obj, "AdapterId", ADAPTER_ID)
    add_string(obj, "GeneratedBy", "scripts/build-portable-detailing-freecad.py")
    add_string(obj, "DetailingSpecId", manifest["spec_id"])
    add_string(obj, "DesignPhase", "architectural_detailing")
    add_string(obj, "ArchitecturalRole", role)
    add_string(obj, "MaterialRole", role)
    add_string(obj, "TargetBoundsBlenderUnits", json.dumps(record["bounds"], separators=(",", ":")))
    add_string_list(obj, "TargetBlenderObjects", record["target_objects"])
    style = styles[role]
    obj.ViewObject.ShapeColor = tuple(float(value) for value in style["color"])
    obj.ViewObject.Transparency = int(style["transparency"])
    created_groups[record["group"]].addObject(obj)
    role_counts[role] += 1
    created.append(obj)

document.recompute()
invalid = [
    obj.Name for obj in created
    if obj.Shape.isNull() or len(obj.Shape.Solids) < 1
]
if invalid:
    raise RuntimeError(f"Invalid generated detail solids: {invalid}")

by_role = {}
for obj in created:
    by_role.setdefault(obj.ArchitecturalRole, []).append(obj)


def overlap_count(left_roles, right_roles):
    left = [obj for role in left_roles for obj in by_role.get(role, [])]
    right = [obj for role in right_roles for obj in by_role.get(role, [])]
    count = 0
    for first in left:
        for second in right:
            if not first.Shape.BoundBox.intersect(second.Shape.BoundBox):
                continue
            if first.Shape.common(second.Shape).Volume > 1.0:
                count += 1
    return count


wall_glass_overlaps = overlap_count(["wall"], ["glazing"])
wall_door_overlaps = overlap_count(["wall"], ["door"])
frame_glass_overlaps = overlap_count(
    ["mullion", "frame", "entry_frame"], ["glazing"]
)
if wall_glass_overlaps or wall_door_overlaps or frame_glass_overlaps:
    raise RuntimeError(
        "Detailing overlap gate failed: "
        f"wall_glass={wall_glass_overlaps} "
        f"wall_door={wall_door_overlaps} "
        f"frame_glass={frame_glass_overlaps}"
    )
# Transient OCC common() operations can leave stale Coin tessellation caches in
# FreeCAD 1.1. Recompute and refresh before saving/capturing the review view.
document.recompute()
Gui.updateGui()
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
document.saveAs(str(OUTPUT_PATH))
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
print(
    "PORTABLE_DETAILING_OVERLAP_OK "
    "wall_glass=0 wall_door=0 frame_glass=0"
)
print(
    f"PORTABLE_DETAILING_BUILD_OK={OUTPUT_PATH} spec={manifest['spec_id']} "
    f"objects={len(created)} solids={sum(len(obj.Shape.Solids) for obj in created)} "
    f"site_context_links={len(context_links)} wall_opening_cuts={wall_opening_cuts} "
    f"glazing_frame_cuts={glazing_frame_cuts} "
    "wall_glass_overlaps=0 wall_door_overlaps=0 frame_glass_overlaps=0 "
    f"roles={json.dumps(dict(sorted(role_counts.items())), separators=(',', ':'))}"
)
