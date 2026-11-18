# Testing and Validation

## Automated tests (`python -m pytest -v`)

| File | Covers |
| --- | --- |
| `test_formulas.py` | All 20 formulas, including edge cases (cold start, clipping, zero weights) |
| `test_phase_engine.py` | Phase tagging, phase breakdown, checkpoint evaluability for full innings and early chases |
| `test_capacity_engine.py` | Ball shares sum to 1, team SR and capacity arithmetic, extras prior |
| `test_target_solver.py` | DP keeps intent 1.0 when target equals capacity, raises intent for higher targets, wicket penalty reduces risk, projection and target formulas |
| `test_deficit_solver.py` | Overs parsing, linear plan interpolation, deficit fully redistributed, status logic |
| `test_backtesting.py` | No future leakage, Match 1 equals priors, earlier predictions unaffected by changes to later deliveries, backtest metrics |
| `test_api.py` | Every GET endpoint, plan then tracker flow, custom XI validation, error codes |

Database-dependent tests are skipped automatically when PostgreSQL is unreachable.

## SQL validation (`database/validation/`)

Each query returns zero rows when the data is consistent.

- `01_data_integrity.sql`: two innings per match, 11-player XI plus one impact player, batters and bowlers belong to the match squad, four-over limit, six legal balls per over.
- `02_score_validation.sql`: innings and match totals equal the sum of deliveries, running totals end at the innings total, winners agree with scores, chases end within one scoring shot of the target.
- `03_phase_validation.sql`: trigger phase equals formula 01, phase splits sum to totals, phase ball limits, stored checkpoints equal `fn_innings_checkpoint`.
- `04_prediction_validation.sql`: no leakage in stored predictions, ball shares and venue shares sum to 1, cumulative checkpoints are non-decreasing, and the SQL-layer weighted SR (formulas 02-03) equals the Python engine's observed SR for every profile of the latest backtest.

## Backtesting method

1. Order RCB matches by date.
2. For each match, run the full pipeline using only earlier completed matches.
3. Compare the capacity projection with actual RCB runs and wickets at overs 6, 16 and 20.
4. A checkpoint is not evaluable when a chase ended before it; an all-out innings remains evaluable.
5. Tolerances: 8 runs at over 6, 14 at over 16, 18 at over 20, or 10 percent of actual if larger.
6. Each match is classified: Accurate, Powerplay shortfall, Middle-overs stall, Death-overs shortfall, Batting collapse, Over-performance, Moderate deviation, Chase finished early.

## Limitations

- The 2026 season is synthetic, so metrics demonstrate the method rather than real-world accuracy.
- 14 matches give small samples, especially for venue (often one innings) and opponent (at most one prior meeting). Both rely on shrinkage toward priors.
- Calibration on 13 matches can select grid-edge values; treat the CALIBRATED set as indicative, and compare with DEFAULT in the Backtesting module.
