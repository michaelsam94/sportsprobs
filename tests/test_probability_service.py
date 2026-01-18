"""Unit tests for probability calculation service."""

import pytest
import math
from app.application.services.probability_service import (
    ProbabilityService,
    MatchProbabilities,
    ExpectedGoals,
)


class TestPoissonDistribution:
    """Tests for Poisson distribution calculations."""

    def test_poisson_probability_basic(self):
        """Test basic Poisson probability calculation."""
        # P(2; 2.5) = (2.5^2 * e^(-2.5)) / 2!
        result = ProbabilityService.poisson_probability(2.5, 2)
        expected = (2.5 ** 2 * math.exp(-2.5)) / math.factorial(2)
        assert abs(result - expected) < 1e-10

    def test_poisson_probability_zero_occurrences(self):
        """Test Poisson probability for zero occurrences."""
        result = ProbabilityService.poisson_probability(1.5, 0)
        expected = math.exp(-1.5)
        assert abs(result - expected) < 1e-10

    def test_poisson_probability_zero_lambda(self):
        """Test Poisson probability with zero lambda."""
        result = ProbabilityService.poisson_probability(0, 0)
        assert result == 1.0

        result = ProbabilityService.poisson_probability(0, 1)
        assert result == 0.0

    def test_poisson_probability_negative_lambda(self):
        """Test that negative lambda raises ValueError."""
        with pytest.raises(ValueError):
            ProbabilityService.poisson_probability(-1, 2)

    def test_poisson_probability_negative_k(self):
        """Test that negative k raises ValueError."""
        with pytest.raises(ValueError):
            ProbabilityService.poisson_probability(2.5, -1)

    def test_poisson_cumulative(self):
        """Test cumulative Poisson probability."""
        result = ProbabilityService.poisson_cumulative(2.0, 2)
        # Should be sum of P(0), P(1), P(2)
        expected = (
            ProbabilityService.poisson_probability(2.0, 0) +
            ProbabilityService.poisson_probability(2.0, 1) +
            ProbabilityService.poisson_probability(2.0, 2)
        )
        assert abs(result - expected) < 1e-10

    def test_poisson_cumulative_zero_k(self):
        """Test cumulative Poisson with k=0."""
        result = ProbabilityService.poisson_cumulative(2.0, 0)
        expected = ProbabilityService.poisson_probability(2.0, 0)
        assert abs(result - expected) < 1e-10

    def test_poisson_cumulative_negative_k(self):
        """Test cumulative Poisson with negative k."""
        result = ProbabilityService.poisson_cumulative(2.0, -1)
        assert result == 0.0


class TestExpectedGoals:
    """Tests for expected goals (xG) calculation."""

    def test_calculate_expected_goals_home(self):
        """Test xG calculation for home team."""
        xg = ProbabilityService.calculate_expected_goals(
            team_goals_for_avg=1.8,
            team_goals_against_avg=1.2,
            opponent_goals_for_avg=1.5,
            opponent_goals_against_avg=1.3,
            league_avg_goals=2.5,
            home_advantage=0.3,
            is_home=True,
        )

        # Expected: (1.8 * 1.3) / 2.5 + 0.3 = 0.936 + 0.3 = 1.236
        expected = (1.8 * 1.3) / 2.5 + 0.3
        assert abs(xg - expected) < 1e-6

    def test_calculate_expected_goals_away(self):
        """Test xG calculation for away team."""
        xg = ProbabilityService.calculate_expected_goals(
            team_goals_for_avg=1.5,
            team_goals_against_avg=1.3,
            opponent_goals_for_avg=1.8,
            opponent_goals_against_avg=1.2,
            league_avg_goals=2.5,
            home_advantage=0.3,
            is_home=False,
        )

        # Expected: (1.5 * 1.2) / 2.5 - 0.15 = 0.72 - 0.15 = 0.57
        expected = (1.5 * 1.2) / 2.5 - 0.15
        assert abs(xg - expected) < 1e-6

    def test_calculate_expected_goals_no_home_advantage(self):
        """Test xG calculation without home advantage."""
        xg_home = ProbabilityService.calculate_expected_goals(
            team_goals_for_avg=1.5,
            team_goals_against_avg=1.0,
            opponent_goals_for_avg=1.5,
            opponent_goals_against_avg=1.0,
            league_avg_goals=2.5,
            home_advantage=0.0,
            is_home=True,
        )

        xg_away = ProbabilityService.calculate_expected_goals(
            team_goals_for_avg=1.5,
            team_goals_against_avg=1.0,
            opponent_goals_for_avg=1.5,
            opponent_goals_against_avg=1.0,
            league_avg_goals=2.5,
            home_advantage=0.0,
            is_home=False,
        )

        # Should be equal without home advantage
        assert abs(xg_home - xg_away) < 1e-6

    def test_calculate_expected_goals_negative_values(self):
        """Test that negative values raise ValueError."""
        with pytest.raises(ValueError):
            ProbabilityService.calculate_expected_goals(
                team_goals_for_avg=-1.0,
                team_goals_against_avg=1.0,
                opponent_goals_for_avg=1.0,
                opponent_goals_against_avg=1.0,
            )

    def test_calculate_expected_goals_zero_league_avg(self):
        """Test that zero league average raises ValueError."""
        with pytest.raises(ValueError):
            ProbabilityService.calculate_expected_goals(
                team_goals_for_avg=1.0,
                team_goals_against_avg=1.0,
                opponent_goals_for_avg=1.0,
                opponent_goals_against_avg=1.0,
                league_avg_goals=0.0,
            )

    def test_calculate_expected_goals_non_negative_result(self):
        """Test that xG is always non-negative."""
        xg = ProbabilityService.calculate_expected_goals(
            team_goals_for_avg=0.1,
            team_goals_against_avg=0.1,
            opponent_goals_for_avg=0.1,
            opponent_goals_against_avg=0.1,
            league_avg_goals=2.5,
            home_advantage=0.0,
            is_home=False,
        )
        assert xg >= 0.0


