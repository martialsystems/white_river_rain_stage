# Copyright (c) 2026 Martial Systems LLC
"""Hydrologic vectors. Rain lags 0..3, last-day Q, day-of-year. No p_sfha."""

from __future__ import annotations

import numpy as np

from rainstage.config import Q_LAG_DAYS, RAIN_LAGS
from rainstage.errors import GateError
from rainstage.pack import RainPack

FEATURE_A_NAMES = (
    "rain_lag0_mm",
    "rain_lag1_mm",
    "rain_lag2_mm",
    "rain_lag3_mm",
    "q_lag1_cfs",
    "doy_sin",
    "doy_cos",
)


def _lag(arr: np.ndarray, k: int) -> np.ndarray:
    out = np.full(arr.shape, np.nan, dtype=float)
    src = np.asarray(arr, dtype=float)
    if k < 0:
        raise GateError("negative rain lag is future rain")
    if k == 0:
        return src.copy()
    out[k:] = src[:-k]
    return out


def basin_mean_rain(pack: RainPack) -> np.ndarray:
    return np.asarray(pack.rain_mm, dtype=float).mean(axis=1)


def doy_trig(dates: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    d = np.asarray(dates).astype("datetime64[D]")
    y = d.astype("datetime64[Y]")
    doy = (d - y).astype("timedelta64[D]").astype(int) + 1
    ang = 2.0 * np.pi * doy / 365.25
    return np.sin(ang), np.cos(ang)


def valid_row_mask(pack: RainPack) -> np.ndarray:
    mean_rain = basin_mean_rain(pack)
    q = np.asarray(pack.q_cfs, dtype=float)
    y = np.asarray(pack.stage_ft, dtype=float)
    ok = np.isfinite(y) & np.isfinite(q)
    for k in RAIN_LAGS:
        ok &= np.isfinite(_lag(mean_rain, k))
    ok &= np.isfinite(_lag(q, Q_LAG_DAYS))
    return ok


def matrix_a(pack: RainPack) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return X (n, 7), y stage ft, row mask. Same-day rain is a nowcast, not QPF."""
    mean_rain = basin_mean_rain(pack)
    q = np.asarray(pack.q_cfs, dtype=float)
    y = np.asarray(pack.stage_ft, dtype=float)
    s, c = doy_trig(pack.dates)
    cols = [_lag(mean_rain, k) for k in RAIN_LAGS]
    cols.append(_lag(q, Q_LAG_DAYS))
    cols.extend([s, c])
    x = np.column_stack(cols)
    ok = valid_row_mask(pack)
    return x, y, ok


def matrix_b(pack: RainPack) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Cell 24 h rain plus last-day Q. Attribution model, not a wet mask."""
    rain = np.asarray(pack.rain_mm, dtype=float)
    q_lag = _lag(np.asarray(pack.q_cfs, dtype=float), Q_LAG_DAYS)
    y = np.asarray(pack.stage_ft, dtype=float)
    x = np.column_stack([rain, q_lag])
    ok = valid_row_mask(pack)
    return x, y, ok


def persistence_yhat(pack: RainPack) -> np.ndarray:
    return _lag(np.asarray(pack.stage_ft, dtype=float), 1)
