# Copyright (c) 2026 Martial Systems LLC
"""Four refuse laws. Verify-before-done is the finish gate."""

from __future__ import annotations

from typing import Any


def laws() -> list[dict[str, Any]]:
    from rainforge.graphs.claim_bans import build_graph as claim_bans
    from rainforge.graphs.fetch_basin import build_graph as fetch_basin
    from rainforge.graphs.no_p_sfha import build_graph as no_p_sfha
    from rainforge.graphs.temporal_split import build_graph as temporal_split

    return [
        {
            "id": "rain.no_p_sfha",
            "build": no_p_sfha,
            "state": {
                "p_sfha_feature": False,
                "p_sfha_label": False,
                "p_sfha_figure": False,
                "p_sfha_import": False,
            },
            "allow_decisions": ["allow"],
        },
        {
            "id": "rain.temporal_split",
            "build": temporal_split,
            "state": {
                "temporal_ok": True,
                "august_2026_in_train": False,
                "random_split": False,
                "future_rain": False,
            },
            "allow_decisions": ["allow"],
        },
        {
            "id": "rain.fetch_basin",
            "build": fetch_basin,
            "state": {
                "stageiv_ok": True,
                "nwis_ok": True,
                "basin_is_nldi": True,
                "basin_is_huc8": False,
                "basin_is_hand_window": False,
            },
            "allow_decisions": ["allow"],
        },
        {
            "id": "rain.claim_bans",
            "build": claim_bans,
            "state": {
                "attrib_as_wet_mask": False,
                "attrib_as_firm": False,
                "flood_warning": False,
                "n_figures": 2,
            },
            "allow_decisions": ["allow"],
        },
    ]
