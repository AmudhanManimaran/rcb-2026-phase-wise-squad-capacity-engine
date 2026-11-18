"""EeSaala Tracker formula library: the 20 analytical formulas of the methodology."""
from .formula_01 import PHASES, PHASE_BALLS, PHASE_OVERS, CHECKPOINT_OVER, phase_of_over, phase_of_ball
from .formula_02 import recency_weight
from .formula_03 import weighted_strike_rate
from .formula_04 import weighted_out_probability
from .formula_05 import shrink_to_prior
from .formula_06 import SLOT_BALL_TEMPLATE, prior_balls, expected_phase_balls
from .formula_07 import ball_share
from .formula_08 import team_strike_rate
from .formula_09 import team_out_probability
from .formula_10 import phase_capacity
from .formula_11 import venue_phase_share
from .formula_12 import blended_average, venue_phase_factor
from .formula_13 import opponent_threat
from .formula_14 import adjusted_capacity
from .formula_15 import bowling_strength_index
from .formula_16 import base_target, recommended_target
from .formula_17 import venue_shaped_targets
from .formula_18 import checkpoint_cost, wicket_resource
from .formula_19 import deficit_carry_forward
from .formula_20 import CHECKPOINT_TOLERANCE, abs_error, rel_error, within_tolerance, mae, mape, bias

FORMULA_CATALOGUE = [
    (1, "Phase assignment", "phase(over): PP 1-6, MID 7-16, DEATH 17-20"),
    (2, "Recency decay", "w_t = 2^(-Age_t / 70)"),
    (3, "Player phase strike rate", "SR(i,p) = 100 * sum(w_t runs_t) / sum(w_t)"),
    (4, "Player phase out probability", "OutProb(i,p) = sum(w_t 1[out_t]) / sum(w_t)"),
    (5, "Cold-start shrinkage", "est = (sum(w x) + k * prior) / (sum(w) + k)"),
    (6, "Expected phase balls", "B_bar_i(p) = (sum(w_m balls_m) + k_m B_prior) / (sum(w_m) + k_m)"),
    (7, "Ball share", "BallShare_i(p) = B_bar_i(p) / sum_j B_bar_j(p)"),
    (8, "Team strike rate", "TeamSR(p) = sum_i BallShare_i(p) * SR(i,p)"),
    (9, "Team out probability", "TeamOut(p) = sum_i BallShare_i(p) * OutProb(i,p)"),
    (10, "Phase capacity", "Cap(p) = Balls(p) * (TeamSR/100 + ExtrasRate); E[W] = Balls(p) * TeamOut"),
    (11, "Venue phase share", "s_p = V_bar_p / V_bar"),
    (12, "Venue phase factor", "VF(p) = V_bar_p / L_bar_p (shrunk to venue prior)"),
    (13, "Opponent threat", "OppThreat(p) = OppEcon(p) / LeagueEcon(p)"),
    (14, "Adjusted capacity", "AdjCap(p) = Cap(p) * VF^beta * OppThreat^alpha"),
    (15, "Bowling strength index", "BSI = clip(LeagueEcon / RCBEcon, 0.85, 1.15)"),
    (16, "Recommended target", "T_base = lambda*Par + (1-lambda)*Cap; T_rec = T_base * (2 - BSI)"),
    (17, "Venue-shaped phase target", "R_p = T * s_p"),
    (18, "Checkpoint solver cost", "Cost = |Runs - R_p| + w * E[Wickets]"),
    (19, "Deficit carry-forward", "Extra_q = Deficit * Eff(q) / sum Eff(remaining)"),
    (20, "Backtest error metrics", "AbsErr, RelErr, MAE, MAPE, Bias, tolerance hit"),
]
