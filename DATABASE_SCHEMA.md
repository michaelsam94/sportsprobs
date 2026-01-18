# PostgreSQL Schema for Sports Analytics

## Overview

This document describes the complete PostgreSQL schema designed for sports analytics with a focus on read-optimized queries and comprehensive indexing strategy.

## Entity Relationship Diagram

```
Leagues (1) ──< (N) Teams
Leagues (1) ──< (N) Matches
Teams (1) ──< (N) Players
Teams (1) ──< (N) Matches (home)
Teams (1) ──< (N) Matches (away)
Matches (1) ──< (N) MatchStats
Teams (1) ──< (N) MatchStats
Leagues (1) ──< (N) HistoricalResults
Teams (1) ──< (N) HistoricalResults
```

## Tables

### 1. Leagues

**Purpose**: Store league/organization information

**Columns**:
- `id` (PK, Integer)
- `name` (String(100), Unique, Indexed)
- `code` (String(10), Unique, Indexed)
- `sport` (String(50), Indexed)
- `country` (String(100), Indexed)
- `region` (String(100))
- `founded_year` (Integer)
- `logo_url` (String(500))
- `website_url` (String(500))
- `description` (Text)
- `is_active` (Boolean, Indexed)
- `season_start_month` (Integer, 1-12)
- `season_end_month` (Integer, 1-12)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Indexes**:
- Primary: `id`
- Unique: `name`, `code`
- Single: `sport`, `country`, `is_active`
- Composite: `(sport, is_active)`, `(country, sport)`

**Common Queries**:
- Get all active leagues for a sport
- Get leagues by country
- Find league by code

### 2. Teams

**Purpose**: Store team information

**Columns**:
- `id` (PK, Integer)
- `league_id` (FK → Leagues, CASCADE DELETE, Indexed)
- `name` (String(100), Indexed)
- `code` (String(10), Unique, Indexed)
- `city` (String(100), Indexed)
- `conference` (String(50), Indexed)
- `division` (String(50), Indexed)
- `founded_year` (Integer)
- `logo_url` (String(500))
- `stadium_name` (String(200))
- `stadium_capacity` (Integer)
- `is_active` (Boolean, Indexed)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Indexes**:
- Primary: `id`
- Unique: `code`
- Single: `league_id`, `name`, `city`, `conference`, `division`, `is_active`
- Composite: `(league_id, is_active)`, `(conference, division)`, `(league_id, name)`

**Common Queries**:
- Get teams by league
- Get teams by conference/division
- Find active teams in a league

### 3. Matches

**Purpose**: Store match/game information

**Columns**:
- `id` (PK, Integer)
- `league_id` (FK → Leagues, CASCADE DELETE, Indexed)
- `home_team_id` (FK → Teams, CASCADE DELETE, Indexed)
- `away_team_id` (FK → Teams, CASCADE DELETE, Indexed)
- `season` (Integer, Indexed)
- `week` (Integer, Indexed)
- `round` (Integer, Indexed)
- `match_date` (DateTime, Indexed)
- `status` (String(20), Indexed) - scheduled, live, finished, cancelled, postponed
- `home_score` (Integer)
- `away_score` (Integer)
- `home_score_overtime` (Integer)
- `away_score_overtime` (Integer)
- `venue` (String(200), Indexed)
- `attendance` (Integer)
- `weather_conditions` (String(100))
- `temperature` (Numeric(5,2))
- `is_playoff` (Boolean, Indexed)
- `is_neutral_venue` (Boolean)
- `referee` (String(100))
- `notes` (String(500))
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Indexes**:
- Primary: `id`
- Single: `league_id`, `home_team_id`, `away_team_id`, `season`, `week`, `round`, `match_date`, `status`, `venue`, `is_playoff`
- Composite:
  - `(league_id, season)` - Get all matches in a league season
  - `(league_id, match_date)` - Get matches by date range
  - `(home_team_id, away_team_id)` - Find head-to-head
  - `(season, status)` - Get matches by status in season
  - `(match_date, status)` - Get upcoming/live matches
  - `(home_team_id, season)` - Team's home matches
  - `(away_team_id, season)` - Team's away matches