class TestMatchProbabilities:
    """Tests for match outcome probability calculations."""

    def test_calculate_match_probabilities_basic(self):
        """Test basic match probability calculation."""
        probs = ProbabilityService.calculate_match_probabilities(
            home_xg=1.5,
            away_xg=1.0,
        )

        # Probabilities should sum to approximately 1.0
        total = probs.home_win + probs.draw + probs.away_win
        assert abs(total - 1.0) < 0.01

        # Home should be more likely to win with higher xG
        assert probs.home_win > probs.away_win

    def test_calculate_match_probabilities_equal_xg(self):
        """Test match probabilities with equal xG."""
        probs = ProbabilityService.calculate_match_probabilities(
            home_xg=1.5,
            away_xg=1.5,
        )

        # With equal xG, home should still have slight advantage
        # but draw should be most likely
        assert probs.draw > probs.away_win
        # Home advantage makes home_win > away_win even with equal xG

    def test_calculate_match_probabilities_high_xg(self):
        """Test match probabilities with high xG values."""
        probs = ProbabilityService.calculate_match_probabilities(
            home_xg=3.0,
            away_xg=1.0,
        )

        # Home should be heavily favored
        assert probs.home_win > 0.7
        assert probs.away_win < 0.1

    def test_calculate_match_probabilities_total_goals(self):
        """Test total goals probabilities."""
        probs = ProbabilityService.calculate_match_probabilities(
            home_xg=1.5,
            away_xg=1.0,
        )

        # Total goals probabilities should sum to approximately 1.0
        total = (
            probs.total_goals_0 +
            probs.total_goals_1 +
            probs.total_goals_2 +
            probs.total_goals_3 +
            probs.total_goals_4_plus
        )
        assert abs(total - 1.0) < 0.01

    def test_calculate_match_probabilities_over_under(self):
        """Test over/under 2.5 goals probabilities."""
        probs = ProbabilityService.calculate_match_probabilities(
            home_xg=1.5,
            away_xg=1.0,
        )

        # Over and under should sum to 1.0
        total = probs.over_2_5_goals + probs.under_2_5_goals
        assert abs(total - 1.0) < 0.01

    def test_calculate_match_probabilities_both_teams_score(self):
        """Test both teams score probability."""
        probs = ProbabilityService.calculate_match_probabilities(
            home_xg=1.5,
            away_xg=1.0,
        )

        # Both teams score should be between 0 and 1
        assert 0.0 <= probs.both_teams_score <= 1.0

    def test_calculate_match_probabilities_negative_xg(self):
        """Test that negative xG raises ValueError."""
        with pytest.raises(ValueError):
            ProbabilityService.calculate_match_probabilities(
                home_xg=-1.0,
                away_xg=1.0,
            )

    def test_calculate_match_probabilities_zero_xg(self):
        """Test match probabilities with zero xG."""
        probs = ProbabilityService.calculate_match_probabilities(
            home_xg=0.0,
            away_xg=0.0,
        )

        # Should be a 0-0 draw
        assert probs.draw == 1.0
        assert probs.home_win == 0.0
        assert probs.away_win == 0.0


