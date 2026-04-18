"""Player-level talent adjustment: correct TM value for age bias.

The thesis: Transfermarkt values discount aging players more aggressively than
on-field performance actually declines. A 37-year-old Messi has a TM value of
~€20M, but his on-field contribution is still top-tier. We want to recover a
"performance-age-corrected" score that captures current contribution.

Approach: fit a discount curve `discount(age) = E[value(age) / peak_value]`
empirically from the dcaribou player_valuations history. A player's
adjusted value at age `a` is `value / discount(a)`, which renormalizes back
to "peak equivalent talent."

For predicting tournament performance (not latent talent), we then apply a
shallower performance decline curve from the literature. The two-step
separation lets us keep the TM-specific bias separate from on-field aging.
"""

from __future__ import annotations

import math
import numpy as np
import pandas as pd


# Literature-based on-field performance age curve.
# Peak around 27; gentle decline through mid-30s; steeper thereafter.
# Sources: Dendir 2016, Brander 2014 — mid-point of published estimates.
def performance_age_factor(age: float) -> float:
    """Expected on-field performance vs peak (peak = 1.0)."""
    if age <= 27:
        # Pre-peak: small rise from age 21
        return max(0.85, 1.0 - 0.02 * max(0, 27 - age))
    # Post-peak: 2% decline per year ages 28–32, 4% per year 33–36, 7% per year 37+
    if age <= 32:
        return 1.0 - 0.02 * (age - 27)
    if age <= 36:
        return 0.90 - 0.04 * (age - 32)
    return max(0.40, 0.74 - 0.07 * (age - 36))


def fit_tm_age_discount(valuation_history: pd.DataFrame, min_history_years: int = 8) -> dict[int, float]:
    """Empirical TM age-discount curve: E[value(age) / peak] by integer age.

    valuation_history: columns ['player_id', 'age', 'value'] (rows = one
    valuation observation per player per date).

    Returns dict age -> discount factor (in [0, 1]).
    """
    # Per-player peak
    peaks = valuation_history.groupby('player_id')['value'].max()
    vh = valuation_history.join(peaks.rename('peak'), on='player_id')
    vh = vh[vh['peak'] > 0].copy()
    vh['ratio'] = vh['value'] / vh['peak']

    # Require the player to have a sufficiently long history so the peak is meaningful
    life_years = vh.groupby('player_id')['age'].agg(lambda a: a.max() - a.min())
    keep_ids = life_years[life_years >= min_history_years].index
    vh = vh[vh['player_id'].isin(keep_ids)]

    # Bin by integer age, take mean ratio
    vh['age_int'] = vh['age'].astype(int)
    curve = vh.groupby('age_int')['ratio'].mean().to_dict()
    return curve


def tm_age_discount(age: float, curve: dict[int, float] | None = None) -> float:
    """Look up TM age discount; linear interpolation between integer ages.

    If curve is None, uses a built-in approximation of the fitted curve
    (conservative fallback).
    """
    if curve is None:
        # Built-in approximation of TM aging, calibrated from spot checks.
        # TM is aggressive: ~25%/year decline over 32.
        return _builtin_tm_discount(age)
    lo, hi = int(math.floor(age)), int(math.ceil(age))
    d_lo = curve.get(lo, _builtin_tm_discount(lo))
    if lo == hi:
        return d_lo
    d_hi = curve.get(hi, _builtin_tm_discount(hi))
    t = age - lo
    return d_lo * (1 - t) + d_hi * t


def _builtin_tm_discount(age: float) -> float:
    """Fallback TM age-discount curve when empirical fit is unavailable."""
    if age <= 26:
        return 1.0
    if age <= 32:
        return 1.0 - 0.06 * (age - 26)  # 6%/yr
    return max(0.10, 0.64 - 0.15 * (age - 32))  # 15%/yr after 32


def adjusted_value(value: float, age: float,
                   tm_curve: dict[int, float] | None = None) -> float:
    """Convert a current TM value into a performance-scaled score.

    Step 1: recover peak-equivalent talent by dividing out TM's age discount.
    Step 2: scale down by the on-field performance age factor for current
    tournament contribution.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return float('nan')
    if value <= 0:
        return 0.0
    latent = value / tm_age_discount(age, tm_curve)
    return latent * performance_age_factor(age)
