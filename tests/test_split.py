# Copyright (c) 2026 Martial Systems LLC

import numpy as np
import pytest

from rainstage.errors import SplitError
from rainstage.split import assert_temporal, temporal_masks


def test_wy2024_then_holdout() -> None:
    dates = np.array(
        [
            np.datetime64("2024-09-30"),
            np.datetime64("2024-10-01"),
            np.datetime64("2026-08-15"),
        ]
    )
    train, hold = temporal_masks(dates)
    assert train.tolist() == [True, False, False]
    assert hold.tolist() == [False, True, True]
    assert_temporal(dates, train, hold)


def test_august_2026_in_train_refused() -> None:
    dates = np.array([np.datetime64("2026-08-15"), np.datetime64("2026-08-16")])
    train = np.array([True, False])
    hold = np.array([False, True])
    with pytest.raises(SplitError, match="August 2026"):
        assert_temporal(dates, train, hold)


def test_random_split_refused() -> None:
    dates = np.array([np.datetime64("2024-01-01"), np.datetime64("2023-06-01")])
    train = np.array([True, False])
    hold = np.array([False, True])
    with pytest.raises(SplitError, match="not a temporal"):
        assert_temporal(dates, train, hold)