class TestCombinedCalculations:
    """Tests for combined probability calculations."""

    def test_calculate_probabilities_from_stats(self):
        """Test combined calculation from statistics."""
        xg, probs = ProbabilityService.calculate_probabilities_from_stats(
            home_goals_for_avg=1.8,
            home_goals_against_avg=1.2,
            away_goals_for_avg=1.5,
            away_goals_against_avg=1.3,
        )

        assert isinstance(xg, ExpectedGoals)
        assert isinstance(probs, MatchProbabilities)
        assert xg.home_xg > 0
        assert xg.away_xg > 0
        assert abs(probs.home_win + probs.draw + probs.away_win - 1.0) < 0.01

    def test_get_most_likely_scoreline(self):
        """Test getting most likely scoreline."""
        home_goals, away_goals, probability = ProbabilityService.get_most_likely_scoreline(
            home_xg=1.5,
            away_xg=1.0,
        )

        assert isinstance(home_goals, int)
        assert isinstance(away_goals, int)
        assert 0.0 <= probability <= 1.0
        assert home_goals >= 0
        assert away_goals >= 0

    def test_get_scoreline_probability(self):
        """Test getting probability of specific scoreline."""
        prob = ProbabilityService.get_scoreline_probability(
            home_xg=1.5,
            away_xg=1.0,
            home_goals=2,
            away_goals=1,
        )

        assert 0.0 <= prob <= 1.0

        # Should match manual calculation
        expected = (
            ProbabilityService.poisson_probability(1.5, 2) *
            ProbabilityService.poisson_probability(1.0, 1)
        )
        assert abs(prob - expected) < 1e-10


class TestDeterministic:
    """Tests to ensure deterministic behavior."""

    def test_deterministic_poisson(self):
        """Test that Poisson calculations are deterministic."""
        result1 = ProbabilityService.poisson_probability(2.5, 2)
        result2 = ProbabilityService.poisson_probability(2.5, 2)
        assert result1 == result2

    def test_deterministic_xg(self):
        """Test that xG calculations are deterministic."""
        result1 = ProbabilityService.calculate_expected_goals(
            team_goals_for_avg=1.5,
            team_goals_against_avg=1.0,
            opponent_goals_for_avg=1.5,
            opponent_goals_against_avg=1.0,
        )
        result2 = ProbabilityService.calculate_expected_goals(
            team_goals_for_avg=1.5,
            team_goals_against_avg=1.0,
            opponent_goals_for_avg=1.5,
            opponent_goals_against_avg=1.0,
        )
        assert result1 == result2

    def test_deterministic_probabilities(self):
        """Test that probability calculations are deterministic."""
        result1 = ProbabilityService.calculate_match_probabilities(1.5, 1.0)
        result2 = ProbabilityService.calculate_match_probabilities(1.5, 1.0)

        assert result1.home_win == result2.home_win
        assert result1.draw == result2.draw
        assert result1.away_win == result2.away_win


class TestStateless:
    """Tests to ensure stateless behavior."""

    def test_stateless_service(self):
        """Test that service is stateless (no instance variables)."""
        # All methods are static, so service is stateless
        # This is verified by the fact that we can call methods without
        # creating an instance
        result = ProbabilityService.poisson_probability(2.5, 2)
        assert result is not None

    def test_no_side_effects(self):
        """Test that methods have no side effects."""
        # Call method multiple times with same inputs
        result1 = ProbabilityService.calculate_match_probabilities(1.5, 1.0)
        result2 = ProbabilityService.calculate_match_probabilities(1.5, 1.0)

        # Results should be identical
        assert result1.home_win == result2.home_win


class TestEdgeCases:
    """Tests for edge cases."""

    def test_very_high_xg(self):
        """Test with very high xG values."""
        probs = ProbabilityService.calculate_match_probabilities(
            home_xg=10.0,
            away_xg=0.5,
        )

        # Home should be heavily favored
        assert probs.home_win > 0.99

    def test_very_low_xg(self):
        """Test with very low xG values."""
        probs = ProbabilityService.calculate_match_probabilities(
            home_xg=0.1,
            away_xg=0.1,
        )

        # Should be mostly 0-0 draws
        assert probs.draw > 0.8
        assert probs.total_goals_0 > 0.8

    def test_max_goals_parameter(self):
        """Test max_goals parameter."""
        probs_low = ProbabilityService.calculate_match_probabilities(
            home_xg=2.0,
            away_xg=2.0,
            max_goals=5,
        )

        probs_high = ProbabilityService.calculate_match_probabilities(
            home_xg=2.0,
            away_xg=2.0,
            max_goals=10,
        )

        # Higher max_goals should capture more probability mass
        # (though difference should be small for reasonable xG)
        total_low = probs_low.home_win + probs_low.draw + probs_low.away_win
        total_high = probs_high.home_win + probs_high.draw + probs_high.away_win

        # Both should be close to 1.0, but high should be closer
        assert abs(total_high - 1.0) <= abs(total_low - 1.0)

