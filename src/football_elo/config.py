from pathlib import Path

# Project root (two levels up from this file: src/football_elo/config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data source URLs (GitHub raw)
DATA_BASE_URL = (
    "https://raw.githubusercontent.com/martj42/"
    "womens-international-results/refs/heads/master"
)
RESULTS_URL = f"{DATA_BASE_URL}/results.csv"
SHOOTOUTS_URL = f"{DATA_BASE_URL}/shootouts.csv"

# Local paths
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Elo parameters
INITIAL_RATING = 1500.0
HOME_ADVANTAGE = 100.0
ELO_DIVISOR = 400.0
