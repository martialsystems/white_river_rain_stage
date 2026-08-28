# Copyright (c) 2026 Martial Systems LLC

import numpy as np
import pytest

from rainstage.errors import GateError
from rainstage.features import _lag, matrix_a
from rainstage.fixture import build_fixture
from rainstage.models import fit_pack
from rainstage.split import TRAIN_END64, august_2026_mask, temporal_masks


def test_negative_lag_is_future_rain() -> None:
    with pytest.raises(GateError, match="future rain"):
        _lag(np.array([1.0, 2.0]), -1)


def test_fixture_skill_and_attribution() -> None:
    pack = build_fixture()
    train, hold = temporal_masks(pack.dates)
    assert not np.any(train & august_2026_mask(pack.dates))
    assert pack.dates[train].max() <= TRAIN_END64
    fit = fit_pack(pack)
    assert fit["n_train"] > 200
    assert fit["n_holdout"] > 200
    assert fit["august_2026_in_train"] is False
    assert fit["random_split"] is False
    a_rmse = fit["skill"]["model_a"]["rmse_ft"]
    clim_rmse = fit["skill"]["climatology"]["rmse_ft"]
    pers_rmse = fit["skill"]["persistence"]["rmse_ft"]
    base_rmse = fit["skill"]["baseline"]["rmse_ft"]
    assert a_rmse < clim_rmse
    assert a_rmse < pers_rmse
    assert a_rmse <= base_rmse * 1.05
    assert fit["skill"]["model_a"]["name"] == "Ridge"
    attr = fit["attribution"]
    assert attr["hotspot_mean_abs_coef"] > attr["other_mean_abs_coef"]
    shifted = build_fixture()
    shifted.cell_row = shifted.cell_row + 80
    shifted.cell_col = shifted.cell_col + 40
    grid = fit_pack(shifted)["attribution"]["grid"]
    assert grid.shape == (8, 10)
    assert np.isfinite(grid).sum() == 80
    xa, y, ok = matrix_a(pack)
    assert xa.shape[1] == 7
    assert "p_sfha" not in str(xa.dtype)
    assert np.isfinite(y[ok]).all()
