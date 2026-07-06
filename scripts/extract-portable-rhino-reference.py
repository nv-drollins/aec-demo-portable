#!/usr/bin/env python3
"""Extract the delivered Rhino template into an exact FreeCAD-neutral manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import rhino3dm


FORMAT = "aec-portable-rhino-reference-v1"
UNIT_TO_MM = {
    "Microns": 0.001,
    "Millimeters": 1.0,
    "Centimeters": 10.0,
    "Meters": 1000.0,
    "Kilometers": 1_000_000.0,
    "Microinches": 0.0000254,
    "Mils": 0.0254,
    "Inches": 25.4,
    "Feet": 304.8,
    "Yards": 914.4,
    "Miles": 1_609_344.0,
}


def xyz(point) -> list[float]:
    return [float(point.X), float(point.Y), float(point.Z)]


def rgba(color) -> list[int]:
    return [int(channel) for channel in color]


def sample_curve(curve, count: int) -> list[list[float]]:
    domain = curve.Domain
    start, end = float(domain.T0), float(domain.T1)
    return [
        xyz(curve.PointAt(start + (end - start) * index / count))
        for index in range(count + 1)
    ]


def update_bounds(bounds: list[list[float]], points: list[list[float]]) -> None:
    for point in points:
        for axis in range(3):
            bounds[0][axis] = min(bounds[0][axis], point[axis])
            bounds[1][axis] = max(bounds[1][axis], point[axis])


def polyline_payload(curve) -> dict:
    polyline = curve.TryGetPolyline()
    return {
        "geometry": "polyline",
        "closed": bool(curve.IsClosed),
        "points": [xyz(polyline[index]) for index in range(len(polyline))],
    }


def nurbs_payload(curve) -> dict:
    nurbs = (
        curve
        if isinstance(curve, rhino3dm.NurbsCurve)
        else curve.ToNurbsCurve()
    )
    if nurbs is None:
        raise RuntimeError(f"Could not convert {type(curve).__name__} to NURBS")
    return {
        "geometry": "nurbs",
        "closed": bool(curve.IsClosed),
        "degree": int(nurbs.Degree),
        "order": int(nurbs.Order),
        "control_points_xyzw": [
            [float(point.X), float(point.Y), float(point.Z), float(point.W)]
            for point in nurbs.Points
        ],
        "rhino_knots": [float(knot) for knot in nurbs.Knots],
    }


def polycurve_payload(curve) -> dict:
    segments = []
    for index in range(curve.SegmentCount):
        segment = curve.SegmentCurve(index)
        if isinstance(segment, rhino3dm.PolylineCurve):
            payload = polyline_payload(segment)
        else:
            payload = nurbs_payload(segment)
        payload["source_type"] = type(segment).__name__
        segments.append(payload)
    return {
        "geometry": "polycurve",
        "closed": bool(curve.IsClosed),
        "segments": segments,
    }


def extract(source: Path, samples: int) -> dict:
    model = rhino3dm.File3dm.Read(str(source))
    if model is None:
        raise RuntimeError(f"rhino3dm could not read {source}")
    unit_name = str(model.Settings.ModelUnitSystem).rsplit(".", 1)[-1]
    if unit_name not in UNIT_TO_MM:
        raise RuntimeError(f"Unsupported Rhino unit system: {unit_name}")

    layers = [
        {
            "index": index,
            "id": str(layer.Id),
            "parent_id": str(layer.ParentLayerId),
            "name": layer.Name,
            "full_path": layer.FullPath,
            "visible": bool(layer.Visible),
            "color_rgba": rgba(layer.Color),
        }
        for index, layer in enumerate(model.Layers)
    ]
    bounds = [[float("inf")] * 3, [float("-inf")] * 3]
    objects = []
    type_counts: dict[str, int] = {}
    for index, file_object in enumerate(model.Objects):
        geometry = file_object.Geometry
        attributes = file_object.Attributes
        type_name = type(geometry).__name__
        type_counts[type_name] = type_counts.get(type_name, 0) + 1
        layer = layers[attributes.LayerIndex]
        item = {
            "index": index,
            "id": str(attributes.Id),
            "name": attributes.Name or "",
            "type": type_name,
            "layer_index": int(attributes.LayerIndex),
            "layer_path": layer["full_path"],
            "visible": bool(attributes.Visible),
        }
        if isinstance(geometry, rhino3dm.PolylineCurve):
            item.update(polyline_payload(geometry))
        elif isinstance(geometry, rhino3dm.NurbsCurve):
            item.update(nurbs_payload(geometry))
        elif isinstance(geometry, rhino3dm.PolyCurve):
            item.update(polycurve_payload(geometry))
        else:
            item.update(
                {
                    "geometry": "unsupported",
                    "reason": f"Unsupported {type_name}",
                }
            )
        if item["geometry"] != "unsupported":
            preview = sample_curve(geometry, samples)
            item["preview_points"] = preview
            update_bounds(bounds, preview)
        objects.append(item)

    if bounds[0][0] == float("inf"):
        bounds = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    curve_count = sum(
        item["geometry"] in {"polyline", "nurbs", "polycurve"}
        for item in objects
    )
    return {
        "format": FORMAT,
        "source": {
            "path": str(source.resolve()),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "archive_version": int(model.ArchiveVersion),
            "units": unit_name,
            "millimetres_per_unit": UNIT_TO_MM[unit_name],
            "absolute_tolerance": float(model.Settings.ModelAbsoluteTolerance),
        },
        "bounds_source_units": {"min": bounds[0], "max": bounds[1]},
        "layers": layers,
        "objects": objects,
        "counts": {
            "layers": len(layers),
            "objects": len(objects),
            "curves": curve_count,
            "unsupported": sum(
                item["geometry"] == "unsupported" for item in objects
            ),
            "types": type_counts,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--samples", type=int, default=96)
    args = parser.parse_args()
    if args.samples < 8:
        parser.error("--samples must be at least 8")
    if not args.source.is_file():
        parser.error(f"source does not exist: {args.source}")
    manifest = extract(args.source, args.samples)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    counts = manifest["counts"]
    print(
        f"PORTABLE_RHINO_EXTRACT_OK={args.manifest.resolve()} "
        f"objects={counts['objects']} curves={counts['curves']} "
        f"unsupported={counts['unsupported']}"
    )


if __name__ == "__main__":
    main()
