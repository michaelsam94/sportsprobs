"""Probability calculation service for sports analytics.

This service provides deterministic, stateless probability calculations
for match outcomes using Poisson distribution and expected goals (xG).
"""

import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MatchProbabilities:
    """Match outcome probabilities."""

    home_win: float
    draw: float
    away_win: float
    total_goals_0: float
    total_goals_1: float
    total_goals_2: float
    total_goals_3: float
    total_goals_4_plus: float
    both_teams_score: float
    over_2_5_goals: float
    under_2_5_goals: float


@dataclass
class ExpectedGoals:
    """Expected goals for a team."""

    home_xg: float
    away_xg: float


class ProbabilityService:
    """Service for calculating match outcome probabilities."""

    @staticmethod
    def poisson_probability(lambda_param: float, k: int) -> float:
        """Calculate Poisson probability.

        Poisson distribution models the probability of a given number of events
        occurring in a fixed interval of time or space.

        Formula: P(k; λ) = (λ^k * e^(-λ)) / k!

        Args:
            lambda_param: Average rate (expected value)
            k: Number of occurrences

        Returns:
            Probability of exactly k occurrences

        Example:
            >>> ProbabilityService.poisson_probability(2.5, 2)
            0.25651562049999994
        """
        if lambda_param < 0:
            raise ValueError("Lambda parameter must be non-negative")
        if k < 0:
            raise ValueError("k must be non-negative")

        if lambda_param == 0:
            return 1.0 if k == 0 else 0.0

        # Calculate: (λ^k * e^(-λ)) / k!
        log_prob = k * math.log(lambda_param) - lambda_param - math.lgamma(k + 1)
        return math.exp(log_prob)

    @staticmethod
    def poisson_cumulative(lambda_param: float, k: int) -> float:
        """Calculate cumulative Poisson probability (P(X <= k)).

        Args:
            lambda_param: Average rate
            k: Maximum number of occurrences

        Returns:
            Probability of k or fewer occurrences
        """
        if lambda_param < 0:
            raise ValueError("Lambda parameter must be non-negative")
        if k < 0:
            return 0.0

        cumulative = 0.0
        for i in range(k + 1):
            cumulative += ProbabilityService.poisson_probability(lambda_param, i)

        return cumulative

    @staticmethod
    def calculate_expected_goals(
        team_goals_for_avg: float,
        team_goals_against_avg: float,
        opponent_goals_for_avg: float,
        opponent_goals_against_avg: float,
        league_avg_goals: float = 2.5,
        home_advantage: float = 0.3,
        is_home: bool = True,
    ) -> float:
        """Calculate expected goals (xG) for a team.

        Uses a simplified xG model based on:
        - Team's average goals scored
        - Opponent's average goals conceded
        - League average goals
        - Home advantage (if applicable)

        Formula:
        xG = (team_goals_for_avg * opponent_goals_against_avg) / league_avg_goals
        If home: xG += home_advantage

        Args:
            team_goals_for_avg: Team's average goals scored per match
            team_goals_against_avg: Team's average goals conceded per match
            opponent_goals_for_avg: Opponent's average goals scored per match
            opponent_goals_against_avg: Opponent's average goals conceded per match
            league_avg_goals: League average goals per match (default: 2.5)
            home_advantage: Home advantage factor (default: 0.3)
            is_home: Whether team is playing at home

        Returns:
            Expected goals for the team

        Example:
            >>> xg = ProbabilityService.calculate_expected_goals(
            ...     team_goals_for_avg=1.8,
            ...     team_goals_against_avg=1.2,
            ...     opponent_goals_for_avg=1.5,
            ...     opponent_goals_against_avg=1.3,
            ...     is_home=True
            ... )
        """
        if any(x < 0 for x in [team_goals_for_avg, team_goals_against_avg,
                                opponent_goals_for_avg, opponent_goals_against_avg,
                                league_avg_goals]):
            raise ValueError("All goal averages must be non-negative")

        if league_avg_goals == 0:
            raise ValueError("League average goals cannot be zero")

        # Calculate base xG
        xg = (team_goals_for_avg * opponent_goals_against_avg) / league_avg_goals

        # Apply home advantage
        if is_home:
            xg += home_advantage
        else:
            # Slight disadvantage for away team
            xg -= (home_advantage * 0.5)

        # Ensure xG is non-negative
        return max(0.0, xg)

    @staticmethod
    def calculate_match_probabilities(
        home_xg: float,
        away_xg: float,
        max_goals: int = 10,
    ) -> MatchProbabilities:
        """Calculate match outcome probabilities using Poisson distribution.

        Uses independent Poisson distributions for home and away goals,
        then calculates probabilities for all possible scorelines.

        Args:
            home_xg: Expected goals for home team
            away_xg: Expected goals for away team
            max_goals: Maximum goals to consider (default: 10)

        Returns:
            MatchProbabilities object with all calculated probabilities

        Example:
            >>> probs = ProbabilityService.calculate_match_probabilities(
            ...     home_xg=1.8,
            ...     away_xg=1.2
            ... )
            >>> probs.home_win
            0.45...
        """
        if home_xg < 0 or away_xg < 0:
            raise ValueError("Expected goals must be non-negative")

        # Initialize probabilities
        home_win_prob = 0.0
        draw_prob = 0.0
        away_win_prob = 0.0
        total_goals_probs = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        both_teams_score_prob = 0.0
        over_2_5_prob = 0.0
        under_2_5_prob = 0.0

        # Calculate probabilities for all possible scorelines
        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                # Probability of this exact scoreline
                prob = (
                    ProbabilityService.poisson_probability(home_xg, home_goals) *
                    ProbabilityService.poisson_probability(away_xg, away_goals)
                )

                # Match outcome probabilities
                if home_goals > away_goals:
                    home_win_prob += prob
                elif home_goals == away_goals:
                    draw_prob += prob
                else:
                    away_win_prob += prob

                # Total goals probabilities
                total_goals = home_goals + away_goals
                if total_goals <= 4:
                    total_goals_probs[total_goals] += prob
                else:
                    total_goals_probs[4] += prob  # 4+ goals

                # Both teams score
                if home_goals > 0 and away_goals > 0:
                    both_teams_score_prob += prob

                # Over/Under 2.5 goals
                if total_goals > 2.5:
                    over_2_5_prob += prob
                else:
                    under_2_5_prob += prob

        return MatchProbabilities(
            home_win=home_win_prob,
            draw=draw_prob,
            away_win=away_win_prob,
            total_goals_0=total_goals_probs[0],
            total_goals_1=total_goals_probs[1],
            total_goals_2=total_goals_probs[2],
            total_goals_3=total_goals_probs[3],
            total_goals_4_plus=total_goals_probs[4],
            both_teams_score=both_teams_score_prob,
            over_2_5_goals=over_2_5_prob,
            under_2_5_goals=under_2_5_prob,
        )

    @staticmethod
    def calculate_probabilities_from_stats(
        home_goals_for_avg: float,
        home_goals_against_avg: float,
        away_goals_for_avg: float,
        away_goals_against_avg: float,
        league_avg_goals: float = 2.5,
        home_advantage: float = 0.3,
        max_goals: int = 10,
    ) -> Tuple[ExpectedGoals, MatchProbabilities]:
        """Calculate probabilities from team statistics.

        Convenience method that combines xG calculation and probability calculation.

        Args:
            home_goals_for_avg: Home team's average goals scored
            home_goals_against_avg: Home team's average goals conceded
            away_goals_for_avg: Away team's average goals scored
            away_goals_against_avg: Away team's average goals conceded
            league_avg_goals: League average goals per match
            home_advantage: Home advantage factor
            max_goals: Maximum goals to consider in calculations

        Returns:
            Tuple of (ExpectedGoals, MatchProbabilities)

        Example:
            >>> xg, probs = ProbabilityService.calculate_probabilities_from_stats(
            ...     home_goals_for_avg=1.8,
            ...     home_goals_against_avg=1.2,
            ...     away_goals_for_avg=1.5,
            ...     away_goals_against_avg=1.3
            ... )
        """
        # Calculate expected goals
        home_xg = ProbabilityService.calculate_expected_goals(
            team_goals_for_avg=home_goals_for_avg,
            team_goals_against_avg=home_goals_against_avg,
            opponent_goals_for_avg=away_goals_for_avg,
            opponent_goals_against_avg=away_goals_against_avg,
            league_avg_goals=league_avg_goals,
            home_advantage=home_advantage,
            is_home=True,
        )

        away_xg = ProbabilityService.calculate_expected_goals(
            team_goals_for_avg=away_goals_for_avg,
            team_goals_against_avg=away_goals_against_avg,
            opponent_goals_for_avg=home_goals_for_avg,
            opponent_goals_against_avg=home_goals_against_avg,
            league_avg_goals=league_avg_goals,
            home_advantage=home_advantage,
            is_home=False,
        )

        # Calculate match probabilities
        probabilities = ProbabilityService.calculate_match_probabilities(
            home_xg=home_xg,
            away_xg=away_xg,
            max_goals=max_goals,
        )

        return ExpectedGoals(home_xg=home_xg, away_xg=away_xg), probabilities

    @staticmethod
    def get_most_likely_scoreline(
        home_xg: float,
        away_xg: float,
        max_goals: int = 10,
    ) -> Tuple[int, int, float]:
        """Get the most likely scoreline.

        Args:
            home_xg: Expected goals for home team
            away_xg: Expected goals for away team
            max_goals: Maximum goals to consider

        Returns:
            Tuple of (home_goals, away_goals, probability)
        """
        max_prob = 0.0
        most_likely = (0, 0)

        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                prob = (
                    ProbabilityService.poisson_probability(home_xg, home_goals) *
                    ProbabilityService.poisson_probability(away_xg, away_goals)
                )

                if prob > max_prob:
                    max_prob = prob
                    most_likely = (home_goals, away_goals)

        return most_likely[0], most_likely[1], max_prob

    @staticmethod
    def get_scoreline_probability(
        home_xg: float,
        away_xg: float,
        home_goals: int,
        away_goals: int,
    ) -> float:
        """Get probability of a specific scoreline.

        Args:
            home_xg: Expected goals for home team
            away_xg: Expected goals for away team
            home_goals: Home team goals
            away_goals: Away team goals

        Returns:
            Probability of the exact scoreline
        """
        return (
            ProbabilityService.poisson_probability(home_xg, home_goals) *
            ProbabilityService.poisson_probability(away_xg, away_goals)
        )

