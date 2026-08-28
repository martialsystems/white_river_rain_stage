# Operator checklist

1. Fixture Stage 0 green: CI oracle only. Does not rescue live skill.
2. Live negative result is `e41fd69`: persistence 1.03 ft RMSE, 178-pixel Ridge 3.19. Do not re-fit to chase that table.
3. 404 or empty Stage IV stops (`run_live.py` exit 2).
4. Figure 2 caption: where Ridge looks, not source areas for the flood. A model that loses to persistence should not be read as a runoff map.
5. At most two figures. Product figures are `logs/nora_live/`.
6. Do not start a next rain tree from this snapshot (longer years plus routed/lagged basin-mean, if asked later).
7. Push public `martialsystems/white_river_rain_stage`.
