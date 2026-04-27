"""Calibrate the Poisson goal model from historical match data.

Replays Elo on the men's (or women's) results, captures each match's
pre-match ratings via the snapshot hook in ``EloSystem``, then fits
Poisson GLMs to recover the constants used in ``worldcup.py``:

  Spec A  (current model form):  log E[goals] = alpha + c * dr
  Spec B  (richer):              log E[goals] = alpha + c * dr + c2 * dr^2 + delta * is_home

Spec A is what the production code assumes. Spec B adds a quadratic in
``dr`` to test whether scoring is sublinear in the rating gap (which
naturally tames blowouts in the WC2026 tail), and a home dummy to check
the Elo system's hardcoded +50 against the goal-scoring data.

Both specs are fit with cluster-robust SEs, clustering by match (each
match contributes two team-rows, which are not independent).
"""

from __future__ import annotations

import argparse
import math

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .config import HOME_ADVANTAGE
from .data import load_all
from .pipeline import EloSystem


# ---------------------------------------------------------------------------
# Data construction
# ---------------------------------------------------------------------------

def replay_with_snapshots(gender: str = "men") -> pd.DataFrame:
    """Replay Elo on the full history, returning one row per match with
    pre-match ratings attached."""
    matches = load_all(gender=gender)
    snapshots: list[dict] = []
    elo = EloSystem(snapshots=snapshots)
    elo.process_all(matches)
    snaps = pd.DataFrame(snapshots)
    snaps = snaps.reset_index(drop=True)
    snaps["match_id"] = snaps.index
    return snaps


def build_team_match_rows(
    snaps: pd.DataFrame, home_advantage: float = HOME_ADVANTAGE,
) -> pd.DataFrame:
    """Expand match snapshots to two team-perspective rows per match.

    ``dr`` follows the same convention as ``worldcup._expected_goals``:
    ``dr = (R_team + ha) - R_opp`` where ``ha`` is the +50 home bump
    (zero at neutral venues, non-zero only for the actual home side).
    """
    ha_home = np.where(snaps["is_neutral"], 0.0, home_advantage)

    home = pd.DataFrame({
        "match_id": snaps["match_id"],
        "date": snaps["date"],
        "tournament": snaps["tournament"],
        "goals": snaps["home_score"].astype(int),
        "dr": (snaps["r_home_pre"] + ha_home) - snaps["r_away_pre"],
        "is_home": (~snaps["is_neutral"]).astype(int),
    })
    away = pd.DataFrame({
        "match_id": snaps["match_id"],
        "date": snaps["date"],
        "tournament": snaps["tournament"],
        "goals": snaps["away_score"].astype(int),
        "dr": snaps["r_away_pre"] - (snaps["r_home_pre"] + ha_home),
        "is_home": 0,
    })
    return pd.concat([home, away], ignore_index=True)


# ---------------------------------------------------------------------------
# Model fits
# ---------------------------------------------------------------------------

def _fit(y, X, groups) -> sm.GLM:
    return sm.GLM(y, X, family=sm.families.Poisson()).fit(
        cov_type="cluster", cov_kwds={"groups": groups},
    )


def fit_spec_a(df: pd.DataFrame):
    X = pd.DataFrame({"const": 1.0, "dr": df["dr"]})
    return _fit(df["goals"], X, df["match_id"].values)


def fit_spec_b(df: pd.DataFrame):
    """Spec B: adds dr^2 (sublinearity) and is_home (does the +50 Elo
    rule fully capture home advantage on the goal side?)."""
    X = pd.DataFrame({
        "const": 1.0,
        "dr": df["dr"],
        "dr_sq": df["dr"] ** 2,
        "is_home": df["is_home"].astype(float),
    })
    return _fit(df["goals"], X, df["match_id"].values)


def fit_spec_bp(df: pd.DataFrame):
    """Spec B': dr^2 only — the parsimonious quadratic model production
    adopts. Home advantage stays encoded as the +50 Elo rule via dr."""
    X = pd.DataFrame({
        "const": 1.0,
        "dr": df["dr"],
        "dr_sq": df["dr"] ** 2,
    })
    return _fit(df["goals"], X, df["match_id"].values)


def predict_spec_a(res, df: pd.DataFrame) -> np.ndarray:
    a, c = res.params["const"], res.params["dr"]
    return np.exp(a + c * df["dr"].values)


def predict_spec_b(res, df: pd.DataFrame) -> np.ndarray:
    a = res.params["const"]
    c = res.params["dr"]
    c2 = res.params["dr_sq"]
    d = res.params["is_home"]
    dr = df["dr"].values
    return np.exp(a + c * dr + c2 * dr ** 2 + d * df["is_home"].values)


def predict_spec_bp(res, df: pd.DataFrame) -> np.ndarray:
    a = res.params["const"]
    c = res.params["dr"]
    c2 = res.params["dr_sq"]
    dr = df["dr"].values
    return np.exp(a + c * dr + c2 * dr ** 2)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _print_fit(name: str, res) -> None:
    print(f"\n=== {name} ===")
    print(f"  N = {int(res.nobs):,}    pseudo-R^2 (deviance) = "
          f"{1 - res.deviance / res.null_deviance:.4f}    AIC = {res.aic:.1f}")
    print(f"  {'param':>10}  {'estimate':>12}  {'cluster SE':>12}  {'z':>8}")
    for name_ in res.params.index:
        b = res.params[name_]
        se = res.bse[name_]
        z = b / se if se > 0 else float("nan")
        print(f"  {name_:>10}  {b:>12.6g}  {se:>12.6g}  {z:>8.2f}")
    print(f"  mu = exp(const) = {math.exp(res.params['const']):.4f}")


