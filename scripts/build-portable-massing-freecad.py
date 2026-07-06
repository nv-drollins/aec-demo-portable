"""Run inside FreeCAD to build the checked portable target massing."""

import json
import os
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui
import Part


FORMAT = "aec-portable-freecad-massing-v1"
ADAPTER_ID = "aec-portable-massing-v1"
SPEC_PATH = Path(os.environ["AEC_PORTABLE_MASSING_SPEC"])
OUTPUT_PATH = Path(os.environ["AEC_PORTABLE_MASSING_FCSTD"])
REFERENCE_NAME = os.environ.get(
    "AEC_PORTABLE_REFERENCE_DOCUMENT", "PortableCliffHouseReference"
)
SITE_NAME = os.environ.get("AEC_PORTABLE_SITE_DOCUMENT", "PortableCliffHouseSite")
MASSING_NAME = os.environ.get(
    "AEC_PORTABLE_MASSING_DOCUMENT", "PortableCliffHouseMassing"
)
TOLERANCE_MM = 0.1


def add_string(obj, name, value):
    if name not in obj.PropertiesList:
        obj.addProperty("App::PropertyString", name, "AEC Portable Massing")
    setattr(obj, name, str(value))


def add_string_list(obj, name, values):
    if name not in obj.PropertiesList:
        obj.addProperty("App::PropertyStringList", name, "AEC Portable Massing")
    setattr(obj, name, [str(value) for value in values])


def triplet(value, label):
    if not isinstance(value, list) or len(value) != 3:
        raise RuntimeError(f"{label} must contain three numbers")
    return [float(item) for item in value]


def close_enough(actual, expected):
    return abs(float(actual) - float(expected)) <= TOLERANCE_MM


spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
if spec.get("format") != FORMAT:
    raise RuntimeError(f"Unexpected massing spec format: {spec.get('format')!r}")
if spec.get("source_units") != "metres":
    raise RuntimeError("Massing source units must be metres")
scale = float(spec["scale_to_mm"])
translation = triplet(spec["translation_mm"], "translation_mm")
objects = spec.get("objects", [])
groups = spec.get("groups", [])
if len(objects) != 11:
    raise RuntimeError(f"Expected 11 target envelopes, found {len(objects)}")

for required in (REFERENCE_NAME, SITE_NAME):
    if required not in App.listDocuments():
        raise RuntimeError(f"Required approved document is not open: {required}")
reference = App.getDocument(REFERENCE_NAME)
site = App.getDocument(SITE_NAME)
if getattr(site.getObject("BuildingPad"), "AdapterId", "") != "aec-portable-site-preparation-v1":
    raise RuntimeError("Portable site is missing its checked BuildingPad")
if getattr(site.getObject("TerrainSurface"), "AdapterId", "") != "aec-portable-site-preparation-v1":
    raise RuntimeError("Portable site is missing its checked TerrainSurface")

for check in spec["reference_checks"]:
    source = reference.getObject(check["object"])
    if source is None or source.Shape.isNull():
        raise RuntimeError(f"Missing reference anchor: {check['object']}")
    expected_min = triplet(check["bounds_mm"]["min"], "expected min")
    expected_max = triplet(check["bounds_mm"]["max"], "expected max")
    box = source.Shape.BoundBox
    actual = [box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax]
    expected = expected_min + expected_max
    if not all(close_enough(a, e) for a, e in zip(actual, expected)):
        raise RuntimeError(
            f"Reference anchor mismatch for {source.Name}: {actual} != {expected}"
        )

group_names = [str(item["name"]) for item in groups]
object_names = [str(item["name"]) for item in objects]
if len(group_names) != len(set(group_names)) or len(object_names) != len(set(object_names)):
    raise RuntimeError("Massing names must be unique")
if any(item["group"] not in group_names for item in objects):
    raise RuntimeError("Every massing object must reference a declared group")

