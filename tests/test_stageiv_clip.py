# Copyright (c) 2026 Martial Systems LLC

from pathlib import Path

import numpy as np
import pytest

rasterio = pytest.importorskip("rasterio")
from rasterio.transform import from_origin

from rainstage.stageiv import clip_tif


def test_clip_converts_inches_and_masks(tmp_path: Path) -> None:
    path = tmp_path / "p.tif"
    data = np.zeros((8, 10), dtype=np.float32)
    data[2:5, 3:7] = 1.0  # 1 inch
    tf = from_origin(-86.20, 40.05, 0.01, 0.01)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=8,
        width=10,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=tf,
        nodata=-1.0,
    ) as dst:
        dst.write(data, 1)
        dst.update_tags(UNITS="inches")
    ring = [
        [-86.175, 39.995],
        [-86.125, 39.995],
        [-86.125, 40.035],
        [-86.175, 40.035],
        [-86.175, 39.995],
    ]
    gj = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [ring]}}
        ],
    }
    rec = clip_tif(str(path), gj)
    assert rec["native_units"] == "inches"
    assert rec["stored_units"] == "mm"
    wet = rec["rain_mm"][rec["rain_mm"] > 1.0]
    assert wet.size > 0
    assert np.allclose(wet, 25.4, atol=0.05)
