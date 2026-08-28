# Methodology: rain-to-stage at USGS 03351000

Question: Can Stage IV rain on the 1,219 mi² Nora drainage, plus last-day discharge, predict gage height at USGS 03351000?

## Layers

| Layer | Role | Source |
|-------|------|--------|
| Basin | clip mask, published 1,219 mi² | NLDI `USGS-03351000`. Pin sha256 `944566fd7828b63d4975dbeea69152c9c339ce11c71e668c01437d82f85f13a3`. Live geodesic area 1,227.28 mi². HUC-8 05120201 and the 5 km Nora HAND window are refused. |
| Rain | Stage IV daily accumulation on the NOAA HRAP 4,762.5 m grid, clipped to the basin, stored in mm | NCEP Stage IV daily GeoTIFF (`water.noaa.gov`). Native units are inches; convert and log. 404 or empty stops. |
| Last-day Q | antecedent | NWIS daily 00060, lag 1 calendar day |
| Label | observed stage | NWIS daily 00065 at 03351000. If DV 00065 is unpublished, daily max of IV 00065. |

Same-day Stage IV (lag 0) is a nowcast of that day's stage from rain that already fell, not QPF.

## Models

**A (skill).** Ridge on basin-mean rain at lags 0, 1, 2, 3 days; last-day Q; day-of-year sine and cosine. Compared to persistence (yesterday's stage) and Ridge on rain-sum + Q_lag. RMSE and MAE in feet on the temporal holdout. HistGradientBoosting is allowed by the contract; Ridge is the v1 skill model because the hydrologic vector is short.

**B (attribution).** Ridge on the vector of Stage IV cell 24 h accumulations plus last-day Q. The map is mean |coefficient| on the holdout, optionally times rain on 2026-08-15. About 1,219 / 16 ≈ 200 cells. That map is which upstream pixels matter, not inundation.

Random row splits are banned. Train through water year 2024 (through 2024-09-30). Hold out from 2024-10-01. August 2026 is not in train. Future rain (negative lag) is refused.

Live v1 date windows are summers (2024-07-01 to 2024-09-30 train; 2025-07-01 to 2025-09-30 and 2026-07-01 to 2026-08-20 holdout), 235 Stage IV days, 178 basin cells. On that holdout, persistence RMSE is 1.03 ft and model A is 3.19 ft (overshoot of the 2026-08-15 crest). The attribution map is still the pixel question. Fixture skill is a synthetic recoverability check, not the live nowcast.

## Stages

0: fixture rain field, synthetic Q/stage, temporal fit, two figures, no `p_sfha` import.
A: fetch Stage IV + NWIS + NLDI; clip; stop on 404/empty.
B: temporal split, fit A and B.
C: two figures, claim scan.

## Claims

Allowed: rain-to-stage nowcast at 03351000; Stage IV pixels on the 1,219 mi² drainage; last-day discharge as antecedent; attribution of upstream rain.

Banned: 100-year exceedance; `P(sfha | hydro)` as a feature, label, or forecast; HAND mask as a FIRM; attribution as a wet mask or a FIRM; flood warning / emergency forecast; training on FEMA; climate; a third figure.
