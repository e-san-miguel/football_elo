"""Tournament classification and K-factor mapping for women's football."""

import re

import pandas as pd

# K=60: World Cup finals and Olympic Games
_K60 = {
    "FIFA World Cup",
    "World Cup",  # Pre-FIFA unofficial (1970-1971)
    "Olympic Games",
}

# K=50: Continental championship finals and intercontinental
_K50 = {
    "UEFA Euro",
    "Euro",
    "European Championship",
    "Copa América",
    "AFC Championship",
    "AFC Asian Cup",
    "CONCACAF Championship",
    "CONCACAF Gold Cup",
    "African Championship",
    "African Cup of Nations",
    "OFC Championship",
    "OFC Nations Cup",
    "Finalissima",
}

# K=40: Explicit qualifier/Olympic qualifying tournaments
# (most are caught by regex, but these are explicit overrides)
_K40 = {
    "AFC Olympic Qualifying Tournament",
    "CONCACAF Olympic Qualifying Tournament",
    "CAF Olympic Qualifying Tournament",
    "OFC Olympic Qualifying Tournament",
    "UEFA Olympic Qualifying Tournament",
    "UEFA Olympic Qualifying play-off",
    "CONCACAF Pre-Olympic Tournament",
    "AFC Olympic qualification",
    "Olympic qualification",
    "Olympic qualifyication",  # Typo in data
}

# Patterns that indicate K=40 (qualifiers)
_QUALIFIER_PATTERN = re.compile(r"qualifi", re.IGNORECASE)

# K=20: Friendlies
_FRIENDLY_NAMES = {"Friendly"}


def get_k_factor(tournament: str) -> int:
    """Return K factor for a tournament name.

    K=60: World Cup finals, Olympics
    K=50: Continental championship finals
    K=40: Qualifiers (WC, continental, Olympic)
    K=30: Other named tournaments (default)
    K=20: Friendlies
    """
    if tournament in _K60:
        return 60
    if tournament in _K50:
        return 50
    if tournament in _K40 or _QUALIFIER_PATTERN.search(tournament):
        return 40
    if tournament in _FRIENDLY_NAMES:
        return 20
    # Default: named tournament
    return 30


def audit_tournament_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """Return a table of all unique tournaments with their K factors and match counts."""
    tournaments = df.groupby("tournament").size().reset_index(name="matches")
    tournaments["k_factor"] = tournaments["tournament"].apply(get_k_factor)
    return tournaments.sort_values(
        ["k_factor", "matches"], ascending=[False, False]
    ).reset_index(drop=True)
