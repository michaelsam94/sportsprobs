# Probability Models for Sports Analytics

## Mathematical Foundation

### 1. Poisson Distribution

The Poisson distribution is used to model the probability of a given number of events occurring in a fixed interval of time or space, given a known average rate.

#### Formula

```
P(k; λ) = (λ^k * e^(-λ)) / k!
```

Where:
- `λ` (lambda) is the average rate (expected value)
- `k` is the number of occurrences
- `e` is Euler's number (≈ 2.71828)
- `k!` is the factorial of k

#### Why Poisson for Football?

1. **Goals are rare events**: In football, goals are relatively infrequent
2. **Independent events**: Goals scored are largely independent of each other
3. **Constant rate**: Over a match, the scoring rate is approximately constant
4. **Empirical fit**: Poisson distribution has been shown to fit football goal data well

#### Example

If a team has an expected goals (xG) of 1.5, the probability of scoring exactly 2 goals is:

```
P(2; 1.5) = (1.5^2 * e^(-1.5)) / 2!
         = (2.25 * 0.2231) / 2
         = 0.251
```

### 2. Expected Goals (xG) Model

Expected goals (xG) is a metric that quantifies the quality of scoring chances. Our simplified model calculates xG based on:

1. **Team's attacking strength**: Average goals scored
2. **Opponent's defensive weakness**: Average goals conceded
3. **League context**: League average goals
4. **Home advantage**: Additional boost for home teams

#### Formula

```
xG_home = (team_goals_for_avg * opponent_goals_against_avg) / league_avg_goals + home_advantage

xG_away = (team_goals_for_avg * opponent_goals_against_avg) / league_avg_goals - (home_advantage * 0.5)
```

#### Example

Given:
- Home team: 1.8 goals scored avg, 1.2 goals conceded avg
- Away team: 1.5 goals scored avg, 1.3 goals conceded avg
- League average: 2.5 goals per match
- Home advantage: 0.3

```
xG_home = (1.8 * 1.3) / 2.5 + 0.3
        = 2.34 / 2.5 + 0.3
        = 0.936 + 0.3
        = 1.236

xG_away = (1.5 * 1.2) / 2.5 - 0.15
        = 1.8 / 2.5 - 0.15
        = 0.72 - 0.15
        = 0.57
```

### 3. Match Outcome Probabilities

Using independent Poisson distributions for home and away goals, we calculate probabilities for all possible scorelines.

#### Win/Draw/Loss Probabilities

For each possible scoreline (home_goals, away_goals):
- **Home Win**: home_goals > away_goals
- **Draw**: home_goals == away_goals
- **Away Win**: home_goals < away_goals

The probability of each outcome is the sum of probabilities of all scorelines that result in that outcome.

#### Formula

```
P(home_goals, away_goals) = P(home_goals; xG_home) * P(away_goals; xG_away)

P(home_win) = Σ P(i, j) for all i > j
P(draw) = Σ P(i, i) for all i
P(away_win) = Σ P(i, j) for all i < j
```

#### Example

With xG_home = 1.5 and xG_away = 1.0:

```
P(1-0) = P(1; 1.5) * P(0; 1.0) = 0.335 * 0.368 = 0.123
P(2-0) = P(2; 1.5) * P(0; 1.0) = 0.251 * 0.368 = 0.092
P(1-1) = P(1; 1.5) * P(1; 1.0) = 0.335 * 0.368 = 0.123
...

P(home_win) = P(1-0) + P(2-0) + P(2-1) + ... ≈ 0.45
P(draw) = P(0-0) + P(1-1) + P(2-2) + ... ≈ 0.30
P(away_win) = P(0-1) + P(0-2) + P(1-2) + ... ≈ 0.25
```

### 4. Additional Probabilities

#### Total Goals Probabilities

```
P(total_goals = k) = Σ P(i, j) for all i + j = k
```

#### Both Teams Score

```
P(both_teams_score) = Σ P(i, j) for all i > 0 and j > 0
```

#### Over/Under 2.5 Goals

```
P(over_2.5) = Σ P(i, j) for all i + j > 2.5
P(under_2.5) = Σ P(i, j) for all i + j <= 2.5
```

## Model Assumptions

1. **Independence**: Home and away goals are independent
2. **Constant rate**: Scoring rate is constant throughout the match
3. **Poisson distribution**: Goals follow Poisson distribution
4. **No correlation**: No correlation between home and away goals
5. **Historical data**: Team averages are representative of future performance

## Limitations

1. **Simplified xG**: Real xG models use shot location, shot type, etc.
2. **No form factor**: Doesn't account for recent form
3. **No injuries**: Doesn't account for player availability
4. **No weather**: Doesn't account for weather conditions
5. **No motivation**: Doesn't account for match importance

## Improvements

Potential enhancements to the model:

1. **Weighted averages**: Give more weight to recent matches
2. **Head-to-head**: Include historical head-to-head results
3. **Form factor**: Account for recent form (last 5 matches)
4. **Injury adjustments**: Reduce xG for teams with key player injuries
5. **Weather adjustments**: Adjust for weather conditions
6. **Motivation factor**: Boost for important matches

## Validation

The model should be validated by:

1. **Historical accuracy**: Compare predicted probabilities to actual outcomes
2. **Calibration**: Ensure probabilities are well-calibrated (50% predictions should win ~50% of the time)
3. **Brier score**: Measure prediction accuracy
4. **Log loss**: Measure prediction quality

## References

1. Maher, M. J. (1982). Modelling association football scores. *Statistica Neerlandica*, 36(3), 109-118.
2. Karlis, D., & Ntzoufras, I. (2003). Analysis of sports data by using bivariate Poisson models. *Journal of the Royal Statistical Society: Series D*, 52(3), 381-393.
3. Rue, H., & Salvesen, Ø. (2000). Prediction and retrospective analysis of soccer matches in a league. *Journal of the Royal Statistical Society: Series D*, 49(3), 399-418.

