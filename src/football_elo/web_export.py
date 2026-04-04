"""Export Elo data as JSON files for the website."""

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

from .config import OUTPUT_DIR
from .output import TEAM_COLORS
from .pipeline import EloSystem

DOCS_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "data"


def slugify(name: str) -> str:
    """Convert team name to URL-safe slug."""
    # Normalize unicode (e.g., é -> e)
    s = unicodedata.normalize("NFKD", name)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s


def export_rankings_json(elo: EloSystem, output_dir: Path) -> None:
    """Export current rankings as JSON."""
    rankings = elo.get_current_rankings()
    history_df = elo.get_history_dataframe()

    # Compute per-team stats
    teams = []
    for rank, row in rankings.iterrows():
        team = row["team"]
        team_hist = history_df[history_df["team"] == team]
        matches = len(team_hist)

        # Last rating change
        last_change = team_hist.iloc[-1]["rating_change"] if matches > 0 else 0

        # Peak rating
        peak_rating = team_hist["rating_after"].max() if matches > 0 else row["rating"]
        peak_date = ""
        if matches > 0:
            peak_idx = team_hist["rating_after"].idxmax()
            peak_date = str(team_hist.loc[peak_idx, "date"].date())

        teams.append({
            "rank": int(rank),
            "team": team,
            "slug": slugify(team),
            "rating": round(row["rating"], 1),
            "rating_change": round(last_change, 1),
            "matches_played": matches,
            "peak_rating": round(peak_rating, 1),
            "peak_date": peak_date,
        })

    # Last match date in the dataset
    last_updated = str(history_df["date"].max().date()) if len(history_df) > 0 else ""

    data = {
        "last_updated": last_updated,
        "teams": teams,
    }
    (output_dir / "rankings.json").write_text(
        json.dumps(data, separators=(",", ":")), encoding="utf-8"
    )


def export_team_colors_json(output_dir: Path) -> None:
    """Export team colors mapping."""
    colors = {slugify(team): color for team, color in TEAM_COLORS.items()}
    (output_dir / "team_colors.json").write_text(
        json.dumps(colors, separators=(",", ":")), encoding="utf-8"
    )


def export_team_histories(elo: EloSystem, output_dir: Path) -> None:
    """Export per-team history JSON files."""
    history_dir = output_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    history_df = elo.get_history_dataframe()

    for team in elo.ratings:
        team_hist = history_df[history_df["team"] == team].copy()
        slug = slugify(team)

        records = []
        for _, r in team_hist.iterrows():
            records.append({
                "date": str(r["date"].date()),
                "opponent": r["opponent"],
                "ts": int(r["team_score"]),
                "os": int(r["opponent_score"]),
                "tournament": r["tournament"],
                "k": int(r["k_factor"]),
                "rb": round(r["rating_before"], 1),
                "ra": round(r["rating_after"], 1),
                "rc": round(r["rating_change"], 1),
            })

        data = {"team": team, "slug": slug, "history": records}
        (history_dir / f"{slug}.json").write_text(
            json.dumps(data, separators=(",", ":")), encoding="utf-8"
        )


def export_history_top_n(elo: EloSystem, n: int, output_dir: Path) -> None:
    """Export bundled history for top N teams (date + rating only)."""
    rankings = elo.get_current_rankings()
    top_teams = rankings.head(n)["team"].tolist()
    history_df = elo.get_history_dataframe()

    result = {}
    for team in top_teams:
        team_hist = history_df[history_df["team"] == team]
        slug = slugify(team)
        result[slug] = {
            "team": team,
            "data": [
                {"date": str(r["date"].date()), "ra": round(r["rating_after"], 1)}
                for _, r in team_hist.iterrows()
            ],
        }

    (output_dir / "history_top20.json").write_text(
        json.dumps(result, separators=(",", ":")), encoding="utf-8"
    )


def export_tournaments_json(output_dir: Path) -> None:
    """Export major tournament dates for quick-jump buttons."""
    tournaments = [
        {"name": "2023 WWC Final", "date": "2023-08-20"},
        {"name": "2019 WWC Final", "date": "2019-07-07"},
        {"name": "2015 WWC Final", "date": "2015-07-05"},
        {"name": "2011 WWC Final", "date": "2011-07-17"},
        {"name": "2007 WWC Final", "date": "2007-09-30"},
        {"name": "2003 WWC Final", "date": "2003-10-12"},
        {"name": "1999 WWC Final", "date": "1999-07-10"},
        {"name": "1995 WWC Final", "date": "1995-06-18"},
        {"name": "1991 WWC Final", "date": "1991-11-30"},
        {"name": "2024 Olympics", "date": "2024-08-10"},
        {"name": "2021 Olympics", "date": "2021-08-06"},
    ]
    (output_dir / "tournaments.json").write_text(
        json.dumps(tournaments, separators=(",", ":")), encoding="utf-8"
    )


def export_all(elo: EloSystem, output_dir: Path = DOCS_DATA_DIR) -> None:
    """Export all JSON files for the website."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Exporting to {output_dir}/")

    export_rankings_json(elo, output_dir)
    print("    rankings.json")

    export_team_colors_json(output_dir)
    print("    team_colors.json")

    export_team_histories(elo, output_dir)
    print(f"    history/ ({len(elo.ratings)} team files)")

    export_history_top_n(elo, 20, output_dir)
    print("    history_top20.json")

    export_tournaments_json(output_dir)
    print("    tournaments.json")
