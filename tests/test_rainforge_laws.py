# Copyright (c) 2026 Martial Systems LLC

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from rainforge._bootstrap import ensure_paths

ensure_paths()

from graphforge.product_law import LawBlockedError

from rainforge.gate import require_claims, require_fetch_basin, require_no_p_sfha, require_split
from rainforge.product_laws import laws


def test_no_p_sfha() -> None:
    require_no_p_sfha(thread_id="t.p.ok")
    with pytest.raises(LawBlockedError):
        require_no_p_sfha(p_sfha_feature=True, thread_id="t.p.bad")


def test_temporal_split() -> None:
    require_split(thread_id="t.s.ok")
    with pytest.raises(LawBlockedError):
        require_split(random_split=True, thread_id="t.s.rand")
    with pytest.raises(LawBlockedError):
        require_split(august_2026_in_train=True, thread_id="t.s.aug")
    with pytest.raises(LawBlockedError):
        require_split(future_rain=True, thread_id="t.s.future")


def test_fetch_basin() -> None:
    require_fetch_basin(
        stageiv_ok=True,
        nwis_ok=True,
        basin_is_nldi=True,
        thread_id="t.f.ok",
    )
    with pytest.raises(LawBlockedError):
        require_fetch_basin(stageiv_ok=False, nwis_ok=True, basin_is_nldi=True, thread_id="t.f.iv")
    with pytest.raises(LawBlockedError):
        require_fetch_basin(
            stageiv_ok=True,
            nwis_ok=True,
            basin_is_nldi=True,
            basin_is_huc8=True,
            thread_id="t.f.huc",
        )
    with pytest.raises(LawBlockedError):
        require_fetch_basin(
            stageiv_ok=True,
            nwis_ok=True,
            basin_is_nldi=True,
            basin_is_hand_window=True,
            thread_id="t.f.hand",
        )


def test_claims_and_figure_cap() -> None:
    require_claims(n_figures=2, thread_id="t.c.ok")
    with pytest.raises(LawBlockedError):
        require_claims(n_figures=3, thread_id="t.c.fig")
    with pytest.raises(LawBlockedError):
        require_claims(attrib_as_wet_mask=True, thread_id="t.c.wet")
    with pytest.raises(LawBlockedError):
        require_claims(attrib_as_runoff=True, thread_id="t.c.runoff")


def test_registry() -> None:
    assert {row["id"] for row in laws()} == {
        "rain.no_p_sfha",
        "rain.temporal_split",
        "rain.fetch_basin",
        "rain.claim_bans",
    }
