# Copyright (c) 2026 Martial Systems LLC
"""NLDI basin for USGS-03351000. Refuse HUC-8 and the 5 km HAND window."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from rainstage.config import (
    DRAINAGE_TOLERANCE,
    GAGE_ID,
    HUC8_REFUSED,
    LOCKED_NLDI_BASIN_SHA256,
    MI2_PER_M2,
    NLDI_BASIN_URL,
    PUBLISHED_DRAINAGE_MI2,
)
from rainstage.errors import FetchError
from rainstage.http import get_json


def _rings(geom: dict[str, Any]) -> list[list[tuple[float, float]]]:
    gtype = str(geom.get("type") or "")
    coords = geom.get("coordinates")
    if gtype == "Polygon":
        polys = [coords]
    elif gtype == "MultiPolygon":
        polys = coords
    else:
        raise FetchError(f"NLDI basin geometry {gtype} is not a polygon")
    rings: list[list[tuple[float, float]]] = []
    for poly in polys:
        if not poly:
            continue
        exterior = poly[0]
        rings.append([(float(x), float(y)) for x, y in exterior])
    if not rings:
        raise FetchError("NLDI basin has no rings")
    return rings


def area_mi2(geojson: dict[str, Any]) -> float:
    from pyproj import Geod

    geod = Geod(ellps="WGS84")
    feats = geojson.get("features") or []
    if not feats:
        raise FetchError("NLDI basin FeatureCollection is empty")
    geom = feats[0].get("geometry") or {}
    total = 0.0
    for ring in _rings(geom):
        if len(ring) < 4:
            continue
        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        area, _perim = geod.polygon_area_perimeter(lons, lats)
        total += abs(float(area))
    return total * MI2_PER_M2


def basin_sha(geojson: dict[str, Any]) -> str:
    blob = json.dumps(geojson, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def require_nldi_basin(geojson: dict[str, Any], *, source: str, gage_id: str) -> dict[str, Any]:
    if source in {"huc8", HUC8_REFUSED, "hand_window"}:
        raise FetchError("HUC-8 and the 5 km HAND window are refused; NLDI 03351000 only")
    if source != "nldi":
        raise FetchError(f"basin source {source} refused; NLDI {GAGE_ID} only")
    if gage_id != GAGE_ID:
        raise FetchError(f"gage {gage_id} refused; this tree is {GAGE_ID}")
    area = area_mi2(geojson)
    rel = abs(area - PUBLISHED_DRAINAGE_MI2) / PUBLISHED_DRAINAGE_MI2
    if rel > DRAINAGE_TOLERANCE:
        raise FetchError(
            f"basin {area:.1f} mi² is not the published {PUBLISHED_DRAINAGE_MI2:,.0f} mi² "
            f"NLDI drainage (HUC-8 and the 5 km HAND window are refused)"
        )
    return {
        "gage_id": gage_id,
        "source": "nldi",
        "area_mi2": float(area),
        "sha256": basin_sha(geojson),
        "n_features": len(geojson.get("features") or []),
    }


def fetch_nldi_basin(*, get_json_fn=None) -> tuple[dict[str, Any], dict[str, Any]]:
    getter = get_json_fn or get_json
    doc = getter(NLDI_BASIN_URL)
    meta = require_nldi_basin(doc, source="nldi", gage_id=GAGE_ID)
    if meta["sha256"] != LOCKED_NLDI_BASIN_SHA256:
        raise FetchError(
            f"NLDI basin sha {meta['sha256']} drifted from pin {LOCKED_NLDI_BASIN_SHA256}"
        )
    return doc, meta
