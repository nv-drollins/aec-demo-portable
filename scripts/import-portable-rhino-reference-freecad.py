"""Run inside FreeCAD to import the delivered Rhino template as reference geometry."""

from collections import Counter
import json
import os
from pathlib import Path
import re

import FreeCAD as App
import FreeCADGui as Gui
import Part


FORMAT = "aec-portable-rhino-reference-v1"
ADAPTER_ID = "aec-portable-rhino-import-v1"
MANIFEST_PATH = Path(os.environ["AEC_PORTABLE_RHINO_MANIFEST"])
OUTPUT_PATH = Path(os.environ["AEC_PORTABLE_REFERENCE_FCSTD"])
DOCUMENT_NAME = os.environ.get(
    "AEC_PORTABLE_REFERENCE_DOCUMENT", "PortableCliffHouseReference"
)


def safe_name(value):
    value = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    if not value or value[0].isdigit():
        value = "Reference_" + value
    return value[:120]


def add_property(obj, property_type, name, value, group="Rhino Reference"):
    if name not in obj.PropertiesList:
        obj.addProperty(property_type, name, group)
    setattr(obj, name, value)
    obj.setEditorMode(name, 1)


def vector(point, scale):
    return App.Vector(
        float(point[0]) * scale,
        float(point[1]) * scale,
        float(point[2]) * scale,
    )


def knots_and_multiplicities(raw_knots):
    knots = []
    multiplicities = []
    for raw in raw_knots:
        if knots and abs(raw - knots[-1]) <= 1e-12:
            multiplicities[-1] += 1
        else:
            knots.append(float(raw))
            multiplicities.append(1)
    if multiplicities:
        multiplicities[0] += 1
        multiplicities[-1] += 1
    return knots, multiplicities


def nurbs_edge(payload, scale):
    poles = [vector(point[:3], scale) for point in payload["control_points_xyzw"]]
    weights = [float(point[3]) for point in payload["control_points_xyzw"]]
    knots, multiplicities = knots_and_multiplicities(payload["rhino_knots"])
    curve = Part.BSplineCurve()
    curve.buildFromPolesMultsKnots(
        poles,
        multiplicities,
        knots,
        bool(payload["closed"]),
        int(payload["degree"]),
        weights,
    )
    return curve.toShape()


def polyline_shape(payload, scale):
    return Part.makePolygon([vector(point, scale) for point in payload["points"]])


def payload_edges(payload, scale):
    if payload["geometry"] == "polyline":
        return list(polyline_shape(payload, scale).Edges)
    if payload["geometry"] == "nurbs":
        return [nurbs_edge(payload, scale)]
    raise RuntimeError(f"Unsupported segment geometry: {payload['geometry']}")


def shape_for(item, scale):
    if item["geometry"] == "polyline":
        return polyline_shape(item, scale), "exact polyline"
    if item["geometry"] == "nurbs":
        return nurbs_edge(item, scale), "exact NURBS"
    if item["geometry"] == "polycurve":
        edges = []
        for segment in item["segments"]:
            edges.extend(payload_edges(segment, scale))
        wire = Part.Wire(edges)
        if bool(item["closed"]) and not wire.isClosed():
            raise RuntimeError("Exact PolyCurve segments did not form a closed wire")
        return wire, "exact segmented PolyCurve"
    raise RuntimeError(f"Unsupported source geometry: {item['geometry']}")


manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
if manifest.get("format") != FORMAT:
    raise RuntimeError(f"Expected {FORMAT}, got {manifest.get('format')!r}")
if manifest["counts"].get("unsupported"):
    raise RuntimeError("Portable reference manifest contains unsupported objects")

if DOCUMENT_NAME in App.listDocuments():
    previous = App.getDocument(DOCUMENT_NAME)
    metadata = previous.getObject("ReferenceMetadata")
    if metadata is None or getattr(metadata, "AdapterId", "") != ADAPTER_ID:
        raise RuntimeError(f"Refusing to replace non-adapter document {DOCUMENT_NAME}")
    App.closeDocument(DOCUMENT_NAME)

