# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

from typing import Any

from rainforge.graphs._common import binary_graph


def _evaluate(state: dict[str, Any]) -> dict[str, Any]:
    v: list[str] = []
    if not state.get("stageiv_ok"):
        v.append("stageiv_empty_or_404")
    if not state.get("nwis_ok"):
        v.append("nwis_empty")
    if not state.get("basin_is_nldi"):
        v.append("basin_not_nldi")
    if state.get("basin_is_huc8"):
        v.append("huc8_clip")
    if state.get("basin_is_hand_window"):
        v.append("hand_window_clip")
    return {"violations": v, "events": [{"node": "evaluate", "ok": not v}]}


def build_graph():
    return binary_graph(
        name="rain.fetch_basin",
        evaluate=_evaluate,
        extra=["stageiv_ok", "nwis_ok", "basin_is_nldi", "basin_is_huc8", "basin_is_hand_window"],
    )
