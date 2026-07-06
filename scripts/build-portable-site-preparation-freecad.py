"""Run inside FreeCAD to build source-derived site geometry for the portable demo."""

import os
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui
import Mesh
import Part


ADAPTER_ID = "aec-portable-site-preparation-v1"
REFERENCE_NAME = os.environ.get(
    "AEC_PORTABLE_REFERENCE_DOCUMENT", "PortableCliffHouseReference"
)
SITE_NAME = os.environ.get(
    "AEC_PORTABLE_SITE_DOCUMENT", "PortableCliffHouseSite"
)
OUTPUT_PATH = Path(os.environ["AEC_PORTABLE_SITE_FCSTD"])
NX = int(os.environ.get("AEC_PORTABLE_TERRAIN_NX", "81"))
NY = int(os.environ.get("AEC_PORTABLE_TERRAIN_NY", "73"))
if NX < 3 or NY < 3:
    raise RuntimeError("Terrain grid dimensions must each be at least 3")


def source_object(reference, name):
    obj = reference.getObject(name)
    if obj is None or obj.Shape.isNull():
        raise RuntimeError(f"Missing valid source object: {name}")
    return obj


def source_edge(reference, name):
    obj = source_object(reference, name)
    if len(obj.Shape.Edges) != 1:
        raise RuntimeError(f"Expected one source edge for {name}")
    return obj.Shape.Edges[0]


def point_fraction(edge, fraction):
    start, end = edge.ParameterRange
    return edge.valueAt(start + (end - start) * fraction)


def horizontal_point(edge, u):
    # Source v-curves run east to west. Site u runs west to east.
    return point_fraction(edge, 1.0 - u)


def vertical_point(edge, v):
    # Source u-curves run north to south. Site v runs south to north.
    return point_fraction(edge, 1.0 - v)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def string_property(obj, name, value):
    if name not in obj.PropertiesList:
        obj.addProperty("App::PropertyString", name, "AEC Portable Demo")
    setattr(obj, name, value)


def source_properties(target, source, role):
    string_property(target, "AdapterId", ADAPTER_ID)
    string_property(target, "GeneratedBy", "scripts/build-portable-site-preparation-freecad.py")
    string_property(target, "SourceDocument", REFERENCE_NAME)
    string_property(target, "SourceReferenceObject", source.Name)
    string_property(target, "SourceRhinoLayer", getattr(source, "RhinoLayerPath", ""))
    string_property(target, "MaterialRole", role)


if REFERENCE_NAME not in App.listDocuments():
    raise RuntimeError(f"Reference document is not open: {REFERENCE_NAME}")
reference = App.getDocument(REFERENCE_NAME)
if SITE_NAME in App.listDocuments():
    previous = App.getDocument(SITE_NAME)
    foreign = [
        obj.Name
        for obj in previous.Objects
        if getattr(obj, "AdapterId", "") != ADAPTER_ID
    ]
    if foreign:
        raise RuntimeError(
            f"Refusing to replace site document containing foreign objects: {foreign}"
        )
    App.closeDocument(SITE_NAME)
document = App.newDocument(SITE_NAME)
document.Label = "Delivered Cliff House — Source-Derived Site"

# The source fingerprint fixes these semantic mappings for beach_house_02.3dm.
north = source_edge(reference, "Rhino_004_NurbsCurve")
east = source_edge(reference, "Rhino_005_NurbsCurve")
middle = source_edge(reference, "Rhino_006_NurbsCurve")
south = source_edge(reference, "Rhino_007_NurbsCurve")
west = source_edge(reference, "Rhino_008_NurbsCurve")

west_south = vertical_point(west, 0.0)
west_north = vertical_point(west, 1.0)
east_south = vertical_point(east, 0.0)
east_north = vertical_point(east, 1.0)
x_min = min(west_south.x, west_north.x)
x_max = max(east_south.x, east_north.x)
y_min = min(west_south.y, east_south.y)
y_max = max(west_north.y, east_north.y)

corner_sw = horizontal_point(south, 0.0).z
corner_se = horizontal_point(south, 1.0).z
corner_nw = horizontal_point(north, 0.0).z
corner_ne = horizontal_point(north, 1.0).z
guide_edges = (south, north, east, west, middle)
guide_elevations = [
    point_fraction(edge, sample / 200.0).z
    for edge in guide_edges
    for sample in range(201)
]
guide_z_min = min(guide_elevations)
guide_z_max = max(guide_elevations)


def boundary_surface_z(u, v, west_z, east_z):
    south_z = horizontal_point(south, u).z
    north_z = horizontal_point(north, u).z
    bilinear = (
        (1.0 - u) * (1.0 - v) * corner_sw
        + u * (1.0 - v) * corner_se
        + (1.0 - u) * v * corner_nw
        + u * v * corner_ne
    )
    return (
        (1.0 - v) * south_z
        + v * north_z
        + (1.0 - u) * west_z
        + u * east_z
        - bilinear
    )


