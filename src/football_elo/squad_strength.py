"""Aggregate per-player adjusted values into a per-team squad score."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .player_strength import adjusted_value


def squad_score_for_team(team_rows: pd.DataFrame,
                         tm_curve: dict[int, float] | None = None) -> float:
    """Sum of age-adjusted TM values across a team's squad (EUR)."""
    total = 0.0
    for _, r in team_rows.iterrows():
        v = r.get('value_at_kickoff')
        a = r.get('age_at_kickoff')
        if pd.isna(v) or pd.isna(a):
            continue
        total += adjusted_value(float(v), float(a), tm_curve)
    return total


def squad_scores(squad_df: pd.DataFrame,
                 tm_curve: dict[int, float] | None = None) -> dict[str, float]:
    """Return {team: score} from a squad DataFrame for a single tournament."""
    return {
        team: squad_score_for_team(rows, tm_curve)
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
