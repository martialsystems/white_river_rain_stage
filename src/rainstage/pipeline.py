# Copyright (c) 2026 Martial Systems LLC
"""Stage 0 fixture. Live fetch-or-stop. Two figures max."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from rainstage.claims import require_clean, require_paths_clean
from rainstage.config import (
    CREST_DATE,
    CREST_STAGE_FT,
    GAGE_ID,
    LIVE_WINDOWS,
    PUBLISHED_DRAINAGE_MI2,
    QUESTION,
)
from rainstage.fetch import fetch_live
from rainstage.figure import write_two
from rainstage.fixture import build_fixture
from rainstage.models import fit_pack

try:
    from rainforge.gate import require_claims, require_fetch_basin, require_no_p_sfha, require_split
except ImportError:  # pragma: no cover

    def require_claims(**kwargs):
        del kwargs

    def require_fetch_basin(**kwargs):
        del kwargs

    def require_no_p_sfha(**kwargs):
        del kwargs

    def require_split(**kwargs):
        del kwargs


def _jsonable(report: dict[str, Any]) -> dict[str, Any]:
    skip = {"holdout", "attribution"}
    out = {k: v for k, v in report.items() if k not in skip}
    attr = report.get("attribution") or {}
    out["attribution"] = {
        k: attr[k]
        for k in ("name", "q_lag_coef", "hotspot_mean_abs_coef", "other_mean_abs_coef")
        if k in attr
    }
    return out


def _run(
    log_dir: Path,
    *,
    pack,
    fixture: bool,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    require_no_p_sfha(thread_id="p_sfha")
    require_clean(QUESTION, source="question")
    fit = fit_pack(pack)
    require_split(
        temporal_ok=True,
        august_2026_in_train=bool(fit["august_2026_in_train"]),
        random_split=bool(fit["random_split"]),
        future_rain=bool(fit["future_rain"]),
        thread_id="split",
    )
    paths = write_two(log_dir, fit=fit)
    require_claims(n_figures=len(paths), thread_id="claims")
    log_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "stage": "0" if fixture else "C",
        "fixture": fixture,
        "question": QUESTION,
        "gage_id": GAGE_ID,
        "crest_date": CREST_DATE,
        "crest_stage_ft": CREST_STAGE_FT,
        "published_drainage_mi2": PUBLISHED_DRAINAGE_MI2,
        "drainage_mi2": pack.drainage_mi2,
        "n_days": pack.n_days,
        "n_cells": pack.n_cells,
        "n_train": fit["n_train"],
        "n_holdout": fit["n_holdout"],
        "rain_units": pack.rain_units,
        "stage_units": pack.stage_units,
        "q_units": pack.q_units,
        "native_rain_units": pack.native_rain_units,
        "basin_sha": pack.basin_sha,
        "source": pack.source,
        "crs": pack.crs,
        "skill": fit["skill"],
        "august_2026_in_train": fit["august_2026_in_train"],
        "random_split": fit["random_split"],
        "future_rain": fit["future_rain"],
        "p_sfha_feature": False,
        "p_sfha_label": False,
        "figures": [p.name for p in paths],
        "attribution": fit["attribution"],
        "holdout": fit["holdout"],
    }
    if extra:
        report.update(extra)
    name = "stage0_report.json" if fixture else "stage_c_report.json"
    payload = _jsonable(report)
    (log_dir / name).write_text(json.dumps(payload, indent=2, default=str) + "\n")
    require_paths_clean([log_dir / name])
    return report


def stage0_fixture(log_dir: Path) -> dict[str, Any]:
    pack = build_fixture()
    return _run(log_dir, pack=pack, fixture=True)


def run_live(
    log_dir: Path,
    *,
    windows: tuple[tuple[date, date], ...] = LIVE_WINDOWS,
) -> dict[str, Any]:
    pack, meta = fetch_live(windows=windows)
    require_fetch_basin(
        stageiv_ok=True,
        nwis_ok=True,
        basin_is_nldi=True,
        basin_is_huc8=False,
        basin_is_hand_window=False,
        thread_id="live.fetch",
    )
    return _run(log_dir, pack=pack, fixture=False, extra={"live": meta})
