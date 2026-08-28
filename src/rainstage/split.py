# Copyright (c) 2026 Martial Systems LLC
"""Temporal water-year split. Random row splits are banned."""

from __future__ import annotations

import numpy as np

from rainstage.config import HOLDOUT_START, WY2024_END
from rainstage.errors import SplitError

TRAIN_END64 = np.datetime64(WY2024_END.isoformat())
HOLDOUT_START64 = np.datetime64(HOLDOUT_START.isoformat())
AUG2026_START = np.datetime64("2026-08-01")
AUG2026_END = np.datetime64("2026-08-31")


def as_day(dates: np.ndarray) -> np.ndarray:
    return np.asarray(dates).astype("datetime64[D]")


def temporal_masks(dates: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    d = as_day(dates)
    train = d <= TRAIN_END64
    holdout = d >= HOLDOUT_START64
    return train, holdout


def august_2026_mask(dates: np.ndarray) -> np.ndarray:
    d = as_day(dates)
    return (d >= AUG2026_START) & (d <= AUG2026_END)


def assert_temporal(dates: np.ndarray, train: np.ndarray, holdout: np.ndarray) -> None:
    """Refuse overlap, holdout-in-train, August 2026 in train, and shuffled rows."""
    d = as_day(dates)
    train = np.asarray(train, dtype=bool)
    holdout = np.asarray(holdout, dtype=bool)
    if train.shape != d.shape or holdout.shape != d.shape:
        raise SplitError("split masks do not match dates")
    if not train.any():
        raise SplitError("train is empty")
    if not holdout.any():
        raise SplitError("holdout is empty")
    if np.any(train & holdout):
        raise SplitError("train and holdout overlap")
    if np.any(train & august_2026_mask(d)):
        raise SplitError("August 2026 in train")
    if np.any(d[train] >= HOLDOUT_START64):
        raise SplitError("holdout dates in train")
    if d[train].max() >= d[holdout].min():
        raise SplitError("not a temporal split")
