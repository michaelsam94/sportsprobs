# Database Schema Summary

## Quick Reference

### Tables Created

1. **leagues** - League/organization information
2. **teams** - Team information (linked to leagues)
3. **players** - Player information (linked to teams)
4. **matches** - Match/game information
5. **match_stats** - Detailed statistics per team per match
6. **historical_results** - Aggregated historical statistics

### Key Relationships

```
Leagues (1) ──< (N) Teams
Leagues (1) ──< (N) Matches
Teams (1) ──< (N) Players
Teams (1) ──< (N) Matches (as home_team)
Teams (1) ──< (N) Matches (as away_team)
Matches (1) ──< (N) MatchStats (2 per match - home & away)
Teams (1) ──< (N) MatchStats
Leagues (1) ──< (N) HistoricalResults
Teams (1) ──< (N) HistoricalResults
```

## Indexing Summary

### Single Column Indexes
- All primary keys
- All foreign keys
- Frequently filtered columns (status, is_active, season, etc.)

### Composite Indexes (Read Optimization)

**Leagues**:
- `(sport, is_active)` - Get active leagues by sport
- `(country, sport)` - Get leagues by country and sport

**Teams**:
- `(league_id, is_active)` - Get active teams in league
- `(conference, division)` - Get teams by conference/division
- `(league_id, name)` - Find team by name in league

**Matches**:
- `(league_id, season)` - Get all matches in league season
- `(league_id, match_date)` - Get matches by date range
- `(home_team_id, away_team_id)` - Find head-to-head
- `(season, status)` - Get matches by status in season
- `(match_date, status)` - Get upcoming/live matches
- `(home_team_id, season)` - Team's home matches
- `(away_team_id, season)` - Team's away matches

**MatchStats**:
- `(match_id, team_id)` - Get stats for team in match
- `(team_id, match_id)` - Get all stats for team
- `(match_id, is_home_team)` - Get home/away stats

**HistoricalResults**:
- `(league_id, season)` - League standings
- `(team_id, season)` - Team's season results
- `(league_id, team_id, season)` - Specific team in league season
- `(season, league_position)` - Standings across leagues
- `(league_id, season, league_position)` - League table
- `(period_type, season)` - Results by period type

## Usage

### Run Migrations

```bash
# Create all tables
alembic upgrade head

# Rollback
alembic downgrade -1

# Create new migration
alembic revision --autogenerate -m "description"
```

### Model Import

```python
from app.infrastructure.database.models import (
    LeagueModel,
    TeamModel,
    MatchModel,
    MatchStatModel,
    HistoricalResultModel,
    PlayerModel,
)
```

## Read Optimization Features

1. **Comprehensive Indexing**: All foreign keys and common query columns indexed
2. **Composite Indexes**: Optimized for multi-column queries
3. **Denormalization**: HistoricalResults pre-aggregates data
4. **Partitioning Ready**: Schema supports future partitioning by season
5. **Covering Indexes**: Composite indexes include frequently accessed columns

## Next Steps

1. Run initial migration: `alembic upgrade head`
2. Seed initial data (leagues, teams)
3. Set up data ingestion pipeline
4. Create materialized views for complex analytics (optional)
5. Monitor query performance and add indexes as needed

