# Copyright (c) 2026 Martial Systems LLC

from pathlib import Path

from rainstage.config import QUESTION
from rainstage.pipeline import stage0_fixture


def test_fixture_two_figures(tmp_path: Path) -> None:
    report = stage0_fixture(tmp_path)
    assert report["question"] == QUESTION
    assert report["p_sfha_feature"] is False
    assert report["p_sfha_label"] is False
    assert report["august_2026_in_train"] is False
    assert (tmp_path / "hydrograph.png").is_file()
    assert (tmp_path / "attribution.png").is_file()
    assert report["figures"] == ["hydrograph.png", "attribution.png"]
    assert report["rain_units"] == "mm"
    assert report["stage_units"] == "ft"
    assert (tmp_path / "stage0_report.json").is_file()
