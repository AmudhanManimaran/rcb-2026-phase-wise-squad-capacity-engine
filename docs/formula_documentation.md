# Formula Documentation

Each formula lives in `backend/formulas/formula_NN.py`. Notation: i = player, p = phase, t = a legal ball faced, m = a match.

| # | Name | Expression | Module |
|---|------|-----------|--------|
| 01 | Phase assignment | PP: overs 1-6 (36 balls), MID: 7-16 (60), DEATH: 17-20 (24) | `formula_01.py`, SQL `fn_phase_of_over`, trigger `trg_bbb_phase` |
| 02 | Recency decay | w_t = 2^(-Age_t / H), H = 70 days by default | `formula_02.py`, SQL `fn_recency_weight` |
| 03 | Player phase SR | SR(i,p) = 100 * sum(w_t runs_t) / sum(w_t) | `formula_03.py`, SQL `fn_player_phase_raw` |
| 04 | Player phase OutProb | OutProb(i,p) = sum(w_t 1[out_t]) / sum(w_t) | `formula_04.py`, SQL `fn_player_phase_raw` |
| 05 | Cold-start shrinkage | est = (sum(w_t x_t) + k * prior) / (sum(w_t) + k) | `formula_05.py` |
| 06 | Expected phase balls | B_i(p) = (sum_m w_m balls_im(p) + k_m * B_prior(slot,p)) / (sum_m w_m + k_m) | `formula_06.py` |
| 07 | Ball share | BallShare_i(p) = B_i(p) / sum_j B_j(p) | `formula_07.py` |
| 08 | Team SR | TeamSR(p) = sum_i BallShare_i(p) * SR(i,p) | `formula_08.py` |
| 09 | Team OutProb | TeamOut(p) = sum_i BallShare_i(p) * OutProb(i,p) | `formula_09.py` |
| 10 | Phase capacity | Cap(p) = Balls(p) * (TeamSR(p)/100 + ExtrasRate); E[W](p) = Balls(p) * TeamOut(p) | `formula_10.py` |
| 11 | Venue phase share | s_p = V_p / sum V | `formula_11.py` |
| 12 | Venue factor | V_p = (n * observed + k_v * prior) / (n + k_v); VF(p) = V_p / L_p | `formula_12.py` |
| 13 | Opponent threat | OppThreat(p) = OppEcon(p) / LeagueEcon(p) | `formula_13.py` |
| 14 | Adjusted capacity | AdjCap(p) = Cap(p) * VF(p)^beta * OppThreat(p)^alpha; AdjW(p) = E[W](p) * OppThreat(p)^(-alpha) | `formula_14.py` |
| 15 | Bowling strength index | BSI = clip(LeagueEcon / RCBEcon, 0.85, 1.15) | `formula_15.py` |
| 16 | Target | T_base = lambda * VenuePar + (1 - lambda) * Capacity; T_recommended = T_base * (2 - BSI) | `formula_16.py` |
| 17 | Venue-shaped phase target | R_p = T * s_p | `formula_17.py` |
| 18 | Checkpoint cost | Cost = abs(Runs - R_target) + w * E[Wickets] | `formula_18.py` |
| 19 | Deficit carry-forward | Extra_q = Deficit * Eff(q) / sum Eff(remaining) | `formula_19.py` |
| 20 | Error metrics | AbsErr, RelErr, MAE, MAPE, Bias, tolerance hit | `formula_20.py` |

## Source of each formula

Formulas 02, 03, 04, 07, 08, 11, 13, 16 (T_recommended), 17, 18 and 19 are taken directly from the project PPT. The remaining formulas (01, 05, 06, 09, 10, 12, 14, 15, the T_base definition in 16, and 20) are the supporting definitions needed to make the PPT pipeline computable end to end. Where the PPT used a symbol without defining it (T_base, BSI, Eff), the definition above is the one implemented.

## Interpretation notes

- **OppThreat** is an economy ratio. Below 1.000 the opponent concedes less than the league in that phase (stronger bowling), so adjusted capacity falls and expected wickets rise.
- **BSI** above 1 means RCB's attack concedes less than the league, so a smaller total is defensible: T_recommended falls below T_base.
- **Priors in shrinkage.** SR is shrunk as runs per ball. k is expressed in weighted balls (calibrated grid: 15, 30, 60).
- **Extras rate** is the league extras per legal ball in the history window, shrunk toward 0.055 with 240 pseudo-balls.
- **Opponent prior.** OppEcon is shrunk toward LeagueEcon / bowl_strength(team, phase) with 36 pseudo-balls, because most opponents have bowled to RCB at most once before a given match.
- **Wicket resource** (used by formulas 18 and 19): resource(W) = max(0.35, 1 - 0.07 * max(0, W - 3)). The DP and the tracker use its ratio to the baseline expected wickets, so the intent-1.0 path reproduces the capacity projection exactly.

## Dynamic-programming solver

State: (phase index, cumulative runs quantised to 0.25, cumulative wickets quantised to 0.05). Action: intent a in {0.80, 0.85, ..., 1.25}.

```
phase runs    = AdjCap(p) * a * resource(W_before) / resource(W_base_before)
phase wickets = AdjW(p) * a^2.2
stage cost    = abs(CumRuns - CumTarget_p) + w * phase wickets      (x1.5 at over 20)
```

The solver returns the minimum-cost intent path, the planned phase and cumulative runs, and expected wickets at each checkpoint.

## Calibration

Grid search over a walk-forward backtest on matches before the validation case:

1. Projection parameters (half-life {35, 50, 70, 100, 140}, k {15, 30, 60}, alpha {0.5, 1.0}, beta {0.5, 1.0}) minimise the checkpoint MAE objective (20-over errors weighted x2).
2. Target weight lambda {0, 0.25, 0.5, 0.75, 1} minimises abs(T_base - actual total) on complete RCB innings.
3. Wicket penalty w {1, 2, 4, 6, 8} minimises the error between planned and actual 20-over wickets.

Ties are broken toward the methodology defaults (70 days, lambda 0.5, w 4).