def _poisson_p_ge(lam: np.ndarray, k: int) -> np.ndarray:
    """Elementwise P(Pois(lam) >= k)."""
    cdf = np.zeros_like(lam, dtype=float)
    for j in range(k):
        cdf += np.exp(-lam) * lam ** j / math.factorial(j)
    return 1.0 - cdf


def _print_calibration_table(name: str, df: pd.DataFrame, lam: np.ndarray, n_bins: int = 10) -> None:
    work = df[["dr", "goals"]].copy()
    work["lam"] = lam
    work["p_ge6_pred"] = _poisson_p_ge(lam, 6)
    work["bin"] = pd.qcut(work["dr"], q=n_bins, duplicates="drop", labels=False)
    g = work.groupby("bin")
    tbl = pd.DataFrame({
        "n": g.size(),
        "dr_lo": g["dr"].min().round(0),
        "dr_hi": g["dr"].max().round(0),
        "obs_goals": g["goals"].mean().round(3),
        "pred_goals": g["lam"].mean().round(3),
        "obs_p_ge6": g["goals"].apply(lambda s: (s >= 6).mean()).round(4),
        "pred_p_ge6": g["p_ge6_pred"].mean().round(4),
    })
    print(f"\n  Calibration table — {name} (deciles of dr)")
    print(tbl.to_string())


def _print_constants(res_a, res_b, res_bp, adopt: str) -> None:
    print("\n=== Copy-paste constants ===")
    if adopt == "A":
        mu = math.exp(res_a.params["const"])
        c = res_a.params["dr"]
        print(f"# In src/football_elo/worldcup.py and docs/js/bracket.js:")
        print(f"GOAL_BASELINE     = {mu:.4f}")
        print(f"GOAL_ELO_SCALING  = {c:.6f}")
    elif adopt == "Bp":
        mu = math.exp(res_bp.params["const"])
        c = res_bp.params["dr"]
        c2 = res_bp.params["dr_sq"]
        print(f"# In src/football_elo/worldcup.py and docs/js/bracket.js:")
        print(f"GOAL_BASELINE        = {mu:.4f}")
        print(f"GOAL_ELO_SCALING     = {c:.6f}")
        print(f"GOAL_ELO_SCALING_SQ  = {c2:.3e}")
        print(f"# Update _expected_goals (worldcup.py) and simScore (bracket.js):")
        print(f"#   lam = mu * exp(c * dr + c2 * dr**2)")
    else:
        d = res_b.params["is_home"]
        print(f"# Spec B's home dummy ({d:+.4f} log-goals) is for diagnostics —")
        print(f"# production uses Spec B' (no home dummy) to keep _expected_goals")
        print(f"# symmetric. Elo's +50 ha stays the rating-side encoding.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(
        prog="football-elo-calibrate",
        description="Fit the Poisson goal model used by the WC simulator.",
    )
    p.add_argument("--gender", default="men", choices=["men", "women"])
    p.add_argument("--since", type=int, default=1990,
                   help="Drop matches before this calendar year (default 1990)")
    p.add_argument("--no-friendlies", action="store_true",
                   help="Drop tournament == 'Friendly' from the fit sample")
    p.add_argument("--adopt", choices=["A", "B", "Bp"], default="Bp",
                   help="Which spec's constants to print for copy-paste "
                        "(default Bp: parsimonious quadratic, what production uses)")
    args = p.parse_args()

    print(f"Replaying Elo on {args.gender}'s match history...")
    snaps = replay_with_snapshots(gender=args.gender)
    print(f"  {len(snaps):,} matches replayed")

    df = build_team_match_rows(snaps)

    n_before = len(df)
    df = df[df["date"].dt.year >= args.since]
    if args.no_friendlies:
        df = df[df["tournament"] != "Friendly"]
    df = df.reset_index(drop=True)
    print(f"  {len(df):,} of {n_before:,} team-match rows after filters "
          f"(since={args.since}, no_friendlies={args.no_friendlies})")

    res_a = fit_spec_a(df)
    res_b = fit_spec_b(df)
    res_bp = fit_spec_bp(df)

    _print_fit("Spec A: goals ~ 1 + dr", res_a)
    _print_calibration_table("Spec A", df, predict_spec_a(res_a, df))

    _print_fit("Spec B: goals ~ 1 + dr + dr^2 + is_home", res_b)
    _print_calibration_table("Spec B", df, predict_spec_b(res_b, df))

    _print_fit("Spec B': goals ~ 1 + dr + dr^2  (production)", res_bp)
    _print_calibration_table("Spec B'", df, predict_spec_bp(res_bp, df))

    print(f"\n  Empirical mean goals (overall): {df['goals'].mean():.3f}")
    print(f"  Empirical P(team scores >= 6):  {(df['goals'] >= 6).mean():.4f}")

    _print_constants(res_a, res_b, res_bp, args.adopt)


if __name__ == "__main__":
    main()
