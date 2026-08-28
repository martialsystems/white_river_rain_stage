# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

from typing import Any

from rainforge.graphs._common import binary_graph


def _evaluate(state: dict[str, Any]) -> dict[str, Any]:
    v: list[str] = []
    if not state.get("temporal_ok"):
        v.append("not_temporal")
    if state.get("august_2026_in_train"):
        v.append("august_2026_in_train")
    if state.get("random_split"):
        v.append("random_split")
    if state.get("future_rain"):
        v.append("future_rain")
    return {"violations": v, "events": [{"node": "evaluate", "ok": not v}]}


def build_graph():
    return binary_graph(
        name="rain.temporal_split",
        evaluate=_evaluate,
        extra=["temporal_ok", "august_2026_in_train", "random_split", "future_rain"],
    )