**Common Queries**:
- Get matches by league and season
- Get upcoming matches
- Get team's matches in a season
- Find head-to-head records
- Get live matches

### 4. MatchStats

**Purpose**: Store detailed statistics for each team in a match

**Columns**:
- `id` (PK, Integer)
- `match_id` (FK → Matches, CASCADE DELETE, Indexed)
- `team_id` (FK → Teams, CASCADE DELETE, Indexed)
- `is_home_team` (Boolean, Indexed)

**General Statistics**:
- `possession_percent` (Numeric(5,2))
- `total_shots`, `shots_on_target`, `shots_off_target` (Integer)
- `corners`, `fouls`, `yellow_cards`, `red_cards`, `offsides` (Integer)

**Football/Soccer Specific**:
- `passes_total`, `passes_accurate` (Integer)
- `pass_accuracy` (Numeric(5,2))
- `crosses_total`, `crosses_accurate` (Integer)

**Basketball Specific**:
- `field_goals_made`, `field_goals_attempted` (Integer)
- `three_pointers_made`, `three_pointers_attempted` (Integer)
- `free_throws_made`, `free_throws_attempted` (Integer)
- `rebounds_offensive`, `rebounds_defensive`, `rebounds_total` (Integer)
- `assists`, `steals`, `blocks`, `turnovers`, `personal_fouls` (Integer)

**American Football Specific**:
- `first_downs`, `rushing_yards`, `passing_yards`, `total_yards` (Integer)
- `penalties`, `penalty_yards` (Integer)
- `time_of_possession` (String(10))

**Baseball Specific**:
- `hits`, `runs`, `errors`, `strikeouts`, `walks` (Integer)

**Metadata**:
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Indexes**:
- Primary: `id`
- Single: `match_id`, `team_id`, `is_home_team`
- Composite:
  - `(match_id, team_id)` - Get stats for a team in a match
  - `(team_id, match_id)` - Get all stats for a team
  - `(match_id, is_home_team)` - Get home/away stats

**Common Queries**:
- Get match statistics for both teams
- Get team's statistics across matches
- Compare home vs away performance

### 5. HistoricalResults

**Purpose**: Store aggregated historical statistics for analytics

**Columns**:
- `id` (PK, Integer)
- `league_id` (FK → Leagues, CASCADE DELETE, Indexed)
- `team_id` (FK → Teams, CASCADE DELETE, Indexed)
- `season` (Integer, Indexed)
- `period_type` (String(20), Indexed) - season, month, week, custom
- `period_start`, `period_end` (DateTime)

**Match Statistics**:
- `matches_played`, `matches_won`, `matches_drawn`, `matches_lost` (Integer)
- `goals_for`, `goals_against`, `goal_difference` (Integer)
- `points` (Integer) - League points

**Home/Away Split**:
- `home_matches_played`, `home_matches_won`, `home_matches_drawn`, `home_matches_lost` (Integer)
- `home_goals_for`, `home_goals_against` (Integer)
- `away_matches_played`, `away_matches_won`, `away_matches_drawn`, `away_matches_lost` (Integer)
- `away_goals_for`, `away_goals_against` (Integer)

**Performance Metrics**:
- `win_percentage` (Numeric(5,2))
- `average_goals_for`, `average_goals_against` (Numeric(5,2))

**Streaks**:
- `current_win_streak`, `current_loss_streak`, `current_unbeaten_streak` (Integer)

**League Position**:
- `league_position` (Integer, Indexed)

**Metadata**:
- `last_updated_match_id` (FK → Matches, SET NULL)
- `is_final` (Boolean, Indexed) - True when period is complete
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Indexes**:
- Primary: `id`
- Single: `league_id`, `team_id`, `season`, `period_type`, `league_position`, `is_final`
- Composite:
  - `(league_id, season)` - League standings for a season
  - `(team_id, season)` - Team's season results
  - `(league_id, team_id, season)` - Specific team in league season
  - `(season, league_position)` - Standings across leagues
  - `(league_id, season, league_position)` - League table
  - `(period_type, season)` - Results by period type

