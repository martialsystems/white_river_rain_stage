# Copyright (c) 2026 Martial Systems LLC

from datetime import date

import numpy as np
import pytest

from rainstage.basin import fetch_nldi_basin, require_nldi_basin
from rainstage.config import GAGE_ID, LOCKED_NLDI_BASIN_SHA256, MIN_LIVE_DAYS
from rainstage.errors import FetchError, FigureCapError
from rainstage.fetch import fetch_live, iter_days
from rainstage.figure import _cap
from rainstage.nwis import _daily_max, _points, _series
from rainstage.stageiv import align_cells, stageiv_url


def _square(lon0: float, lat0: float, dlon: float, dlat: float) -> dict:
    ring = [
        [lon0, lat0],
        [lon0 + dlon, lat0],
        [lon0 + dlon, lat0 + dlat],
        [lon0, lat0 + dlat],
        [lon0, lat0],
    ]
    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [ring]}}],
    }


def test_huc8_and_hand_window_refused() -> None:
    gj = _square(-86.2, 39.8, 0.02, 0.02)
    with pytest.raises(FetchError, match="HUC-8"):
        require_nldi_basin(gj, source="huc8", gage_id=GAGE_ID)
    with pytest.raises(FetchError, match="HAND"):
        require_nldi_basin(gj, source="hand_window", gage_id=GAGE_ID)


def test_tiny_polygon_is_not_1219() -> None:
    gj = _square(-86.2, 39.8, 0.02, 0.02)
    with pytest.raises(FetchError, match="1,219"):
        require_nldi_basin(gj, source="nldi", gage_id=GAGE_ID)


def test_published_drainage_accepted() -> None:
    pytest.importorskip("pyproj")
    from rainstage.basin import area_mi2

    gj0 = _square(-86.70, 39.55, 0.60, 0.50)
    scale = (1219.0 / area_mi2(gj0)) ** 0.5
    gj = _square(-86.70, 39.55, 0.60 * scale, 0.50 * scale)
    area = area_mi2(gj)
    assert 1219 * 0.85 < area < 1219 * 1.15
    meta = require_nldi_basin(gj, source="nldi", gage_id=GAGE_ID)
    assert meta["source"] == "nldi"
    assert meta["sha256"]
    with pytest.raises(FetchError, match="sha"):
        fetch_nldi_basin(get_json_fn=lambda url: gj)


def test_nwis_parse_and_skip_ice() -> None:
    doc = {
        "value": {
            "timeSeries": [
                {
                    "variable": {"variableCode": [{"value": "00065"}]},
                    "values": [
                        {
                            "value": [
                                {"dateTime": "2024-07-01T00:00:00.000-04:00", "value": "4.2"},
                                {"dateTime": "2024-07-02T00:00:00.000-04:00", "value": "Ice"},
                            ]
                        }
                    ],
                }
            ]
        }
    }
    series = _series(doc, code="00065")
    assert series[np.datetime64("2024-07-01")] == 4.2
    assert np.datetime64("2024-07-02") not in series
    iv = {
        "value": {
            "timeSeries": [
                {
                    "variable": {"variableCode": [{"value": "00065"}]},
                    "values": [
                        {
                            "value": [
                                {"dateTime": "2026-08-15T00:00:00.000-04:00", "value": "10.0"},
                                {"dateTime": "2026-08-15T12:00:00.000-04:00", "value": "21.18"},
                                {"dateTime": "2026-08-16T01:00:00.000-04:00", "value": "8.0"},
                            ]
                        }
                    ],
                }
            ]
        }
    }
    mx = _daily_max(_points(iv, code="00065"))
    assert mx[np.datetime64("2026-08-15")] == 21.18
    assert mx[np.datetime64("2026-08-16")] == 8.0


def test_stageiv_url() -> None:
    url = stageiv_url(date(2026, 8, 15))
    assert "2026/08/15" in url
    assert "nws_precip_1day_20260815_conus.tif" in url


def test_align_cells_intersection() -> None:
    d1 = {
        "rain_mm": np.array([1.0, 2.0], dtype=np.float32),
        "cell_row": np.array([0, 1]),
        "cell_col": np.array([0, 0]),
        "local_row": np.array([0, 1]),
        "local_col": np.array([0, 0]),
        "cell_x": np.array([0.0, 0.0]),
        "cell_y": np.array([0.0, 1.0]),
        "grid_shape": (2, 1),
        "crs": "EPSG:4326",
        "native_units": "inches",
    }
    d2 = {
        "rain_mm": np.array([3.0, 4.0], dtype=np.float32),
        "cell_row": np.array([1, 2]),
        "cell_col": np.array([0, 0]),
        "local_row": np.array([1, 2]),
        "local_col": np.array([0, 0]),
        "cell_x": np.array([0.0, 0.0]),
        "cell_y": np.array([1.0, 2.0]),
        "grid_shape": (2, 1),
        "crs": "EPSG:4326",
        "native_units": "inches",
    }
    rain, cells = align_cells([d1, d2])
    assert rain.shape == (2, 1)
    assert cells["cell_row"].tolist() == [1]


def test_figure_cap() -> None:
    _cap(2)
    with pytest.raises(FigureCapError):
        _cap(3)


def test_live_stageiv_404_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(url: str, gj: dict):
        del url, gj
        raise FetchError("GET empty or 404: stageiv")

    def fake_nldi(get_json_fn=None):
        del get_json_fn
        return _square(-86.5, 39.5, 1.0, 1.0), {
            "sha256": "abc",
            "area_mi2": 1219.0,
            "source": "nldi",
            "gage_id": GAGE_ID,
        }

    def fake_daily(*, start, end, get_json_fn=None):
        del start, end, get_json_fn
        return {"q_cfs": {np.datetime64("2024-07-01"): 100.0}, "stage_ft": {np.datetime64("2024-07-01"): 4.0}}

    monkeypatch.setattr("rainstage.fetch.fetch_nldi_basin", fake_nldi)
    monkeypatch.setattr("rainstage.fetch.fetch_daily", fake_daily)
    with pytest.raises(FetchError, match="empty or 404"):
        fetch_live(
            windows=((date(2024, 7, 1), date(2024, 7, 1)),),
            clip_fn=boom,
        )


def test_iter_days_dedupes() -> None:
    days = iter_days(((date(2024, 7, 1), date(2024, 7, 2)), (date(2024, 7, 2), date(2024, 7, 3))))
    assert days == [date(2024, 7, 1), date(2024, 7, 2), date(2024, 7, 3)]
    assert MIN_LIVE_DAYS >= 30
    assert len(LOCKED_NLDI_BASIN_SHA256) == 64
