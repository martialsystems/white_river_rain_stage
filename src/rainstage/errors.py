# Copyright (c) 2026 Martial Systems LLC


class GateError(RuntimeError):
    """Stage hard gate failed."""


class ClaimBanError(GateError):
    """Report text hit a banned claim."""


class FetchError(GateError):
    """Stage IV, NLDI, or NWIS 404/empty, or basin is not NLDI 03351000."""


class SplitError(GateError):
    """Temporal split leaked holdout, August 2026, or a random shuffle."""


class FigureCapError(GateError):
    """This tree stops at two figures."""
