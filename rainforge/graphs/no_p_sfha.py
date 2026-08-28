# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

from typing import Any

from rainforge.graphs._common import binary_graph

_FLAGS = ("p_sfha_feature", "p_sfha_label", "p_sfha_figure", "p_sfha_import")


def _evaluate(state: dict[str, Any]) -> dict[str, Any]:
    v = [k for k in _FLAGS if state.get(k)]
    return {"violations": v, "events": [{"node": "evaluate", "ok": not v}]}


def build_graph():
    return binary_graph(name="rain.no_p_sfha", evaluate=_evaluate, extra=list(_FLAGS))
