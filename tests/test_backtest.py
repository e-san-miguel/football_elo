"""Unit tests for backtest math and age-adjustment functions."""

import pytest

from football_elo.backtest import _match_scores
from football_elo.player_strength import (
    performance_age_factor,
    _builtin_tm_discount,
    adjusted_value,
)
from football_elo.squad_strength import z_scores


class TestMatchScores:
    def test_perfect_prediction(self):
        # Predict certain home win, home wins
        brier, loss = _match_scores(1.0, 0.0, 0.0, 2, 0)
        assert brier == pytest.approx(0.0)
        assert loss == pytest.approx(0.0)

    def test_totally_wrong(self):
        # Predict certain away win, home wins instead
        brier, loss = _match_scores(0.0, 0.0, 1.0, 2, 0)
        assert brier == pytest.approx(2.0)
        assert loss > 10  # -log(eps) is huge

    def test_uniform_prediction_home_win(self):
        # 1/3 each way, home wins
        brier, _ = _match_scores(1/3, 1/3, 1/3, 1, 0)
        expected = (1/3 - 1)**2 + (1/3)**2 + (1/3)**2
        assert brier == pytest.approx(expected)

    def test_draw_outcome(self):
        # Predict 50/30/20, draw happens
        brier, loss = _match_scores(0.5, 0.3, 0.2, 1, 1)
        assert brier == pytest.approx(0.5**2 + 0.7**2 + 0.2**2)


class TestAgeCurves:
    def test_performance_peak_at_27(self):
        factors = [performance_age_factor(a) for a in range(20, 40)]
        peak_idx = max(range(len(factors)), key=lambda i: factors[i])
        peak_age = 20 + peak_idx
        assert 25 <= peak_age <= 28

    def test_performance_monotonic_post_peak(self):
        ages = list(range(28, 40))
        factors = [performance_age_factor(a) for a in ages]
        # Strictly non-increasing after 28
        assert all(factors[i] >= factors[i+1] for i in range(len(factors)-1))

    def test_tm_discount_monotonic_post_peak(self):
        ages = list(range(27, 40))
        discounts = [_builtin_tm_discount(a) for a in ages]
        assert all(discounts[i] >= discounts[i+1] for i in range(len(discounts)-1))

    def test_tm_discount_more_aggressive_than_performance(self):
        # At age 36: TM discount should be lower than performance factor
        assert _builtin_tm_discount(36) < performance_age_factor(36)

    def test_adjusted_value_inflates_old_stars(self):
        # Old Messi: €10M at age 37
        v_young = adjusted_value(100e6, 27)
        v_old = adjusted_value(10e6, 37)
        # Old-star adjusted value should still be meaningful, not ~zero
        assert v_old > 15e6


class TestZScores:
    def test_basic(self):
        scores = {"A": 100, "B": 200, "C": 300}
        z = z_scores(scores)
        assert z["A"] < z["B"] < z["C"]
        assert sum(z.values()) == pytest.approx(0.0, abs=1e-9)

    def test_all_equal(self):
        z = z_scores({"A": 5, "B": 5, "C": 5})
        assert all(v == 0.0 for v in z.values())

    def test_empty(self):
        assert z_scores({}) == {}
