"""Aggregate per-player adjusted values into a per-team squad score."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .player_strength import adjusted_value


def squad_score_for_team(team_rows: pd.DataFrame,
                         tm_curve: dict[int, float] | None = None,
                         agg: str = "mean") -> float:
    """Age-adjusted TM value aggregated across a team's squad.

    agg='mean' averages across players with valid TM data — robust to missing
    players and to squad-size changes (23 in 2018 → 26 in 2022).
    agg='sum' sums total squad value (sensitive to squad size + missing data).
    """
    vals: list[float] = []
    for _, r in team_rows.iterrows():
        v = r.get('value_at_kickoff')
        a = r.get('age_at_kickoff')
        if pd.isna(v) or pd.isna(a):
            continue
        vals.append(adjusted_value(float(v), float(a), tm_curve))
    if not vals:
        return 0.0
    if agg == "mean":
        return sum(vals) / len(vals)
    return sum(vals)


def squad_scores(squad_df: pd.DataFrame,
                 tm_curve: dict[int, float] | None = None,
                 agg: str = "mean") -> dict[str, float]:
    """Return {team: score} from a squad DataFrame for a single tournament."""
    return {
        team: squad_score_for_team(rows, tm_curve, agg=agg)
        for team, rows in squad_df.groupby('team')
    }


def z_scores(scores: dict[str, float]) -> dict[str, float]:
    """Z-normalize scores across the tournament's teams."""
    vals = list(scores.values())
    if not vals:
        return {}
    mu = sum(vals) / len(vals)
    var = sum((v - mu) ** 2 for v in vals) / len(vals)
    sd = var ** 0.5
    if sd == 0:
        return {t: 0.0 for t in scores}
    return {t: (v - mu) / sd for t, v in scores.items()}


def load_tournament_squads(year: int) -> pd.DataFrame:
    """Load data/squads/{year}.csv."""
    root = Path(__file__).resolve().parent.parent.parent
    path = root / "data" / "squads" / f"{year}.csv"
    return pd.read_csv(path)
