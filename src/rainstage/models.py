# Copyright (c) 2026 Martial Systems LLC
"""Skill model A (Ridge on hydrologic vector), rain+Q baseline, persistence, Ridge B."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from rainstage.errors import SplitError
from rainstage.features import FEATURE_A_NAMES, matrix_a, matrix_b, persistence_yhat
from rainstage.pack import RainPack
from rainstage.split import assert_temporal, temporal_masks


def rmse(y: np.ndarray, yhat: np.ndarray) -> float:
    err = np.asarray(y, dtype=float) - np.asarray(yhat, dtype=float)
    return float(np.sqrt(np.mean(err * err)))


def mae(y: np.ndarray, yhat: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(y, dtype=float) - np.asarray(yhat, dtype=float))))


def _skill(y: np.ndarray, yhat: np.ndarray) -> dict[str, float]:
    return {"rmse_ft": rmse(y, yhat), "mae_ft": mae(y, yhat)}


def fit_pack(pack: RainPack) -> dict[str, Any]:
    """Train through WY2024, score 2025-2026. August 2026 is confirmation, not train."""
    train_all, hold_all = temporal_masks(pack.dates)
    xa, y, ok = matrix_a(pack)
    xb, yb, okb = matrix_b(pack)
    if not np.array_equal(y, yb) or not np.array_equal(ok, okb):
        raise SplitError("model A and B row alignment drifted")
    train = train_all & ok
    hold = hold_all & ok
    assert_temporal(pack.dates, train_all, hold_all)
    if not train.any() or not hold.any():
        raise SplitError("no valid rows in train or holdout after lags")

    y_tr, y_ho = y[train], y[hold]
    xa_tr, xa_ho = xa[train], xa[hold]
    xb_tr, xb_ho = xb[train], xb[hold]

    model_a = Pipeline(
        [
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=1.0)),
        ]
    )
    model_a.fit(xa_tr, y_tr)
    yhat_a = model_a.predict(xa_ho)

    baseline = Pipeline(
        [
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=1.0)),
        ]
    )
    rain_sum_tr = xa_tr[:, :4].sum(axis=1, keepdims=True)
    rain_sum_ho = xa_ho[:, :4].sum(axis=1, keepdims=True)
    q_tr = xa_tr[:, 4:5]
    q_ho = xa_ho[:, 4:5]
    baseline.fit(np.hstack([rain_sum_tr, q_tr]), y_tr)
    yhat_base = baseline.predict(np.hstack([rain_sum_ho, q_ho]))

    pers = persistence_yhat(pack)
    yhat_pers = pers[hold]
    yhat_clim = np.full_like(y_ho, float(y_tr.mean()))

    model_b = Pipeline(
        [
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=5.0)),
        ]
    )
    model_b.fit(xb_tr, y_tr)
    ridge: Ridge = model_b.named_steps["ridge"]
    scale: StandardScaler = model_b.named_steps["scale"]
    coef = ridge.coef_.astype(float)
    # Undo feature scaling so coefficients are per original mm / cfs.
    scale_ok = np.asarray(scale.scale_, dtype=float)
    scale_ok = np.where(scale_ok == 0.0, 1.0, scale_ok)
    coef_native = coef / scale_ok
    cell_coef = coef_native[:-1]
    abs_coef = np.abs(cell_coef)

    r0 = int(np.min(pack.cell_row))
    c0 = int(np.min(pack.cell_col))
    shape = (int(np.max(pack.cell_row)) - r0 + 1, int(np.max(pack.cell_col)) - c0 + 1)
    grid = np.full(shape, np.nan, dtype=float)
    overlay = np.full(shape, np.nan, dtype=float)
    for i, (r, c) in enumerate(zip(pack.cell_row, pack.cell_col)):
        grid[int(r) - r0, int(c) - c0] = abs_coef[i]
    crest = np.datetime64("2026-08-15")
    crest_idx = np.where(pack.dates.astype("datetime64[D]") == crest)[0]
    if crest_idx.size:
        rain15 = np.asarray(pack.rain_mm[int(crest_idx[0])], dtype=float)
        prod = abs_coef * rain15
        for i, (r, c) in enumerate(zip(pack.cell_row, pack.cell_col)):
            overlay[int(r) - r0, int(c) - c0] = prod[i]

    out: dict[str, Any] = {
        "n_train": int(train.sum()),
        "n_holdout": int(hold.sum()),
        "feature_a_names": list(FEATURE_A_NAMES),
        "skill": {
            "persistence": _skill(y_ho, yhat_pers),
            "climatology": _skill(y_ho, yhat_clim),
            "baseline": _skill(y_ho, yhat_base),
            "model_a": {**_skill(y_ho, yhat_a), "name": "Ridge"},
        },
        "holdout": {
            "dates": pack.dates[hold],
            "observed_ft": y_ho,
            "persistence_ft": yhat_pers,
            "baseline_ft": yhat_base,
            "model_a_ft": yhat_a,
        },
        "attribution": {
            "name": "Ridge",
            "abs_coef": abs_coef,
            "grid": grid,
            "crest_overlay": overlay,
            "q_lag_coef": float(coef_native[-1]),
        },
        "august_2026_in_train": False,
        "random_split": False,
        "future_rain": False,
    }
    if pack.hotspot is not None:
        hot = np.asarray(pack.hotspot, dtype=bool)
        other = ~hot
        out["attribution"]["hotspot_mean_abs_coef"] = float(abs_coef[hot].mean())
        out["attribution"]["other_mean_abs_coef"] = float(abs_coef[other].mean())
    return out
