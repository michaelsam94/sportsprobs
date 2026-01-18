# Probability Service Usage Examples

## Quick Start

```python
from app.application.services.probability_service import (
    ProbabilityService,
    MatchProbabilities,
    ExpectedGoals,
)
```

## Basic Usage

### 1. Calculate Expected Goals (xG)

```python
# Calculate xG for home team
home_xg = ProbabilityService.calculate_expected_goals(
    team_goals_for_avg=1.8,      # Team's average goals scored
    team_goals_against_avg=1.2,  # Team's average goals conceded
    opponent_goals_for_avg=1.5,  # Opponent's average goals scored
    opponent_goals_against_avg=1.3,  # Opponent's average goals conceded
    league_avg_goals=2.5,        # League average goals per match
    home_advantage=0.3,          # Home advantage factor
    is_home=True,                # Playing at home
)

# Calculate xG for away team
away_xg = ProbabilityService.calculate_expected_goals(
    team_goals_for_avg=1.5,
    team_goals_against_avg=1.3,
    opponent_goals_for_avg=1.8,
    opponent_goals_against_avg=1.2,
    league_avg_goals=2.5,
    home_advantage=0.3,
    is_home=False,
)

print(f"Home xG: {home_xg:.2f}")
print(f"Away xG: {away_xg:.2f}")
```

### 2. Calculate Match Probabilities

```python
# Calculate probabilities from xG values
probabilities = ProbabilityService.calculate_match_probabilities(
    home_xg=1.8,
    away_xg=1.2,
)

print(f"Home Win: {probabilities.home_win:.2%}")
print(f"Draw: {probabilities.draw:.2%}")
print(f"Away Win: {probabilities.away_win:.2%}")
print(f"Over 2.5 Goals: {probabilities.over_2_5_goals:.2%}")
print(f"Both Teams Score: {probabilities.both_teams_score:.2%}")
```

### 3. Calculate from Team Statistics

```python
# One-step calculation from team stats
xg, probabilities = ProbabilityService.calculate_probabilities_from_stats(
    home_goals_for_avg=1.8,
    home_goals_against_avg=1.2,
    away_goals_for_avg=1.5,
    away_goals_against_avg=1.3,
    league_avg_goals=2.5,
    home_advantage=0.3,
)

print(f"Expected Goals: Home {xg.home_xg:.2f} - {xg.away_xg:.2f} Away")
print(f"Home Win Probability: {probabilities.home_win:.2%}")
```

## Advanced Usage

### Get Most Likely Scoreline

```python
home_goals, away_goals, probability = ProbabilityService.get_most_likely_scoreline(
    home_xg=1.8,
    away_xg=1.2,
)

print(f"Most likely scoreline: {home_goals}-{away_goals} ({probability:.2%})")
```

### Get Specific Scoreline Probability

```python
# Probability of a 2-1 home win
prob = ProbabilityService.get_scoreline_probability(
    home_xg=1.8,
    away_xg=1.2,
    home_goals=2,
    away_goals=1,
)

print(f"Probability of 2-1: {prob:.2%}")
```

### Poisson Distribution

```python
# Probability of scoring exactly 2 goals with xG of 1.5
prob = ProbabilityService.poisson_probability(lambda_param=1.5, k=2)
print(f"P(2 goals; xG=1.5) = {prob:.2%}")

# Cumulative probability (2 or fewer goals)
cumulative = ProbabilityService.poisson_cumulative(lambda_param=1.5, k=2)
print(f"P(≤2 goals; xG=1.5) = {cumulative:.2%}")
```

## Integration Example

### Using with Match Data

```python
async def calculate_match_probabilities_from_db(
    match_id: int,
    db: AsyncSession,
):
    """Calculate probabilities for a match from database."""
    from app.infrastructure.repositories.match_repository import MatchRepository
    from app.infrastructure.repositories.historical_result_repository import HistoricalResultRepository
    
    # Get match
    match_repo = MatchRepository(db)
    match = await match_repo.get_by_id(match_id)
    
    # Get team statistics
    hist_repo = HistoricalResultRepository(db)
    home_stats = await hist_repo.get_team_season_stats(
        team_id=match.home_team_id,
        season=match.season,
    )
    away_stats = await hist_repo.get_team_season_stats(
        team_id=match.away_team_id,
        season=match.season,
    )
    
    # Calculate probabilities
    xg, probs = ProbabilityService.calculate_probabilities_from_stats(
        home_goals_for_avg=home_stats.average_goals_for,
        home_goals_against_avg=home_stats.average_goals_against,
        away_goals_for_avg=away_stats.average_goals_for,
        away_goals_against_avg=away_stats.average_goals_against,
    )
    
    return {
        "expected_goals": {
            "home": xg.home_xg,
            "away": xg.away_xg,
        },
        "probabilities": {
            "home_win": probs.home_win,
            "draw": probs.draw,
            "away_win": probs.away_win,
        },
        "most_likely_scoreline": ProbabilityService.get_most_likely_scoreline(
            xg.home_xg,
            xg.away_xg,
        ),
    }
```

## API Endpoint Example

```python
@router.get("/matches/{match_id}/probabilities")
async def get_match_probabilities(
    match_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get match outcome probabilities."""
    # Fetch team statistics from database
    # ... (implementation)
    
    # Calculate probabilities
    xg, probs = ProbabilityService.calculate_probabilities_from_stats(
        home_goals_for_avg=home_stats.goals_for_avg,
        home_goals_against_avg=home_stats.goals_against_avg,
        away_goals_for_avg=away_stats.goals_for_avg,
        away_goals_against_avg=away_stats.goals_against_avg,
    )
    
    return {
        "match_id": match_id,
        "expected_goals": {
            "home": round(xg.home_xg, 2),
            "away": round(xg.away_xg, 2),
        },
        "outcome_probabilities": {
            "home_win": round(probs.home_win, 4),
            "draw": round(probs.draw, 4),
            "away_win": round(probs.away_win, 4),
        },
        "total_goals_probabilities": {
            "0": round(probs.total_goals_0, 4),
            "1": round(probs.total_goals_1, 4),
            "2": round(probs.total_goals_2, 4),
            "3": round(probs.total_goals_3, 4),
            "4_plus": round(probs.total_goals_4_plus, 4),
        },
        "both_teams_score": round(probs.both_teams_score, 4),
        "over_2_5_goals": round(probs.over_2_5_goals, 4),
        "under_2_5_goals": round(probs.under_2_5_goals, 4),
    }
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_probability_service.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app.application.services.probability_service
```

## Key Features

✅ **Deterministic**: Same inputs always produce same outputs  
✅ **Stateless**: No instance variables, all static methods  
✅ **Testable**: Comprehensive unit tests included  
✅ **Mathematically Sound**: Based on established Poisson model  
✅ **Well Documented**: Mathematical explanations provided  

