"""Unit tests for Elo math functions."""

import math
import pytest
from football_elo.elo import (
    expected_result,
    goal_difference_index,
    match_result_value,
    compute_rating_change,
)


class TestExpectedResult:
    def test_equal_ratings(self):
        assert expected_result(1500, 1500) == pytest.approx(0.5)

    def test_higher_rated_team(self):
        we = expected_result(1600, 1400)
        assert we == pytest.approx(0.7597, abs=0.001)

    def test_lower_rated_team(self):
        we = expected_result(1400, 1600)
        assert we == pytest.approx(0.2403, abs=0.001)

    def test_symmetry(self):
        """Expected results for both teams sum to 1."""
        we_a = expected_result(1700, 1500)
        we_b = expected_result(1500, 1700)
        assert we_a + we_b == pytest.approx(1.0)

    def test_large_difference(self):
        we = expected_result(2000, 1200)
        assert we > 0.99

    def test_dr_120(self):
        """dr=120 should give approximately 0.666."""
        we = expected_result(1560, 1440)
        assert we == pytest.approx(0.666, abs=0.01)


class TestGoalDifferenceIndex:
    def test_draw(self):
        assert goal_difference_index(0) == 1.0

    def test_one_goal(self):
        assert goal_difference_index(1) == 1.0
        assert goal_difference_index(-1) == 1.0

    def test_two_goals(self):
        assert goal_difference_index(2) == 1.5
        assert goal_difference_index(-2) == 1.5

    def test_three_goals(self):
        assert goal_difference_index(3) == 1.75

    def test_five_goals(self):
        assert goal_difference_index(5) == 1.75  # capped

    def test_ten_goals(self):
        assert goal_difference_index(10) == 1.75  # capped

    def test_eleven_goals(self):
        assert goal_difference_index(11) == 1.75  # capped


class TestMatchResultValue:
    def test_home_win(self):
        assert match_result_value(3, 1, None, "A", "B") == (1.0, 0.0)

    def test_away_win(self):
        assert match_result_value(0, 2, None, "A", "B") == (0.0, 1.0)

    def test_draw(self):
        assert match_result_value(1, 1, None, "A", "B") == (0.5, 0.5)

    def test_shootout_treated_as_draw(self):
        assert match_result_value(2, 2, "A", "A", "B") == (0.5, 0.5)
        assert match_result_value(2, 2, "B", "A", "B") == (0.5, 0.5)


class TestComputeRatingChange:
    def test_zero_sum(self):
        """Rating changes must sum to zero."""
        d_home, d_away = compute_rating_change(
            1600, 1400, 2, 1, k_factor=40, is_neutral=False
        )
        assert d_home + d_away == pytest.approx(0.0)

    def test_zero_sum_neutral(self):
        d_home, d_away = compute_rating_change(
            1600, 1400, 0, 3, k_factor=60, is_neutral=True
        )
        assert d_home + d_away == pytest.approx(0.0)

    def test_zero_sum_draw(self):
        d_home, d_away = compute_rating_change(
            1500, 1500, 1, 1, k_factor=30, is_neutral=True
        )
        assert d_home + d_away == pytest.approx(0.0)
        assert d_home == pytest.approx(0.0)  # Equal teams, draw -> no change

    def test_upset_gives_large_change(self):
        """A weak team beating a strong team at a neutral venue."""
        d_home, d_away = compute_rating_change(
            1300, 1700, 1, 0, k_factor=60, is_neutral=True
        )
        assert d_home > 0  # Weak team gains
        assert d_away < 0  # Strong team loses
        assert d_home > 40  # Should be a large gain

    def test_expected_win_gives_small_change(self):
        """A strong team winning as expected."""
        d_home, d_away = compute_rating_change(
            1700, 1300, 1, 0, k_factor=20, is_neutral=True
        )
        assert d_home > 0  # Still gains, but...
        assert d_home < 5  # Small gain

    def test_neutral_vs_home(self):
        """Home advantage should shift expected results."""
        d_neutral, _ = compute_rating_change(
            1500, 1500, 2, 1, k_factor=40, is_neutral=True
        )
        d_home, _ = compute_rating_change(
            1500, 1500, 2, 1, k_factor=40, is_neutral=False
        )
        # Home team winning at home is more expected, so less reward
        assert d_home < d_neutral

    def test_shootout_result(self):
        """Shootout should be treated as draw for rating purposes."""
        d_home, d_away = compute_rating_change(
            1500, 1500, 1, 1, k_factor=60, is_neutral=True,
            shootout_winner="A", home_team="A", away_team="B"
        )
        assert d_home == pytest.approx(0.0)
        assert d_away == pytest.approx(0.0)

    def test_big_goal_difference_amplifies(self):
        """Larger goal difference should give larger rating change."""
        d1, _ = compute_rating_change(
            1500, 1500, 1, 0, k_factor=40, is_neutral=True
        )
        d5, _ = compute_rating_change(
            1500, 1500, 5, 0, k_factor=40, is_neutral=True
        )
        assert d5 > d1