validated = []
for item in objects:
    source_min = triplet(item["bounds_source_m"]["min"], f"{item['name']} min")
    source_max = triplet(item["bounds_source_m"]["max"], f"{item['name']} max")
    built_min = [source_min[i] * scale + translation[i] for i in range(3)]
    built_max = [source_max[i] * scale + translation[i] for i in range(3)]
    size = [built_max[i] - built_min[i] for i in range(3)]
    if any(value <= 0 for value in size):
        raise RuntimeError(f"Non-positive massing size for {item['name']}: {size}")
    color = triplet(item["color_rgb"], f"{item['name']} color")
    if any(value < 0.0 or value > 1.0 for value in color):
        raise RuntimeError(f"Invalid color for {item['name']}")
    validated.append((item, source_min, built_min, built_max, size, color))

if MASSING_NAME in App.listDocuments():
    previous = App.getDocument(MASSING_NAME)
    foreign = [
        obj.Name
        for obj in previous.Objects
        if getattr(obj, "AdapterId", "") != ADAPTER_ID
    ]
    if foreign:
        raise RuntimeError(
            f"Refusing to replace massing document with foreign objects: {foreign}"
        )
    App.closeDocument(MASSING_NAME)
document = App.newDocument(MASSING_NAME)
document.Label = "Delivered Cliff House — Target Massing Reconstruction"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
# FreeCAD requires an owner file path before creating cross-document App::Link
# objects. Save the new managed document once, then save the completed result
# again after validation.
document.saveAs(str(OUTPUT_PATH))

parent = document.addObject("App::DocumentObjectGroup", "PortableCliffHouseMassing")
parent.Label = "Portable Cliff House Massing"
add_string(parent, "AdapterId", ADAPTER_ID)
add_string(parent, "MassingSpecId", spec["id"])
add_string(parent, "MassingSpecPath", str(SPEC_PATH))
add_string(parent, "Provenance", spec["provenance"]["note"])

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
    add_string(group, "MassingSpecId", spec["id"])
    parent.addObject(group)
    created_groups[group.Name] = group

created = []
for item, source_min, built_min, built_max, size, color in validated:
    shape = Part.makeBox(size[0], size[1], size[2], App.Vector(*built_min))
    if shape.isNull() or len(shape.Solids) != 1:
        raise RuntimeError(f"Failed to build one solid for {item['name']}")
    obj = document.addObject("Part::Feature", item["name"])
    obj.Label = item["name"]
    obj.Shape = shape
    add_string(obj, "AdapterId", ADAPTER_ID)
    add_string(obj, "GeneratedBy", "scripts/build-portable-massing-freecad.py")
    add_string(obj, "MassingSpecId", spec["id"])
    add_string(obj, "DesignPhase", "massing")
    add_string(obj, "ArchitecturalRole", item["role"])
    add_string(obj, "MaterialRole", item["role"])
    add_string(obj, "TargetBoundsMetres", json.dumps(item["bounds_source_m"], separators=(",", ":")))
    add_string(obj, "BuiltBoundsMillimetres", json.dumps({"min": built_min, "max": built_max}, separators=(",", ":")))
    add_string_list(obj, "SourceReferenceObjects", item["source_reference_objects"])
    add_string_list(obj, "TargetBlenderObjects", item["target_blender_objects"])
    obj.ViewObject.ShapeColor = tuple(color)
    created_groups[item["group"]].addObject(obj)
    created.append(obj)

document.recompute()
invalid = [
    obj.Name for obj in created
    if obj.Shape.isNull() or len(obj.Shape.Solids) != 1
]
if invalid:
    raise RuntimeError(f"Invalid generated massing solids: {invalid}")
document.saveAs(str(OUTPUT_PATH))
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
total_volume = sum(float(obj.Shape.Volume) for obj in created)
overall = document.getObject("L3_roof_slab").Shape.BoundBox
print(
    f"PORTABLE_MASSING_BUILD_OK={OUTPUT_PATH} spec={spec['id']} "
    f"objects={len(created)} solids={sum(len(obj.Shape.Solids) for obj in created)} "
    f"site_context_links={len(context_links)} "
    f"translation_mm={translation} total_volume_mm3={total_volume:.3f} "
    f"roof_bounds_mm=[{overall.XMin:.3f},{overall.YMin:.3f},{overall.ZMin:.3f}]-"
    f"[{overall.XMax:.3f},{overall.YMax:.3f},{overall.ZMax:.3f}]"
)
