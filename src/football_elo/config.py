from pathlib import Path

# Project root (two levels up from this file: src/football_elo/config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data source URLs per gender (GitHub raw)
DATA_SOURCES = {
    "women": {
        "results": "https://raw.githubusercontent.com/martj42/womens-international-results/refs/heads/master/results.csv",
        "shootouts": "https://raw.githubusercontent.com/martj42/womens-international-results/refs/heads/master/shootouts.csv",
    },
    "men": {
        "results": "https://raw.githubusercontent.com/martj42/international_results/refs/heads/master/results.csv",
        "shootouts": "https://raw.githubusercontent.com/martj42/international_results/refs/heads/master/shootouts.csv",
    },
}

# Local paths
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Elo parameters
INITIAL_RATING = 1500.0
HOME_ADVANTAGE = 50.0
ELO_DIVISOR = 400.0
