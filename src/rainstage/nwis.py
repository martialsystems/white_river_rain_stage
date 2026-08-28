# Copyright (c) 2026 Martial Systems LLC
"""NWIS discharge 00060 (daily) and gage height 00065 (daily, else daily max of IV)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Callable

import numpy as np

from rainstage.config import GAGE_ID, NWIS_DV_URL
from rainstage.errors import FetchError
from rainstage.http import get_json

NWIS_IV_URL = (
    "https://waterservices.usgs.gov/nwis/iv/?format=json&sites={site}"
    "&startDT={start}&endDT={end}&parameterCd={code}&siteStatus=all"
)
IV_CHUNK_DAYS = 60


def _time_series(doc: dict[str, Any]) -> list[dict[str, Any]]:
    blob = doc.get("value") if isinstance(doc.get("value"), dict) else doc
    return list((blob or {}).get("timeSeries") or [])


def _points(doc: dict[str, Any], *, code: str) -> list[tuple[np.datetime64, float]]:
    out: list[tuple[np.datetime64, float]] = []
    for ts in _time_series(doc):
        var = ((ts.get("variable") or {}).get("variableCode") or [{}])[0]
        if str(var.get("value") or "") != code:
            continue
        rows = ((ts.get("values") or [{}])[0]).get("value") or []
        for rec in rows:
            raw = rec.get("value")
            stamp = str(rec.get("dateTime") or "")[:10]
            if not stamp:
                continue
            try:
                val = float(raw)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(val):
                continue
            out.append((np.datetime64(stamp), val))
    return out


def _series(doc: dict[str, Any], *, code: str) -> dict[np.datetime64, float]:
    """Last value per calendar day (DV has one row per day)."""
    out: dict[np.datetime64, float] = {}
    for day, val in _points(doc, code=code):
        out[day] = val
    return out


def _daily_max(points: list[tuple[np.datetime64, float]]) -> dict[np.datetime64, float]:
    out: dict[np.datetime64, float] = {}
    for day, val in points:
        prev = out.get(day)
        out[day] = val if prev is None or val > prev else prev
    return out


def _chunks(start: date, end: date, *, width: int = IV_CHUNK_DAYS) -> list[tuple[date, date]]:
    out: list[tuple[date, date]] = []
    cur = start
    while cur <= end:
        stop = min(end, cur + timedelta(days=width - 1))
        out.append((cur, stop))
        cur = stop + timedelta(days=1)
    return out


def fetch_stage_iv_daily_max(
    *,
    start: date,
    end: date,
    site: str = GAGE_ID,
    get_json_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[np.datetime64, float]:
    getter = get_json_fn or get_json
    points: list[tuple[np.datetime64, float]] = []
    for a, b in _chunks(start, end):
        doc = getter(NWIS_IV_URL.format(site=site, start=a.isoformat(), end=b.isoformat(), code="00065"))
        points.extend(_points(doc, code="00065"))
    stage = _daily_max(points)
    if not stage:
        raise FetchError("NWIS IV 00065 is empty")
    return stage


def fetch_daily(
    *,
    start: date,
    end: date,
    site: str = GAGE_ID,
    get_json_fn=None,
) -> dict[str, dict[np.datetime64, float]]:
    getter = get_json_fn or get_json
    q_doc = getter(NWIS_DV_URL.format(site=site, start=start.isoformat(), end=end.isoformat(), code="00060"))
    q = _series(q_doc, code="00060")
    if not q:
        raise FetchError("NWIS daily 00060 is empty")
    h_doc = getter(NWIS_DV_URL.format(site=site, start=start.isoformat(), end=end.isoformat(), code="00065"))
    h = _series(h_doc, code="00065")
    stage_source = "dv"
    if not h:
        h = fetch_stage_iv_daily_max(start=start, end=end, site=site, get_json_fn=getter)
        stage_source = "iv_daily_max"
    return {"q_cfs": q, "stage_ft": h, "stage_source": stage_source}
