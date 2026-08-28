# Copyright (c) 2026 Martial Systems LLC
"""NCEP Stage IV daily GeoTIFF, clipped to the NLDI basin. Units stored as mm."""

from __future__ import annotations

from datetime import date
from typing import Any

import numpy as np

from rainstage.config import STAGEIV_INCH_TO_MM, STAGEIV_URL
from rainstage.errors import FetchError

_GDAL_ENV = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
    "GDAL_HTTP_UNSAFESSL": "NO",
}


def stageiv_url(day: date) -> str:
    stamp = day.strftime("%Y%m%d")
    return STAGEIV_URL.format(y=day.year, m=day.month, d=day.day, stamp=stamp)


def _native_units(src) -> str:
    tags = {str(k).lower(): str(v).lower() for k, v in (src.tags() or {}).items()}
    units = tags.get("units") or tags.get("unit") or ""
    desc = ""
    if src.descriptions:
        desc = str(src.descriptions[0] or "").lower()
    blob = f"{units} {desc}"
    if "mm" in blob or "millimet" in blob:
        return "mm"
    if "inch" in blob or units in {"in", "inches"}:
        return "inches"
    return "inches"


def _to_mm(arr: np.ndarray, native: str) -> np.ndarray:
    out = np.asarray(arr, dtype=float)
    if native == "mm":
        return out
    return out * STAGEIV_INCH_TO_MM


def clip_tif(
    path_or_url: str,
    geojson: dict[str, Any],
) -> dict[str, Any]:
    """Read a Stage IV GeoTIFF and return basin cell rain in mm plus grid coords."""
    import rasterio
    from rasterio.features import geometry_mask
    from rasterio.warp import transform_geom

    env = {k: v for k, v in _GDAL_ENV.items()}
    opener = path_or_url
    if path_or_url.startswith("http"):
        opener = f"/vsicurl/{path_or_url}"
    feats = geojson.get("features") or []
    if not feats:
        raise FetchError("Stage IV clip: empty basin")
    geom = feats[0].get("geometry")
    if not geom:
        raise FetchError("Stage IV clip: basin has no geometry")
    try:
        with rasterio.Env(**env):
            with rasterio.open(opener) as src:
                native = _native_units(src)
                geom_r = transform_geom("EPSG:4326", src.crs, geom, precision=6)
                mask = geometry_mask(
                    [geom_r],
                    out_shape=(src.height, src.width),
                    transform=src.transform,
                    invert=True,
                )
                if not mask.any():
                    raise FetchError("Stage IV clip: basin covers no pixels")
                rows, cols = np.where(mask)
                r0, r1 = int(rows.min()), int(rows.max()) + 1
                c0, c1 = int(cols.min()), int(cols.max()) + 1
                window = rasterio.windows.Window.from_slices((r0, r1), (c0, c1))
                data = src.read(1, window=window, masked=True)
                submask = mask[r0:r1, c0:c1]
                nodata = src.nodata
                arr = np.array(data, dtype=float)
                if nodata is not None:
                    arr[arr == float(nodata)] = np.nan
                arr[arr < 0] = np.nan
                arr[~submask] = np.nan
                rain_mm = _to_mm(arr, native)
                valid = submask & np.isfinite(rain_mm)
                if not valid.any():
                    raise FetchError("Stage IV clip: no finite rain cells")
                rr, cc = np.where(valid)
                values = rain_mm[rr, cc]
                xs, ys = rasterio.transform.xy(src.window_transform(window), rr, cc, offset="center")
                return {
                    "rain_mm": np.asarray(values, dtype=np.float32),
                    "cell_row": (rr + r0).astype(np.int32),
                    "cell_col": (cc + c0).astype(np.int32),
                    "cell_x": np.asarray(xs, dtype=np.float64),
                    "cell_y": np.asarray(ys, dtype=np.float64),
                    "grid_shape": (int(r1 - r0), int(c1 - c0)),
                    "local_row": rr.astype(np.int32),
                    "local_col": cc.astype(np.int32),
                    "crs": str(src.crs),
                    "transform": tuple(src.transform)[:6],
                    "native_units": native,
                    "stored_units": "mm",
                    "window": (r0, r1, c0, c1),
                }
    except FetchError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise FetchError(f"Stage IV read failed: {path_or_url}: {exc}") from exc


def align_cells(days: list[dict[str, Any]]) -> tuple[np.ndarray, dict[str, Any]]:
    """Stack days on the intersection of cell (row, col) keys."""
    if not days:
        raise FetchError("Stage IV: zero days after clip")
    keys = None
    for rec in days:
        cur = set(zip(rec["cell_row"].tolist(), rec["cell_col"].tolist()))
        keys = cur if keys is None else (keys & cur)
    if not keys:
        raise FetchError("Stage IV: no shared basin cells across days")
    ordered = sorted(keys)
    n_cells = len(ordered)
    index = {k: i for i, k in enumerate(ordered)}
    rain = np.full((len(days), n_cells), np.nan, dtype=np.float32)
    loc = None
    for t, rec in enumerate(days):
        for r, c, v, lr, lc, x, y in zip(
            rec["cell_row"],
            rec["cell_col"],
            rec["rain_mm"],
            rec["local_row"],
            rec["local_col"],
            rec["cell_x"],
            rec["cell_y"],
        ):
            k = (int(r), int(c))
            if k in index:
                rain[t, index[k]] = v
                if loc is None:
                    loc = {}
                loc.setdefault(k, (int(lr), int(lc), float(x), float(y)))
    rows = np.array([k[0] for k in ordered], dtype=np.int32)
    cols = np.array([k[1] for k in ordered], dtype=np.int32)
    xs = np.array([loc[k][2] for k in ordered], dtype=np.float64)
    ys = np.array([loc[k][3] for k in ordered], dtype=np.float64)
    local_r = np.array([loc[k][0] for k in ordered], dtype=np.int32)
    local_c = np.array([loc[k][1] for k in ordered], dtype=np.int32)
    shape = days[0]["grid_shape"]
    return rain, {
        "cell_row": rows,
        "cell_col": cols,
        "cell_x": xs,
        "cell_y": ys,
        "local_row": local_r,
        "local_col": local_c,
        "grid_shape": shape,
        "crs": days[0]["crs"],
        "native_units": days[0]["native_units"],
    }