vertices = []
for row in range(NY):
    v = row / (NY - 1)
    west_point = vertical_point(west, v)
    east_point = vertical_point(east, v)
    middle_point = vertical_point(middle, v)
    middle_u = (middle_point.x - x_min) / (x_max - x_min)
    middle_base = boundary_surface_z(
        middle_u, v, west_point.z, east_point.z
    )
    middle_delta = middle_point.z - middle_base
    for column in range(NX):
        u = column / (NX - 1)
        x = x_min + u * (x_max - x_min)
        y = y_min + v * (y_max - y_min)
        base_z = boundary_surface_z(u, v, west_point.z, east_point.z)
        if u <= middle_u:
            weight = u / middle_u if middle_u > 0.0 else 0.0
        else:
            weight = (
                (1.0 - u) / (1.0 - middle_u)
                if middle_u < 1.0
                else 0.0
            )
        z = base_z + smoothstep(weight) * middle_delta
        z = max(guide_z_min, min(guide_z_max, z))
        vertices.append(App.Vector(x, y, z))

triangles = []
for row in range(NY - 1):
    for column in range(NX - 1):
        southwest = row * NX + column
        southeast = southwest + 1
        northwest = (row + 1) * NX + column
        northeast = northwest + 1
        triangles.append(
            [vertices[southwest], vertices[southeast], vertices[northwest]]
        )
        triangles.append(
            [vertices[southeast], vertices[northeast], vertices[northwest]]
        )

terrain = document.addObject("Mesh::Feature", "TerrainSurface")
terrain.Label = "Terrain Surface (source-derived)"
terrain.Mesh = Mesh.Mesh(triangles)
string_property(terrain, "AdapterId", ADAPTER_ID)
string_property(terrain, "GeneratedBy", "scripts/build-portable-site-preparation-freecad.py")
string_property(terrain, "SourceDocument", REFERENCE_NAME)
string_property(
    terrain,
    "SourceGuideCurves",
    "Rhino_004,Rhino_005,Rhino_006,Rhino_007,Rhino_008",
)
string_property(terrain, "MaterialRole", "terrain")
terrain.addProperty("App::PropertyInteger", "GridNX", "AEC Portable Demo")
terrain.addProperty("App::PropertyInteger", "GridNY", "AEC Portable Demo")
terrain.GridNX = NX
terrain.GridNY = NY
terrain.ViewObject.ShapeColor = (0.27, 0.36, 0.18)

boundary = document.addObject("Part::Feature", "LotBoundary")
boundary.Label = "Lot Boundary (source guides)"
boundary.Shape = Part.makeCompound(
    [edge.copy() for edge in (north, east, south, west)]
)
string_property(boundary, "AdapterId", ADAPTER_ID)
string_property(boundary, "GeneratedBy", "scripts/build-portable-site-preparation-freecad.py")
string_property(boundary, "SourceDocument", REFERENCE_NAME)
string_property(boundary, "MaterialRole", "lot_boundary")
boundary.ViewObject.LineColor = (0.95, 0.80, 0.12)
boundary.ViewObject.LineWidth = 5.0

SLABS = (
    ("Rhino_002_building_plan", "BuildingPad", "building_pad", (0.42, 0.44, 0.48)),
    ("Rhino_003_driveway_plan", "DrivewayPad", "driveway", (0.16, 0.17, 0.18)),
    ("Rhino_009_PolyCurve", "PatioPad", "patio", (0.70, 0.68, 0.62)),
    ("Rhino_010_PolylineCurve", "StairsPad", "stairs", (0.62, 0.60, 0.55)),
)
created_slabs = []
for source_name, output_name, role, color in SLABS:
    source = source_object(reference, source_name)
    wire = (
        source.Shape
        if source.Shape.ShapeType == "Wire"
        else Part.Wire(source.Shape.Edges)
    )
    if not wire.isClosed():
        raise RuntimeError(f"Source footprint is not closed: {source_name}")
    solid = Part.Face(wire).extrude(App.Vector(0.0, 0.0, 50.0))
    if solid.isNull() or len(solid.Solids) != 1:
        raise RuntimeError(f"Failed to create slab from {source_name}")
    obj = document.addObject("Part::Feature", output_name)
    obj.Label = output_name
    obj.Shape = solid
    source_properties(obj, source, role)
    obj.ViewObject.ShapeColor = color
    created_slabs.append(obj)

document.recompute()
if terrain.Mesh.CountFacets != len(triangles):
    raise RuntimeError("Terrain facet count did not survive recompute")
for obj in (boundary, *created_slabs):
    if obj.Shape.isNull():
        raise RuntimeError(f"Generated null shape: {obj.Name}")

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
document.saveAs(str(OUTPUT_PATH))
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
terrain_box = terrain.Mesh.BoundBox
print(
    f"PORTABLE_SITE_BUILD_OK={OUTPUT_PATH} "
    f"objects={len(document.Objects)} slabs={len(created_slabs)} "
    f"terrain_vertices={len(vertices)} terrain_faces={len(triangles)} "
    f"bounds_mm=[{terrain_box.XMin:.3f},{terrain_box.YMin:.3f},{terrain_box.ZMin:.3f}]-"
    f"[{terrain_box.XMax:.3f},{terrain_box.YMax:.3f},{terrain_box.ZMax:.3f}]"
)