**Common Queries**:
- Get league standings
- Get team's season statistics
- Get historical performance trends
- Compare teams across seasons

## Indexing Strategy

### Read Optimization Principles

1. **Primary Keys**: All tables have integer primary keys for fast lookups
2. **Foreign Keys**: All foreign keys are indexed for join performance
3. **Composite Indexes**: Created for common query patterns
4. **Covering Indexes**: Include frequently accessed columns together
5. **Partial Indexes**: Consider for filtered queries (e.g., active teams only)

### Index Types

- **B-Tree Indexes**: Default for most columns (equality, range queries)
- **Composite Indexes**: For multi-column queries
- **Unique Indexes**: For data integrity (league codes, team codes)

### Query Patterns Optimized

1. **League-based queries**: `league_id` indexed in all related tables
2. **Season-based queries**: `season` indexed with composite indexes
3. **Date range queries**: `match_date` indexed with composite indexes
4. **Team performance**: `team_id` with `season` composite indexes
5. **Status filtering**: `status`, `is_active`, `is_final` indexed
6. **Standings queries**: `league_position` with league/season composites

## Migration Strategy

### Initial Migration

Run the initial migration to create all tables:

```bash
alembic upgrade head
```

### Future Migrations

1. Add new columns as needed
2. Create additional indexes based on query patterns
3. Add constraints for data integrity
4. Consider partitioning for large tables (matches, match_stats)

## Performance Considerations

### Read Optimization

1. **Denormalization**: HistoricalResults table pre-aggregates data
2. **Indexing**: Comprehensive indexing for common queries
3. **Partitioning**: Consider partitioning matches by season
4. **Materialized Views**: Consider for complex analytics queries

### Write Optimization

1. **Batch Inserts**: Use bulk insert for match stats
2. **Async Operations**: All database operations are async
3. **Connection Pooling**: Configured in SQLAlchemy
4. **Transaction Management**: Proper transaction boundaries

### Maintenance

1. **VACUUM**: Regular vacuum for PostgreSQL
2. **ANALYZE**: Update statistics regularly
3. **Index Maintenance**: Monitor index usage
4. **Partition Management**: For partitioned tables

## Example Queries

### Get League Standings

```sql
SELECT 
    t.name,
    hr.matches_played,
    hr.matches_won,
    hr.matches_drawn,
    hr.matches_lost,
    hr.goals_for,
    hr.goals_against,
    hr.goal_difference,
    hr.points,
    hr.league_position
FROM historical_results hr
JOIN teams t ON hr.team_id = t.id
WHERE hr.league_id = ? 
  AND hr.season = ?
  AND hr.period_type = 'season'
  AND hr.is_final = true
ORDER BY hr.league_position;
```

### Get Team's Recent Matches

```sql
SELECT 
    m.match_date,
    ht.name as home_team,
    at.name as away_team,
    m.home_score,
    m.away_score,
    m.status
FROM matches m
JOIN teams ht ON m.home_team_id = ht.id
JOIN teams at ON m.away_team_id = at.id
WHERE (m.home_team_id = ? OR m.away_team_id = ?)
  AND m.season = ?
ORDER BY m.match_date DESC
LIMIT 10;
```

### Get Match Statistics

```sql
SELECT 
    t.name as team_name,
    ms.is_home_team,
    ms.possession_percent,
    ms.total_shots,
    ms.shots_on_target,
    ms.passes_total,
    ms.passes_accurate
FROM match_stats ms
JOIN teams t ON ms.team_id = t.id
WHERE ms.match_id = ?
ORDER BY ms.is_home_team DESC;
```

## Schema Evolution

The schema is designed to be extensible:

1. **New Sports**: Add sport-specific columns to MatchStats
2. **New Metrics**: Add columns to HistoricalResults
3. **New Periods**: Use period_type for different aggregations
4. **New Relationships**: Add foreign keys as needed

