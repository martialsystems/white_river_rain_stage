# Copyright (c) 2026 Martial Systems LLC
"""Tiny basin and fake Stage IV so CI trains without NOAA."""

from __future__ import annotations

import hashlib

import numpy as np

from rainstage.config import (
    CREST_DATE,
    FIXTURE_COLS,
    FIXTURE_END,
    FIXTURE_HOTSPOT_COLS,
    FIXTURE_HOTSPOT_ROWS,
    FIXTURE_ROWS,
    FIXTURE_START,
    GAGE_ID,
)
from rainstage.pack import RainPack


def _dates() -> np.ndarray:
    n = (FIXTURE_END - FIXTURE_START).days + 1
    return np.arange(
        np.datetime64(FIXTURE_START.isoformat()),
        np.datetime64(FIXTURE_END.isoformat()) + np.timedelta64(1, "D"),
    )


def hotspot_mask() -> np.ndarray:
    mask = np.zeros((FIXTURE_ROWS, FIXTURE_COLS), dtype=bool)
    mask[:FIXTURE_HOTSPOT_ROWS, :FIXTURE_HOTSPOT_COLS] = True
    return mask


def build_fixture(*, seed: int = 7) -> RainPack:
    """Synthetic nowcast: upstream hotspot rain plus Q_lag drive stage."""
    rng = np.random.default_rng(seed)
    dates = _dates()
    n = dates.shape[0]
    rows, cols = FIXTURE_ROWS, FIXTURE_COLS
    hot = hotspot_mask().reshape(-1)
    n_cells = rows * cols

    y = dates.astype("datetime64[Y]")
    doy = (dates - y).astype("timedelta64[D]").astype(int) + 1
    seasonal = 0.55 + 0.45 * np.sin(2 * np.pi * (doy - 80) / 365.25)
    background = rng.gamma(0.45, 6.0, size=(n, n_cells)) * seasonal[:, None]
    bursts = rng.random((n, n_cells)) < 0.06
    background = background + bursts * rng.gamma(2.0, 12.0, size=(n, n_cells))
    extra = rng.gamma(0.8, 10.0, size=(n, n_cells))
    rain = background.copy()
    rain[:, hot] = rain[:, hot] + extra[:, hot]

    crest = np.datetime64(CREST_DATE)
    for delta, mm in ((-3, 10.0), (-2, 18.0), (-1, 28.0), (0, 38.0), (1, 16.0)):
        idx = int(np.searchsorted(dates, crest + np.timedelta64(delta, "D")))
        if 0 <= idx < n:
            rain[idx, :] += 8.0
            rain[idx, hot] += mm

    mean_rain = rain.mean(axis=1)
    hot_rain = rain[:, hot].mean(axis=1)
    q = np.zeros(n, dtype=float)
    q[0] = 400.0
    for t in range(1, n):
        q[t] = 0.70 * q[t - 1] + 20.0 * mean_rain[t] + 40.0 * hot_rain[t] + rng.normal(0.0, 6.0)
        q[t] = max(80.0, q[t])

    stage = np.zeros(n, dtype=float)
    stage[0] = 4.2
    for t in range(1, n):
        rain3 = mean_rain[max(0, t - 3) : t + 1].mean()
        stage[t] = (
            3.4
            + 0.38 * (stage[t - 1] - 3.4)
            + 0.070 * rain3
            + 0.125 * hot_rain[t]
            + 0.00045 * q[t - 1]
            + 0.28 * np.sin(2 * np.pi * doy[t] / 365.25)
            + rng.normal(0.0, 0.08)
        )
        stage[t] = max(2.4, stage[t])

    rr, cc = np.meshgrid(np.arange(rows), np.arange(cols), indexing="ij")
    sha = hashlib.sha256(hot.tobytes() + rain[:8].tobytes()).hexdigest()
    return RainPack(
        dates=dates,
        rain_mm=rain.astype(np.float32),
        q_cfs=q.astype(np.float64),
        stage_ft=stage.astype(np.float64),
        cell_row=rr.reshape(-1).astype(np.int32),
        cell_col=cc.reshape(-1).astype(np.int32),
        cell_x=(cc.reshape(-1) + 0.5).astype(np.float64),
        cell_y=(rr.reshape(-1) + 0.5).astype(np.float64),
        grid_shape=(rows, cols),
        crs="fixture-grid",
        basin_sha=sha,
        gage_id=GAGE_ID,
        source="fixture",
        drainage_mi2=None,
        hotspot=hot,
        native_rain_units="mm",
        extra={"n_hotspot": int(hot.sum())},
    )
