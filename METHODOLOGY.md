# Methodology: rain-to-stage at USGS 03351000

Question: Can Stage IV rain on the 1,219 mi² Nora drainage, plus last-day discharge, predict gage height at USGS 03351000?

Live answer at `e41fd69`, this sample, this Ridge: no. Persistence RMSE 1.03 ft. Rain-sum plus yesterday's Q 2.58. 178-pixel Ridge 3.19 RMSE, MAE tied with the two-feature rain model. Fixture skill does not rescue live.

## Layers

| Layer | Role | Source |
|-------|------|--------|
| Basin | clip mask, published 1,219 mi² | NLDI `USGS-03351000`. Pin sha256 `944566fd7828b63d4975dbeea69152c9c339ce11c71e668c01437d82f85f13a3`. Live geodesic area 1,227.28 mi². HUC-8 05120201 and the 5 km Nora HAND window are refused. |
| Rain | Stage IV daily accumulation on the NOAA HRAP 4,762.5 m grid, clipped to the basin, stored in mm | NCEP Stage IV daily GeoTIFF (`water.noaa.gov`). Native units are inches; convert and log. 404 or empty stops. |
| Last-day Q | antecedent | NWIS daily 00060, lag 1 calendar day |
| Label | observed stage | NWIS daily 00065 at 03351000. If DV 00065 is unpublished, daily max of IV 00065. |

Same-day Stage IV (lag 0) is a nowcast of that day's stage from rain that already fell, not QPF. Daily rain versus daily-max stage ignores travel time on 1,227 mi².

## Models

**A (skill).** Ridge on basin-mean rain at lags 0, 1, 2, 3 days; last-day Q; day-of-year sine and cosine. Compared to persistence (yesterday's stage) and Ridge on rain-sum + Q_lag. RMSE and MAE in feet on the temporal holdout. Persistence is the bar.

**B (attribution).** Ridge on the vector of Stage IV cell 24 h accumulations plus last-day Q. About 178 cells on this drainage. The grid is where Ridge looks, not source areas for the flood. A model that loses to persistence should not be read as a runoff map.

Random row splits are banned. Train through water year 2024 (through 2024-09-30). Hold out from 2024-10-01. August 2026 is not in train. Future rain (negative lag) is refused.

Live v1 windows are summers (2024-07-01 to 2024-09-30 train; 2025-07-01 to 2025-09-30 and 2026-07-01 to 2026-08-20 holdout), 235 Stage IV days, 89 train rows, 143 holdout rows. 178 cells on 89 days is a wide, short matrix. The two-feature rain-sum model beating Ridge is the tell. Summers plus one huge crest in holdout punish a linear rain term.

## Stages

0: fixture rain field, synthetic Q/stage, temporal fit, two figures, no `p_sfha` import. Fixture is a CI oracle (planted hotspot recoverable), not live skill.
A: fetch Stage IV + NWIS + NLDI; clip; stop on 404/empty.
B: temporal split, fit A and B.
C: two figures, claim scan.

## Claims

Allowed: rain-to-stage nowcast at 03351000; Stage IV pixels on the 1,219 mi² drainage; last-day discharge as antecedent; negative live result versus persistence; "where Ridge looks."

Banned: 100-year exceedance; `P(sfha | hydro)` as a feature, label, or forecast; HAND mask as a FIRM; attribution as a wet mask, a FIRM, a runoff map, or source areas for the flood; fixture skill rescues live; flood warning / emergency forecast; training on FEMA; climate; a third figure.

## Next tree, if any

Longer years plus a routed or lagged basin-mean rain term. Not more pixels. Not a wet mask. Persistence stays the bar. Do not start that tree from this snapshot.
