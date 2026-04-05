"""Core Elo rating calculation functions.

Implements the eloratings.net methodology:
    Rn = Ro + K * G * (W - We)
"""

from .config import ELO_DIVISOR, HOME_ADVANTAGE


def expected_result(rating_a: float, rating_b: float) -> float:
    """Compute expected match result for team A against team B.

    We = 1 / (10^(-dr/400) + 1), where dr = rating_a - rating_b.
    """
    dr = rating_a - rating_b
    return 1.0 / (10.0 ** (-dr / ELO_DIVISOR) + 1.0)


def goal_difference_index(goal_diff: int) -> float:
    """Compute G factor from absolute goal difference.

    - 0 or 1: G = 1
    - 2:      G = 1.5
    - N >= 3: G = (11 + N) / 8
    """
    n = abs(goal_diff)
    if n <= 1:
        return 1.0
    if n == 2:
        return 1.5
    return (11 + n) / 8


def match_result_value(
    home_score: int,
    away_score: int,
    shootout_winner: str | None,
    home_team: str,
    away_team: str,
) -> tuple[float, float]:
    """Determine W values for home and away teams.

    Win=1, Loss=0, Draw=0.5.
    Matches decided by shootout are treated as draws (0.5 each).
    """
    if home_score > away_score:
        return 1.0, 0.0
    if home_score < away_score:
        return 0.0, 1.0
    # Scores are level — draw (shootouts still count as 0.5)
    return 0.5, 0.5


def compute_rating_change(
    rating_home: float,
    rating_away: float,
    home_score: int,
    away_score: int,
    k_factor: int,
    is_neutral: bool,
    shootout_winner: str | None = None,
    home_team: str = "",
    away_team: str = "",
) -> tuple[float, float]:
    """Compute rating change for both teams after a match.

    Returns (delta_home, delta_away).
    """
    # Adjust for home advantage in expected result calculation
    ha = 0.0 if is_neutral else HOME_ADVANTAGE
    we_home = expected_result(rating_home + ha, rating_away)
    we_away = 1.0 - we_home

    # Actual result
    w_home, w_away = match_result_value(
        home_score, away_score, shootout_winner, home_team, away_team
    )

    # Goal difference index
    g = goal_difference_index(home_score - away_score)

    # Rating changes
    delta_home = k_factor * g * (w_home - we_home)
    delta_away = k_factor * g * (w_away - we_away)

    return delta_home, delta_away
