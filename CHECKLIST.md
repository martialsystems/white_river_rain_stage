# Operator checklist

1. Fixture Stage 0 green: two figures, temporal split, no `p_sfha`.
2. Live: NLDI basin area near 1,219 mi² (pin 1,227.28), Stage IV clip in mm on NOAA HRAP, NWIS 00060 plus 00065 as DV or IV daily max.
3. 404 or empty Stage IV stops (`run_live.py` exit 2).
4. Holdout RMSE vs persistence in the report. August 2026 not in train.
5. At most two figures. Attribution caption is pixels, not a wet mask. Product figures are `logs/nora_live/`.
6. Push public `martialsystems/white_river_rain_stage`.
