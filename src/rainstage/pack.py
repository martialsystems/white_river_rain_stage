# Copyright (c) 2026 Martial Systems LLC
"""Daily rain cube plus Q and stage. One gage, one basin."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class RainPack:
    """Aligned daily arrays. rain_mm is (n_days, n_cells), clipped to the basin."""

    dates: np.ndarray
    rain_mm: np.ndarray
    q_cfs: np.ndarray
    stage_ft: np.ndarray
    cell_row: np.ndarray
    cell_col: np.ndarray
    cell_x: np.ndarray
    cell_y: np.ndarray
    grid_shape: tuple[int, int]
    crs: str
    rain_units: str = "mm"
    q_units: str = "cfs"
    stage_units: str = "ft"
    basin_sha: str = ""
    gage_id: str = "03351000"
    source: str = "fixture"
    drainage_mi2: float | None = None
    hotspot: np.ndarray | None = None
    native_rain_units: str = "mm"
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def n_days(self) -> int:
        return int(self.dates.shape[0])

    @property
    def n_cells(self) -> int:
        return int(self.rain_mm.shape[1])
