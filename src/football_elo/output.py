"""Output formatting: CSV, markdown, and charts."""

from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .pipeline import EloSystem


def write_rankings_csv(rankings: pd.DataFrame, filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    rankings.to_csv(filepath)


def write_rankings_markdown(rankings: pd.DataFrame, filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    lines = ["| Rank | Team | Rating |", "|---:|:---|---:|"]
    for rank, row in rankings.iterrows():
        lines.append(f"| {rank} | {row['team']} | {row['rating']:.0f} |")
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_history_csv(elo_system: EloSystem, filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df = elo_system.get_history_dataframe()
    df.to_csv(filepath, index=False)


# Flag-inspired colors for top teams
TEAM_COLORS = {
    "United States": "#002868",   # navy blue
    "Spain": "#c60b1e",           # red
    "Japan": "#bc002d",           # crimson
    "England": "#ffffff",         # white (with dark edge)
    "France": "#002395",          # blue
    "Germany": "#000000",         # black
    "Sweden": "#006aa7",          # blue
    "Brazil": "#009739",          # green
    "Canada": "#ff0000",          # red
    "Netherlands": "#ff6600",     # orange
    "North Korea": "#024fa2",     # blue
    "Australia": "#00843d",       # green
    "Norway": "#ba0c2f",         # red
    "Denmark": "#c8102e",         # red
    "Italy": "#008c45",           # green
    "China PR": "#ee1c25",        # red
    "Mexico": "#006847",          # green
    "Colombia": "#fcd116",        # yellow
    "Nigeria": "#008751",         # green
    "South Korea": "#cd2e3a",     # red
}

# Teams that need edge color to be visible on white background
_NEEDS_EDGE = {"England"}


def plot_top_n_history(
    elo_system: EloSystem, n: int, filepath: Path
) -> None:
    """Plot rating history for the top N teams by current rating."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    rankings = elo_system.get_current_rankings()
    top_teams = rankings.head(n)["team"].tolist()

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_facecolor("#f7f7f7")

    for team in top_teams:
        hist = elo_system.get_team_history(team)
        color = TEAM_COLORS.get(team)
        lw = 2.0 if team in ("United States", "Spain") else 1.3
        if team in _NEEDS_EDGE:
            # Draw a dark outline behind the white line
            ax.plot(hist["date"], hist["rating_after"], color="#888888",
                    linewidth=lw + 1, alpha=0.5)
        ax.plot(hist["date"], hist["rating_after"], label=team,
                color=color, linewidth=lw)

    ax.set_xlim(left=datetime(1990, 1, 1))
    ax.set_xlabel("Year")
    ax.set_ylabel("Elo Rating")
    ax.set_title("Women's International Football Elo Ratings — Top Teams")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=1500, color="gray", linestyle="--", alpha=0.5, label="_baseline")

    fig.tight_layout()
    fig.savefig(filepath, dpi=150)
    plt.close(fig)


def plot_top_n_history_smooth(
    elo_system: EloSystem, n: int, filepath: Path, window_days: int = 365
) -> None:
    """Plot smoothed rating history (rolling average) for top N teams."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    rankings = elo_system.get_current_rankings()
    top_teams = rankings.head(n)["team"].tolist()

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_facecolor("#f7f7f7")

    for team in top_teams:
        hist = elo_system.get_team_history(team)
        # Create a time-indexed series and resample to daily, then rolling mean
        series = (
            hist.set_index("date")["rating_after"]
            .resample("D").last()
            .ffill()
            .rolling(window=window_days, center=True, min_periods=1)
            .mean()
        )
        color = TEAM_COLORS.get(team)
        lw = 2.5 if team in ("United States", "Spain") else 1.5
        if team in _NEEDS_EDGE:
            ax.plot(series.index, series.values, color="#888888",
                    linewidth=lw + 1, alpha=0.5)
        ax.plot(series.index, series.values, label=team,
                color=color, linewidth=lw)

    ax.set_xlim(left=datetime(1990, 1, 1))
    ax.set_xlabel("Year")
    ax.set_ylabel("Elo Rating")
    ax.set_title(
        f"Women's International Football Elo Ratings — "
        f"Smoothed Trends ({window_days}-day rolling average)"
    )
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=1500, color="gray", linestyle="--", alpha=0.5)

    fig.tight_layout()
    fig.savefig(filepath, dpi=150)
    plt.close(fig)
