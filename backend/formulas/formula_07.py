"""Formula 07: Player ball share within the selected XI.

BallShare_i(p) = B_bar_i(p) / sum_j B_bar_j(p)
"""


def ball_share(expected_balls: dict) -> dict:
    total = sum(max(v, 0.0) for v in expected_balls.values())
    if total <= 0:
        n = len(expected_balls) or 1
        return {k: 1.0 / n for k in expected_balls}
    return {k: max(v, 0.0) / total for k, v in expected_balls.items()}
