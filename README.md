# White River rain-to-stage (Nora)

Can Stage IV rain on the 1,219 mi² Nora drainage, plus last-day discharge, predict gage height at USGS 03351000?

This tree is hydrology ML at USGS **03351000** / NWS **NORI3**. The label is observed gage height (NWIS 00065; daily max of IV because DV 00065 is unpublished). Inputs are NCEP Stage IV daily rainfall clipped to the NLDI basin for that gage (published **1,219 mi²**, live geodesic **1,227.28 mi²**, 178 HRAP cells) and last-day discharge (NWIS 00060, lag 1). The map is which upstream Stage IV pixels the model uses (Ridge |coefficient|). That map is attribution, not a wet mask. This tree does not read `p_sfha`.

Sibling HAND paint: https://github.com/martialsystems/white_river_stage_inundation  
Sibling map-completion: https://github.com/martialsystems/indiana_flood_completion

Nowcast, not QPF: rain that already fell. Daily timestep. Train through water year 2024 (through 2024-09-30). Hold out 2025 to 2026. August 2026 is a named confirmation event and is not in train. Live v1 windows are summers: 2024-07-01 to 2024-09-30 (train), 2025-07-01 to 2025-09-30 and 2026-07-01 to 2026-08-20 (holdout). 235 Stage IV days, 0 skipped.

![Figure 1. Holdout hydrograph](logs/nora_live/hydrograph.png)

Figure 1. Live holdout: observed stage, persistence, and model A (Ridge on basin-mean rain lags 0 to 3, last-day Q, day-of-year). Lines at 11.00 ft and 21.18 ft. August 2026 shaded. Persistence RMSE 1.03 ft. Model A 3.19 ft: it overshoots the 2026-08-15 crest. Yesterday's stage is the better nowcast on this sample.

![Figure 2. Attribution](logs/nora_live/attribution.png)

Figure 2. Live Stage IV pixels on the 1,219 mi² drainage, colored by holdout |Ridge coefficient|. Upstream rain the model uses, not a wet mask.

## Live skill (holdout)

From `logs/nora_live/stage_c_report.json`. RMSE and MAE in feet. Train n=89 (WY2024 summer). Holdout n=143. August 2026 not in train. Native Stage IV units: inches, stored as mm. Label: IV daily max.

| Model | RMSE (ft) | MAE (ft) |
|-------|----------:|---------:|
| Persistence | 1.03 | 0.50 |
| Climatology | 3.42 | 1.49 |
| Rain-sum + Q_lag | 2.58 | 0.83 |
| Model A (Ridge) | 3.19 | 0.84 |

## Stage 0

Synthetic 8×10 basin so CI trains without NOAA. Fixture skill (A RMSE 0.37 ft vs persistence 0.54 ft) is in `logs/stage0_fixture/stage0_report.json`. Tests require A to beat persistence on that synthetic series and the hotspot |coef| to exceed the other cells.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src:. python3 scripts/run_fixture.py logs/stage0_fixture
.venv/bin/python -m pytest tests -q
PYTHONPATH=src:. python3 scripts/run_live.py logs/nora_live
```

Do not use stock `/usr/bin/python3 -m pytest`: it has no rasterio. HTTP 404 or an empty Stage IV cube stops (`run_live.py` exit 2). Daymet and PRISM are not substitutes. Two figures max, then this tree stops.

| File | Role |
|------|------|
| [METHODOLOGY.md](METHODOLOGY.md) | Locked contract |
| [AGENTS.md](AGENTS.md) | Agent rules |
| [CHECKLIST.md](CHECKLIST.md) | Operator list |
| `src/rainstage/` | Basin, Stage IV clip, models A/B, figures, claims |
| `rainforge/` | GraphForge pin: no `p_sfha`, temporal split, fetch-or-stop, claim bans |