doc = App.newDocument(DOCUMENT_NAME)
doc.Label = "[REFERENCE] Delivered Cliff House Curves"
scale = float(manifest["source"]["millimetres_per_unit"])
metadata = doc.addObject("App::FeaturePython", "ReferenceMetadata")
metadata.Label = "REFERENCE IMPORT — DO NOT EDIT"
add_property(metadata, "App::PropertyString", "AdapterId", ADAPTER_ID)
add_property(metadata, "App::PropertyString", "ManifestFormat", FORMAT)
add_property(metadata, "App::PropertyString", "SourceFile", manifest["source"]["path"])
add_property(metadata, "App::PropertyString", "SourceSHA256", manifest["source"]["sha256"])
add_property(metadata, "App::PropertyString", "SourceUnits", manifest["source"]["units"])
add_property(metadata, "App::PropertyFloat", "MillimetresPerUnit", scale)

root_group = doc.addObject("App::DocumentObjectGroup", "ReferenceLayers")
root_group.Label = "Rhino layers (reference only)"
layer_groups = {}
for layer in sorted(
    manifest["layers"],
    key=lambda value: (value["full_path"].count("::"), value["index"]),
):
    full_path = layer["full_path"]
    group = doc.addObject(
        "App::DocumentObjectGroup", safe_name("Layer_" + full_path)
    )
    group.Label = "Layer: " + layer["name"]
    add_property(group, "App::PropertyString", "RhinoLayerPath", full_path)
    parent_path = full_path.rpartition("::")[0]
    (layer_groups[parent_path] if parent_path else root_group).addObject(group)
    layer_groups[full_path] = group

representations = Counter()
created = []
for item in manifest["objects"]:
    stem = item["name"] or item["type"]
    internal_name = safe_name(f"Rhino_{item['index']:03d}_{stem}")
    obj = doc.addObject("Part::Feature", internal_name)
    obj.Label = item["name"] or f"{item['type']} {item['index']:03d}"
    obj.Shape, representation = shape_for(item, scale)
    if obj.Shape.isNull():
        raise RuntimeError(f"Imported null shape for source object {item['index']}")
    obj.setEditorMode("Shape", 1)
    color = manifest["layers"][item["layer_index"]]["color_rgba"]
    obj.ViewObject.LineColor = tuple(channel / 255.0 for channel in color[:3])
    obj.ViewObject.LineWidth = 4.0 if item["closed"] else 2.0
    obj.ViewObject.Visibility = bool(item["visible"])
    add_property(obj, "App::PropertyString", "AdapterId", ADAPTER_ID)
    add_property(obj, "App::PropertyInteger", "RhinoObjectIndex", int(item["index"]))
    add_property(obj, "App::PropertyString", "RhinoObjectId", item["id"])
    add_property(obj, "App::PropertyString", "RhinoObjectType", item["type"])
    add_property(obj, "App::PropertyString", "RhinoObjectName", item["name"])
    add_property(obj, "App::PropertyString", "RhinoLayerPath", item["layer_path"])
    add_property(obj, "App::PropertyString", "Representation", representation)
    add_property(obj, "App::PropertyBool", "ReadOnlyReference", True)
    layer_groups[item["layer_path"]].addObject(obj)
    representations[representation] += 1
    created.append(obj)

doc.recompute()
invalid = [obj.Name for obj in created if obj.Shape.isNull()]
if invalid:
    raise RuntimeError(f"Imported invalid reference shapes: {invalid}")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
doc.saveAs(str(OUTPUT_PATH))
Gui.activeDocument().activeView().viewTop()
Gui.activeDocument().activeView().fitAll()
print(
    f"PORTABLE_FREECAD_REFERENCE_OK={OUTPUT_PATH} "
    f"curves={len(created)} layers={len(layer_groups)} invalid=0 "
    f"representations={dict(representations)}"
)
