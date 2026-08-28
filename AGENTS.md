# Agent notes: white_river_rain_stage

Public GitHub. MIT. Question: Can Stage IV rain on the 1,219 mi² Nora drainage, plus last-day discharge, predict gage height at USGS 03351000?

This tree does not read `p_sfha`. Do not edit https://github.com/martialsystems/indiana_flood_completion or https://github.com/martialsystems/white_river_stage_inundation. Do not paint a wet mask. Do not start hourly MRMS as v1, QPF, WTP/substations, or a third figure.

Live Stage IV / NLDI / NWIS that 404s or is empty is a stop. Do not substitute Daymet or PRISM. Basin is NLDI 03351000, not HUC-8, not the 5 km HAND window.

`rainforge/` is the GraphForge pin: no `p_sfha`, temporal WY2024/holdout, fetch-or-stop, claim bans.

## Verify

`python3 ~/agent_laws_verify_before_done/vbd_gate.py check --app-root . --claim-done`

`vbd.runtime.json` runs `.venv/bin/python -m pytest`, `scripts/run_fixture.py`, and `rainforge/scripts/sanity_rainforge.py`. Do not use stock `/usr/bin/python3 -m pytest`.
