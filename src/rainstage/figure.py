# Copyright (c) 2026 Martial Systems LLC
"""Two figures: holdout hydrograph, then Stage IV pixel attribution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from rainstage.claims import require_clean
from rainstage.config import CREST_STAGE_FT, FLOOD_STAGE_FT, GAGE_ID, MAX_FIGURES
from rainstage.errors import FigureCapError


def _cap(n: int) -> None:
    if n > MAX_FIGURES:
        raise FigureCapError(f"this tree stops at {MAX_FIGURES} figures")


def write_hydrograph(dest: Path, *, fit: dict[str, Any], title: str, subtitle: str) -> Path:
    require_clean(title, source="fig1_title")
    require_clean(subtitle, source="fig1_sub")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    ho = fit["holdout"]
    d_raw = np.asarray(ho["dates"]).astype("datetime64[D]")
    y_obs = np.asarray(ho["observed_ft"], dtype=float)
    y_pers = np.asarray(ho["persistence_ft"], dtype=float)
    y_a = np.asarray(ho["model_a_ft"], dtype=float)
    from datetime import datetime

    dates = np.array([datetime.strptime(str(x)[:10], "%Y-%m-%d") for x in d_raw])
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    cuts = [0]
    if d_raw.size > 1:
        cuts.extend(list(np.where(np.diff(d_raw) > np.timedelta64(1, "D"))[0] + 1))
    cuts.append(len(dates))
    for j, (a, b) in enumerate(zip(cuts[:-1], cuts[1:])):
        lab = j == 0
        ax.plot(dates[a:b], y_obs[a:b], color="#222222", lw=1.6, label="observed stage" if lab else None)
        ax.plot(dates[a:b], y_pers[a:b], color="#7a7a7a", lw=1.0, ls="--", label="persistence" if lab else None)
        ax.plot(dates[a:b], y_a[a:b], color="#1b6ca8", lw=1.3, label="model A" if lab else None)
    ax.axhline(FLOOD_STAGE_FT, color="#b36b00", lw=0.9, ls=":", label=f"{FLOOD_STAGE_FT:.2f} ft flood stage")
    ax.axhline(CREST_STAGE_FT, color="#9b1b30", lw=0.9, ls=":", label=f"{CREST_STAGE_FT:.2f} ft 2026-08-15")
    ax.axvspan(
        np.datetime64("2026-08-01").astype(object),
        np.datetime64("2026-08-20").astype(object),
        color="#9b1b30",
        alpha=0.08,
        label="August 2026",
    )
    ax.set_ylabel("gage height (ft)")
    ax.set_title(title, fontsize=10)
    ax.legend(loc="upper left", fontsize=7, frameon=False, ncol=2)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.text(0.5, 0.02, subtitle, ha="center", fontsize=8)
    fig.subplots_adjust(bottom=0.16, top=0.88, left=0.10, right=0.98)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest, dpi=130)
    plt.close(fig)
    return dest


def write_attribution(dest: Path, *, fit: dict[str, Any], title: str, subtitle: str) -> Path:
    require_clean(title, source="fig2_title")
    require_clean(subtitle, source="fig2_sub")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    grid = np.asarray(fit["attribution"]["grid"], dtype=float)
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    im = ax.imshow(grid, origin="upper", cmap="YlOrRd")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("mean |Ridge coef| (ft / mm)", fontsize=8)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=10)
    fig.text(0.5, 0.03, subtitle, ha="center", fontsize=8)
    fig.subplots_adjust(bottom=0.10, top=0.90)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest, dpi=130)
    plt.close(fig)
    return dest


def write_two(log_dir: Path, *, fit: dict[str, Any]) -> list[Path]:
    paths = [
        write_hydrograph(
            log_dir / "hydrograph.png",
            fit=fit,
            title=f"{GAGE_ID} holdout hydrograph: rain-to-stage nowcast",
            subtitle="Observed, persistence, model A. Lines at 11.00 ft and 21.18 ft. August 2026 shaded.",
        ),
        write_attribution(
            log_dir / "attribution.png",
            fit=fit,
            title=f"{GAGE_ID} Stage IV pixels: holdout |coefficient|",
            subtitle="Upstream rain the model uses, not a wet mask.",
        ),
    ]
    _cap(len(paths))
    return paths
