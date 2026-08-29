# Copyright (c) 2026 Martial Systems LLC
"""Locked Nora rain-to-stage contract. Does not read p_sfha."""

from __future__ import annotations

from datetime import date

GAGE_ID = "03351000"
GAGE_NWS_ID = "NORI3"
PUBLISHED_DRAINAGE_MI2 = 1219.0
DRAINAGE_TOLERANCE = 0.15
FLOOD_STAGE_FT = 11.00
CREST_STAGE_FT = 21.18
CREST_DATE = "2026-08-15"
WY2024_END = date(2024, 9, 30)
HOLDOUT_START = date(2024, 10, 1)
RAIN_LAGS = (0, 1, 2, 3)
Q_LAG_DAYS = 1
MAX_FIGURES = 2
QUESTION = "Does rain on the Nora basin help you guess tomorrow's stage?"
USER_AGENT = "MartialSystemsResearch/white_river_rain_stage"
NLDI_BASIN_URL = (
    "https://api.water.usgs.gov/nldi/linked-data/nwissite/USGS-03351000/basin?f=json"
)
LOCKED_NLDI_BASIN_SHA256 = "944566fd7828b63d4975dbeea69152c9c339ce11c71e668c01437d82f85f13a3"
LOCKED_NLDI_AREA_MI2 = 1227.28
LOCKED_STAGEIV_CELLSIZE_M = 4762.5
LOCKED_STAGEIV_CRS_TOKEN = "NOAA_HRAP_Grid"
LOCKED_LIVE_COMMIT = "e41fd69602046683818dd33b28ddc07029d8c605"
LIVE_ATTRIBUTION_SUBTITLE = (
    "Where Ridge looks, not source areas for the flood. "
    "A model that loses to persistence should not be read as a runoff map."
)
FIXTURE_ATTRIBUTION_SUBTITLE = (
    "Fixture: which cells the synthetic Ridge uses. Does not rescue live skill."
)
NWIS_DV_URL = (
    "https://waterservices.usgs.gov/nwis/dv/?format=json&sites={site}"
    "&startDT={start}&endDT={end}&parameterCd={code}&siteStatus=all"
)
STAGEIV_URL = (
    "https://water.noaa.gov/resources/downloads/precip/stageIV/"
    "{y:04d}/{m:02d}/{d:02d}/nws_precip_1day_{stamp}_conus.tif"
)
HUC8_REFUSED = "05120201"
MI2_PER_M2 = 1.0 / 2_589_988.110336
# Live windows: late WY2024 train, then holdout summers including August 2026.
LIVE_WINDOWS = (
    (date(2024, 7, 1), date(2024, 9, 30)),
    (date(2025, 7, 1), date(2025, 9, 30)),
    (date(2026, 7, 1), date(2026, 8, 20)),
)
MIN_LIVE_DAYS = 30
STAGEIV_INCH_TO_MM = 25.4
FIXTURE_ROWS = 8
FIXTURE_COLS = 10
FIXTURE_HOTSPOT_ROWS = 3
FIXTURE_HOTSPOT_COLS = 4
FIXTURE_START = date(2023, 10, 1)
FIXTURE_END = date(2026, 8, 20)
