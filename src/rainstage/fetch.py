# Copyright (c) 2026 Martial Systems LLC
"""Live NLDI + NWIS + Stage IV. 404/empty stops. Do not substitute Daymet/PRISM."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from typing import Any, Iterable

import numpy as np

from rainstage.basin import fetch_nldi_basin
from rainstage.config import (
    GAGE_ID,
    LIVE_WINDOWS,
    LOCKED_STAGEIV_CELLSIZE_M,
    LOCKED_STAGEIV_CRS_TOKEN,
    MIN_LIVE_DAYS,
)
from rainstage.errors import FetchError
from rainstage.nwis import fetch_daily
from rainstage.pack import RainPack
from rainstage.stageiv import align_cells, clip_tif, stageiv_url


def iter_days(windows: Iterable[tuple[date, date]] = LIVE_WINDOWS) -> list[date]:
    out: list[date] = []
    seen: set[date] = set()
    for start, end in windows:
        d = start
        while d <= end:
            if d not in seen:
                out.append(d)
                seen.add(d)
            d += timedelta(days=1)
    return out


def _align_nwis(dates: np.ndarray, series: dict[str, dict[np.datetime64, float]]) -> tuple[np.ndarray, np.ndarray]:
    qmap = series["q_cfs"]
    hmap = series["stage_ft"]
    q = np.array([qmap.get(d, np.nan) for d in dates], dtype=float)
    h = np.array([hmap.get(d, np.nan) for d in dates], dtype=float)
    return q, h


def fetch_live(
    *,
    windows: Iterable[tuple[date, date]] = LIVE_WINDOWS,
    get_json_fn=None,
    clip_fn=None,
) -> tuple[RainPack, dict[str, Any]]:
    geojson, basin_meta = fetch_nldi_basin(get_json_fn=get_json_fn)
    days = iter_days(windows)
    if not days:
        raise FetchError("live date windows are empty")
    nwis = fetch_daily(start=days[0], end=days[-1], get_json_fn=get_json_fn)
    stage_source = str(nwis.get("stage_source") or "dv")
    clipper = clip_fn or (lambda url, gj: clip_tif(url, gj))
    got: dict[date, dict[str, Any]] = {}
    skipped: list[dict[str, Any]] = []

    def _one(day: date) -> tuple[date, dict[str, Any]]:
        return day, clipper(stageiv_url(day), geojson)

    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = [pool.submit(_one, d) for d in days]
        done = 0
        for fut in as_completed(futs):
            done += 1
            try:
                day, rec = fut.result()
            except FetchError as exc:
                skipped.append({"error": str(exc)})
                print(f"Stage IV skip {done}/{len(days)}: {exc}", flush=True)
                continue
            got[day] = rec
            if done == 1 or done % 10 == 0 or done == len(days):
                print(f"Stage IV {day.isoformat()} {done}/{len(days)} kept {len(got)}", flush=True)
    kept = [d for d in days if d in got]
    clips = [got[d] for d in kept]
    if len(kept) < MIN_LIVE_DAYS:
        raise FetchError(
            f"Stage IV live days {len(kept)} < {MIN_LIVE_DAYS} "
            f"(skipped {len(skipped)}); empty or 404 stops"
        )
    if clips:
        tr = clips[0].get("transform") or ()
        crs = str(clips[0].get("crs") or "")
        cell = abs(float(tr[0])) if tr else 0.0
        if abs(cell - LOCKED_STAGEIV_CELLSIZE_M) > 1.0:
            raise FetchError(f"Stage IV cell size {cell} m drifted from {LOCKED_STAGEIV_CELLSIZE_M}")
        if LOCKED_STAGEIV_CRS_TOKEN not in crs:
            raise FetchError(f"Stage IV CRS is not {LOCKED_STAGEIV_CRS_TOKEN}: {crs[:80]}")
    rain, cells = align_cells(clips)
    dates = np.array([np.datetime64(d.isoformat()) for d in kept])
    q, stage = _align_nwis(dates, nwis)
    if not np.isfinite(stage).any():
        raise FetchError("NWIS 00065 has no overlap with Stage IV days")
    pack = RainPack(
        dates=dates,
        rain_mm=rain,
        q_cfs=q,
        stage_ft=stage,
        cell_row=cells["cell_row"],
        cell_col=cells["cell_col"],
        cell_x=cells["cell_x"],
        cell_y=cells["cell_y"],
        grid_shape=tuple(cells["grid_shape"]),
        crs=str(cells["crs"]),
        basin_sha=str(basin_meta["sha256"]),
        gage_id=GAGE_ID,
        source="stageiv",
        drainage_mi2=float(basin_meta["area_mi2"]),
        native_rain_units=str(cells["native_units"]),
        extra={
            "n_skipped": len(skipped),
            "skipped": skipped[:12],
            "basin": basin_meta,
            "stage_source": stage_source,
        },
    )
    meta = {
        "basin": basin_meta,
        "n_requested": len(days),
        "n_stageiv": len(kept),
        "n_skipped": len(skipped),
        "rain_units": "mm",
        "stage_units": "ft",
        "q_units": "cfs",
        "native_rain_units": cells["native_units"],
        "crs": cells["crs"],
        "n_cells": pack.n_cells,
        "stage_source": stage_source,
    }
    return pack, meta
