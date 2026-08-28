# Copyright (c) 2026 Martial Systems LLC
"""Call sites for refuse laws."""

from __future__ import annotations

from typing import Any

from rainforge._bootstrap import ensure_paths

ensure_paths()

from graphforge.product_law import require_law

from rainforge.graphs.claim_bans import build_graph as build_claims
from rainforge.graphs.fetch_basin import build_graph as build_fetch
from rainforge.graphs.no_p_sfha import build_graph as build_p
from rainforge.graphs.temporal_split import build_graph as build_split


def require_no_p_sfha(**flags: Any) -> None:
    thread_id = str(flags.pop("thread_id", "rain_p"))
    state = {
        "p_sfha_feature": False,
        "p_sfha_label": False,
        "p_sfha_figure": False,
        "p_sfha_import": False,
    }
    state.update(flags)
    require_law(
        build_p(),
        state,
        allow_decisions=["allow"],
        law_id="rain.no_p_sfha",
        thread_id=thread_id,
        raise_error=True,
    )


def require_split(**flags: Any) -> None:
    thread_id = str(flags.pop("thread_id", "rain_split"))
    state = {
        "temporal_ok": True,
        "august_2026_in_train": False,
        "random_split": False,
        "future_rain": False,
    }
    state.update(flags)
    require_law(
        build_split(),
        state,
        allow_decisions=["allow"],
        law_id="rain.temporal_split",
        thread_id=thread_id,
        raise_error=True,
    )


def require_fetch_basin(**flags: Any) -> None:
    thread_id = str(flags.pop("thread_id", "rain_fetch"))
    state = {
        "stageiv_ok": False,
        "nwis_ok": False,
        "basin_is_nldi": False,
        "basin_is_huc8": False,
        "basin_is_hand_window": False,
    }
    state.update(flags)
    require_law(
        build_fetch(),
        state,
        allow_decisions=["allow"],
        law_id="rain.fetch_basin",
        thread_id=thread_id,
        raise_error=True,
    )


def require_claims(**flags: Any) -> None:
    thread_id = str(flags.pop("thread_id", "rain_claims"))
    state = {
        "attrib_as_wet_mask": False,
        "attrib_as_firm": False,
        "flood_warning": False,
        "attrib_as_runoff": False,
        "n_figures": 2,
    }
    state.update(flags)
    require_law(
        build_claims(),
        state,
        allow_decisions=["allow"],
        law_id="rain.claim_bans",
        thread_id=thread_id,
        raise_error=True,
    )
