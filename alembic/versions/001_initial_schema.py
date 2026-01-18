"""Initial schema for sports analytics

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create leagues table
    op.create_table(
        'leagues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('sport', sa.String(length=50), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('founded_year', sa.Integer(), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('website_url', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('season_start_month', sa.Integer(), nullable=True),
        sa.Column('season_end_month', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_leagues_id', 'leagues', ['id'], unique=False)
    op.create_index('ix_leagues_name', 'leagues', ['name'], unique=True)
    op.create_index('ix_leagues_code', 'leagues', ['code'], unique=True)
    op.create_index('ix_leagues_sport', 'leagues', ['sport'], unique=False)
    op.create_index('ix_leagues_country', 'leagues', ['country'], unique=False)
    op.create_index('ix_leagues_is_active', 'leagues', ['is_active'], unique=False)
    op.create_index('idx_league_sport_active', 'leagues', ['sport', 'is_active'], unique=False)
    op.create_index('idx_league_country_sport', 'leagues', ['country', 'sport'], unique=False)

    # Create teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('conference', sa.String(length=50), nullable=True),
        sa.Column('division', sa.String(length=50), nullable=True),
        sa.Column('founded_year', sa.Integer(), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('stadium_name', sa.String(length=200), nullable=True),
        sa.Column('stadium_capacity', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['league_id'], ['leagues.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_teams_id', 'teams', ['id'], unique=False)
    op.create_index('ix_teams_league_id', 'teams', ['league_id'], unique=False)
    op.create_index('ix_teams_name', 'teams', ['name'], unique=False)
    op.create_index('ix_teams_code', 'teams', ['code'], unique=True)
    op.create_index('ix_teams_city', 'teams', ['city'], unique=False)
    op.create_index('ix_teams_conference', 'teams', ['conference'], unique=False)
    op.create_index('ix_teams_division', 'teams', ['division'], unique=False)
    op.create_index('ix_teams_is_active', 'teams', ['is_active'], unique=False)
    op.create_index('idx_team_league_active', 'teams', ['league_id', 'is_active'], unique=False)
    op.create_index('idx_team_conference_division', 'teams', ['conference', 'division'], unique=False)
    op.create_index('idx_team_league_name', 'teams', ['league_id', 'name'], unique=False)

    # Create players table (existing, keeping structure)
    op.create_table(
        'players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('position', sa.String(length=50), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('jersey_number', sa.Integer(), nullable=True),
        sa.Column('height', sa.Float(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('date_of_birth', sa.DateTime(), nullable=True),
        sa.Column('nationality', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_players_id', 'players', ['id'], unique=False)
    op.create_index('ix_players_name', 'players', ['name'], unique=False)
    op.create_index('ix_players_team_id', 'players', ['team_id'], unique=False)

    # Create matches table
    op.create_table(
        'matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.Column('home_team_id', sa.Integer(), nullable=False),
        sa.Column('away_team_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('week', sa.Integer(), nullable=True),
        sa.Column('round', sa.Integer(), nullable=True),
        sa.Column('match_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('home_score', sa.Integer(), nullable=True),
        sa.Column('away_score', sa.Integer(), nullable=True),
        sa.Column('home_score_overtime', sa.Integer(), nullable=True),
        sa.Column('away_score_overtime', sa.Integer(), nullable=True),
        sa.Column('venue', sa.String(length=200), nullable=True),
        sa.Column('attendance', sa.Integer(), nullable=True),
        sa.Column('weather_conditions', sa.String(length=100), nullable=True),
        sa.Column('temperature', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('is_playoff', sa.Boolean(), nullable=False),
        sa.Column('is_neutral_venue', sa.Boolean(), nullable=False),
        sa.Column('referee', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['league_id'], ['leagues.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['home_team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['away_team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_matches_id', 'matches', ['id'], unique=False)
    op.create_index('ix_matches_league_id', 'matches', ['league_id'], unique=False)
    op.create_index('ix_matches_home_team_id', 'matches', ['home_team_id'], unique=False)
    op.create_index('ix_matches_away_team_id', 'matches', ['away_team_id'], unique=False)
    op.create_index('ix_matches_season', 'matches', ['season'], unique=False)
    op.create_index('ix_matches_week', 'matches', ['week'], unique=False)
    op.create_index('ix_matches_round', 'matches', ['round'], unique=False)
    op.create_index('ix_matches_match_date', 'matches', ['match_date'], unique=False)
    op.create_index('ix_matches_status', 'matches', ['status'], unique=False)
    op.create_index('ix_matches_venue', 'matches', ['venue'], unique=False)
    op.create_index('ix_matches_is_playoff', 'matches', ['is_playoff'], unique=False)
    op.create_index('idx_match_league_season', 'matches', ['league_id', 'season'], unique=False)
    op.create_index('idx_match_league_date', 'matches', ['league_id', 'match_date'], unique=False)
    op.create_index('idx_match_teams', 'matches', ['home_team_id', 'away_team_id'], unique=False)
    op.create_index('idx_match_season_status', 'matches', ['season', 'status'], unique=False)
    op.create_index('idx_match_date_status', 'matches', ['match_date', 'status'], unique=False)
    op.create_index('idx_match_team_season', 'matches', ['home_team_id', 'season'], unique=False)
    op.create_index('idx_match_away_team_season', 'matches', ['away_team_id', 'season'], unique=False)

    # Create match_stats table
    op.create_table(
        'match_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('possession_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('total_shots', sa.Integer(), nullable=False),
        sa.Column('shots_on_target', sa.Integer(), nullable=False),
        sa.Column('shots_off_target', sa.Integer(), nullable=False),
        sa.Column('corners', sa.Integer(), nullable=False),
        sa.Column('fouls', sa.Integer(), nullable=False),
        sa.Column('yellow_cards', sa.Integer(), nullable=False),
        sa.Column('red_cards', sa.Integer(), nullable=False),
        sa.Column('offsides', sa.Integer(), nullable=False),
        sa.Column('passes_total', sa.Integer(), nullable=False),
        sa.Column('passes_accurate', sa.Integer(), nullable=False),
        sa.Column('pass_accuracy', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('crosses_total', sa.Integer(), nullable=False),
        sa.Column('crosses_accurate', sa.Integer(), nullable=False),
        sa.Column('field_goals_made', sa.Integer(), nullable=False),
        sa.Column('field_goals_attempted', sa.Integer(), nullable=False),
        sa.Column('three_pointers_made', sa.Integer(), nullable=False),
        sa.Column('three_pointers_attempted', sa.Integer(), nullable=False),
        sa.Column('free_throws_made', sa.Integer(), nullable=False),
        sa.Column('free_throws_attempted', sa.Integer(), nullable=False),
        sa.Column('rebounds_offensive', sa.Integer(), nullable=False),
        sa.Column('rebounds_defensive', sa.Integer(), nullable=False),
        sa.Column('rebounds_total', sa.Integer(), nullable=False),
        sa.Column('assists', sa.Integer(), nullable=False),
        sa.Column('steals', sa.Integer(), nullable=False),
        sa.Column('blocks', sa.Integer(), nullable=False),
        sa.Column('turnovers', sa.Integer(), nullable=False),
        sa.Column('personal_fouls', sa.Integer(), nullable=False),
        sa.Column('first_downs', sa.Integer(), nullable=False),
        sa.Column('rushing_yards', sa.Integer(), nullable=False),
        sa.Column('passing_yards', sa.Integer(), nullable=False),
        sa.Column('total_yards', sa.Integer(), nullable=False),
        sa.Column('penalties', sa.Integer(), nullable=False),
        sa.Column('penalty_yards', sa.Integer(), nullable=False),
        sa.Column('time_of_possession', sa.String(length=10), nullable=True),
        sa.Column('hits', sa.Integer(), nullable=False),
        sa.Column('runs', sa.Integer(), nullable=False),
        sa.Column('errors', sa.Integer(), nullable=False),
        sa.Column('strikeouts', sa.Integer(), nullable=False),
        sa.Column('walks', sa.Integer(), nullable=False),
        sa.Column('is_home_team', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_match_stats_id', 'match_stats', ['id'], unique=False)
    op.create_index('ix_match_stats_match_id', 'match_stats', ['match_id'], unique=False)
    op.create_index('ix_match_stats_team_id', 'match_stats', ['team_id'], unique=False)
    op.create_index('ix_match_stats_is_home_team', 'match_stats', ['is_home_team'], unique=False)
    op.create_index('idx_match_stat_match_team', 'match_stats', ['match_id', 'team_id'], unique=False)
    op.create_index('idx_match_stat_team_match', 'match_stats', ['team_id', 'match_id'], unique=False)
    op.create_index('idx_match_stat_match_home', 'match_stats', ['match_id', 'is_home_team'], unique=False)

    # Create historical_results table
    op.create_table(
        'historical_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=True),
        sa.Column('period_end', sa.DateTime(), nullable=True),
        sa.Column('matches_played', sa.Integer(), nullable=False),
        sa.Column('matches_won', sa.Integer(), nullable=False),
        sa.Column('matches_drawn', sa.Integer(), nullable=False),
        sa.Column('matches_lost', sa.Integer(), nullable=False),
        sa.Column('goals_for', sa.Integer(), nullable=False),
        sa.Column('goals_against', sa.Integer(), nullable=False),
        sa.Column('goal_difference', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('home_matches_played', sa.Integer(), nullable=False),
        sa.Column('home_matches_won', sa.Integer(), nullable=False),
        sa.Column('home_matches_drawn', sa.Integer(), nullable=False),
        sa.Column('home_matches_lost', sa.Integer(), nullable=False),
        sa.Column('home_goals_for', sa.Integer(), nullable=False),
        sa.Column('home_goals_against', sa.Integer(), nullable=False),
        sa.Column('away_matches_played', sa.Integer(), nullable=False),
        sa.Column('away_matches_won', sa.Integer(), nullable=False),
        sa.Column('away_matches_drawn', sa.Integer(), nullable=False),
        sa.Column('away_matches_lost', sa.Integer(), nullable=False),
        sa.Column('away_goals_for', sa.Integer(), nullable=False),
        sa.Column('away_goals_against', sa.Integer(), nullable=False),
        sa.Column('win_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('average_goals_for', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('average_goals_against', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('current_win_streak', sa.Integer(), nullable=False),
        sa.Column('current_loss_streak', sa.Integer(), nullable=False),
        sa.Column('current_unbeaten_streak', sa.Integer(), nullable=False),
        sa.Column('league_position', sa.Integer(), nullable=True),
        sa.Column('last_updated_match_id', sa.Integer(), nullable=True),
        sa.Column('is_final', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['league_id'], ['leagues.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['last_updated_match_id'], ['matches.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_historical_results_id', 'historical_results', ['id'], unique=False)
    op.create_index('ix_historical_results_league_id', 'historical_results', ['league_id'], unique=False)
    op.create_index('ix_historical_results_team_id', 'historical_results', ['team_id'], unique=False)
    op.create_index('ix_historical_results_season', 'historical_results', ['season'], unique=False)
    op.create_index('ix_historical_results_period_type', 'historical_results', ['period_type'], unique=False)
    op.create_index('ix_historical_results_league_position', 'historical_results', ['league_position'], unique=False)
    op.create_index('ix_historical_results_is_final', 'historical_results', ['is_final'], unique=False)
    op.create_index('idx_historical_league_season', 'historical_results', ['league_id', 'season'], unique=False)
    op.create_index('idx_historical_team_season', 'historical_results', ['team_id', 'season'], unique=False)
    op.create_index('idx_historical_league_team_season', 'historical_results', ['league_id', 'team_id', 'season'], unique=False)
    op.create_index('idx_historical_season_position', 'historical_results', ['season', 'league_position'], unique=False)
    op.create_index('idx_historical_league_season_position', 'historical_results', ['league_id', 'season', 'league_position'], unique=False)
    op.create_index('idx_historical_period_type', 'historical_results', ['period_type', 'season'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_historical_period_type', table_name='historical_results')
    op.drop_index('idx_historical_league_season_position', table_name='historical_results')
    op.drop_index('idx_historical_season_position', table_name='historical_results')
    op.drop_index('idx_historical_league_team_season', table_name='historical_results')
    op.drop_index('idx_historical_team_season', table_name='historical_results')
    op.drop_index('idx_historical_league_season', table_name='historical_results')
    op.drop_index('ix_historical_results_is_final', table_name='historical_results')
    op.drop_index('ix_historical_results_league_position', table_name='historical_results')
    op.drop_index('ix_historical_results_period_type', table_name='historical_results')
    op.drop_index('ix_historical_results_season', table_name='historical_results')
    op.drop_index('ix_historical_results_team_id', table_name='historical_results')
    op.drop_index('ix_historical_results_league_id', table_name='historical_results')
    op.drop_index('ix_historical_results_id', table_name='historical_results')
    op.drop_table('historical_results')

    op.drop_index('idx_match_stat_match_home', table_name='match_stats')
    op.drop_index('idx_match_stat_team_match', table_name='match_stats')
    op.drop_index('idx_match_stat_match_team', table_name='match_stats')
    op.drop_index('ix_match_stats_is_home_team', table_name='match_stats')
    op.drop_index('ix_match_stats_team_id', table_name='match_stats')
    op.drop_index('ix_match_stats_match_id', table_name='match_stats')
    op.drop_index('ix_match_stats_id', table_name='match_stats')
    op.drop_table('match_stats')

    op.drop_index('idx_match_away_team_season', table_name='matches')
    op.drop_index('idx_match_team_season', table_name='matches')
    op.drop_index('idx_match_date_status', table_name='matches')
    op.drop_index('idx_match_season_status', table_name='matches')
    op.drop_index('idx_match_teams', table_name='matches')
    op.drop_index('idx_match_league_date', table_name='matches')
    op.drop_index('idx_match_league_season', table_name='matches')
    op.drop_index('ix_matches_is_playoff', table_name='matches')
    op.drop_index('ix_matches_venue', table_name='matches')
    op.drop_index('ix_matches_status', table_name='matches')
    op.drop_index('ix_matches_match_date', table_name='matches')
    op.drop_index('ix_matches_round', table_name='matches')
    op.drop_index('ix_matches_week', table_name='matches')
    op.drop_index('ix_matches_season', table_name='matches')
    op.drop_index('ix_matches_away_team_id', table_name='matches')
    op.drop_index('ix_matches_home_team_id', table_name='matches')
    op.drop_index('ix_matches_league_id', table_name='matches')
    op.drop_index('ix_matches_id', table_name='matches')
    op.drop_table('matches')

    op.drop_index('ix_players_team_id', table_name='players')
    op.drop_index('ix_players_name', table_name='players')
    op.drop_index('ix_players_id', table_name='players')
    op.drop_table('players')

    op.drop_index('idx_team_league_name', table_name='teams')
    op.drop_index('idx_team_conference_division', table_name='teams')
    op.drop_index('idx_team_league_active', table_name='teams')
    op.drop_index('ix_teams_is_active', table_name='teams')
    op.drop_index('ix_teams_division', table_name='teams')
    op.drop_index('ix_teams_conference', table_name='teams')
    op.drop_index('ix_teams_city', table_name='teams')
    op.drop_index('ix_teams_code', table_name='teams')
    op.drop_index('ix_teams_name', table_name='teams')
    op.drop_index('ix_teams_league_id', table_name='teams')
    op.drop_index('ix_teams_id', table_name='teams')
    op.drop_table('teams')

    op.drop_index('idx_league_country_sport', table_name='leagues')
    op.drop_index('idx_league_sport_active', table_name='leagues')
    op.drop_index('ix_leagues_is_active', table_name='leagues')
    op.drop_index('ix_leagues_country', table_name='leagues')
    op.drop_index('ix_leagues_sport', table_name='leagues')
    op.drop_index('ix_leagues_code', table_name='leagues')
    op.drop_index('ix_leagues_name', table_name='leagues')
    op.drop_index('ix_leagues_id', table_name='leagues')
    op.drop_table('leagues')

