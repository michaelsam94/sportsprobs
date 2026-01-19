"""Google Gemini AI client for comprehensive sports statistics analysis."""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json

import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini AI sports analysis."""

    def __init__(self):
        """Initialize Gemini client."""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.timeout = 60

    def _get_comprehensive_analysis_prompt(
        self,
        home_team: str,
        away_team: str,
        sport: str = "football",
        league: Optional[str] = None,
        match_date: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a comprehensive prompt for detailed sports statistics analysis.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            sport: Sport type (football, basketball, etc.)
            league: League name (optional)
            match_date: Match date (optional)
            context: Additional context data (optional)
        
        Returns:
            Detailed prompt string for Gemini
        """
        base_prompt = f"""You are an expert sports analyst with deep knowledge of {sport} statistics and analytics. 
Analyze the upcoming match between {home_team} (home) and {away_team} (away).

"""
        
        if league:
            base_prompt += f"League: {league}\n"
        if match_date:
            base_prompt += f"Match Date: {match_date}\n"
        
        base_prompt += f"""
Provide a COMPREHENSIVE and DETAILED statistical analysis in JSON format. Include ALL of the following:

1. TEAM PERFORMANCE METRICS:
   - Recent form (last 5-10 matches): wins, draws, losses, goals scored/conceded
   - Home/Away performance: win rates, average goals, defensive records
   - League position and points
   - Goal scoring patterns: average goals per match, scoring frequency
   - Defensive strength: clean sheets, goals conceded per match
   - Attack efficiency: shots per goal, conversion rates

2. HEAD-TO-HEAD STATISTICS:
   - Historical matchups between these teams
   - Recent meetings (last 5-10 encounters)
   - Win/loss/draw records
   - Average goals in previous meetings
   - Trends and patterns in their matchups

3. PLAYER STATISTICS (if available):
   - Key players and their recent form
   - Top scorers and assist providers
   - Injury concerns or suspensions
   - Player vs player matchups

4. TACTICAL ANALYSIS:
   - Preferred formations and playing styles
   - Strengths and weaknesses
   - Set piece performance (corners, free kicks)
   - Counter-attack effectiveness
   - Possession-based vs direct play styles

5. MATCH-SPECIFIC FACTORS:
   - Home advantage impact
   - Weather conditions (if relevant)
   - Motivation factors (relegation battle, title race, etc.)
   - Fatigue considerations (recent fixture congestion)

6. STATISTICAL PREDICTIONS:
   - Expected goals (xG) for both teams
   - Match outcome probabilities (home win, draw, away win)
   - Most likely scorelines (top 3-5)
   - Over/Under goals predictions
   - Both teams to score probability
   - Clean sheet probabilities

7. KEY STATISTICS TO INCLUDE:
   - Possession percentages (average)
   - Shots per match (total, on target, off target)
   - Pass accuracy and total passes
   - Corners per match
   - Fouls and cards (yellow/red)
   - Offsides (for football)
   - Aerial duels won (for football)
   - Successful dribbles
   - Key passes and chances created
   - Defensive actions (tackles, interceptions, clearances)
   - Saves (for goalkeepers)

8. ADVANCED METRICS:
   - Expected goals (xG) and expected goals against (xGA)
   - Expected points (xP)
   - Shot quality metrics
   - Pressing intensity
   - Build-up play effectiveness
   - Defensive organization metrics

9. TREND ANALYSIS:
   - Form trends (improving/declining)
   - Scoring trends (increasing/decreasing)
   - Defensive trends
   - Performance against similar opponents

10. RISK FACTORS:
    - Injury concerns
    - Suspension issues
    - Recent poor form
    - Tactical vulnerabilities

Return the analysis as a JSON object with the following structure:
{{
    "match_info": {{
        "home_team": "{home_team}",
        "away_team": "{away_team}",
        "sport": "{sport}",
        "league": "{league or 'Unknown'}",
        "match_date": "{match_date or 'TBD'}"
    }},
    "team_performance": {{
        "home": {{
            "recent_form": {{"wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0}},
            "home_record": {{"wins": 0, "draws": 0, "losses": 0, "win_rate": 0.0, "avg_goals_for": 0.0, "avg_goals_against": 0.0}},
            "league_position": 0,
            "points": 0,
            "goals_scored": 0,
            "goals_conceded": 0,
            "clean_sheets": 0,
            "avg_goals_per_match": 0.0,
            "avg_goals_conceded_per_match": 0.0,
            "shots_per_match": 0.0,
            "shots_on_target_per_match": 0.0,
            "possession_avg": 0.0,
            "pass_accuracy_avg": 0.0,
            "corners_per_match": 0.0,
            "fouls_per_match": 0.0
        }},
        "away": {{
            "recent_form": {{"wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0}},
            "away_record": {{"wins": 0, "draws": 0, "losses": 0, "win_rate": 0.0, "avg_goals_for": 0.0, "avg_goals_against": 0.0}},
            "league_position": 0,
            "points": 0,
            "goals_scored": 0,
            "goals_conceded": 0,
            "clean_sheets": 0,
            "avg_goals_per_match": 0.0,
            "avg_goals_conceded_per_match": 0.0,
            "shots_per_match": 0.0,
            "shots_on_target_per_match": 0.0,
            "possession_avg": 0.0,
            "pass_accuracy_avg": 0.0,
            "corners_per_match": 0.0,
            "fouls_per_match": 0.0
        }}
    }},
    "head_to_head": {{
        "total_meetings": 0,
        "home_wins": 0,
        "draws": 0,
        "away_wins": 0,
        "avg_goals_per_match": 0.0,
        "recent_meetings": []
    }},
    "predictions": {{
        "probabilities": {{
            "home_win": 0.0,
            "draw": 0.0,
            "away_win": 0.0
        }},
        "expected_goals": {{
            "home": 0.0,
            "away": 0.0
        }},
        "likely_scorelines": [
            {{"score": "0-0", "probability": 0.0}}
        ],
        "over_under": {{
            "over_2_5": 0.0,
            "under_2_5": 0.0
        }},
        "both_teams_to_score": 0.0,
        "clean_sheet_home": 0.0,
        "clean_sheet_away": 0.0
    }},
    "key_statistics": {{
        "home": {{
            "possession_avg": 0.0,
            "shots_total_avg": 0.0,
            "shots_on_target_avg": 0.0,
            "passes_total_avg": 0.0,
            "pass_accuracy_avg": 0.0,
            "corners_avg": 0.0,
            "fouls_avg": 0.0,
            "yellow_cards_avg": 0.0,
            "red_cards_avg": 0.0,
            "offsides_avg": 0.0
        }},
        "away": {{
            "possession_avg": 0.0,
            "shots_total_avg": 0.0,
            "shots_on_target_avg": 0.0,
            "passes_total_avg": 0.0,
            "pass_accuracy_avg": 0.0,
            "corners_avg": 0.0,
            "fouls_avg": 0.0,
            "yellow_cards_avg": 0.0,
            "red_cards_avg": 0.0,
            "offsides_avg": 0.0
        }}
    }},
    "advanced_metrics": {{
        "home": {{
            "expected_goals": 0.0,
            "expected_goals_against": 0.0,
            "expected_points": 0.0
        }},
        "away": {{
            "expected_goals": 0.0,
            "expected_goals_against": 0.0,
            "expected_points": 0.0
        }}
    }},
    "tactical_analysis": {{
        "home": {{
            "formation": "",
            "playing_style": "",
            "strengths": [],
            "weaknesses": []
        }},
        "away": {{
            "formation": "",
            "playing_style": "",
            "strengths": [],
            "weaknesses": []
        }}
    }},
    "risk_factors": {{
        "home": [],
        "away": []
    }},
    "analysis_summary": ""
}}

IMPORTANT: 
- Provide realistic and detailed statistics based on your knowledge
- If specific data is not available, provide reasonable estimates based on team reputation and league standards
- Ensure all probabilities sum to approximately 1.0
- Include at least 3-5 likely scorelines
- Be thorough and comprehensive in your analysis
- Focus on actionable insights for match prediction and analysis
"""
        
        if context:
            base_prompt += f"\n\nAdditional Context:\n{json.dumps(context, indent=2)}\n"
        
        return base_prompt

    async def analyze_match(
        self,
        home_team: str,
        away_team: str,
        sport: str = "football",
        league: Optional[str] = None,
        match_date: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive match analysis using Gemini AI.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            sport: Sport type (default: football)
            league: League name (optional)
            match_date: Match date (optional)
            context: Additional context data (optional)
        
        Returns:
            Dictionary with comprehensive match analysis
        """
        try:
            prompt = self._get_comprehensive_analysis_prompt(
                home_team=home_team,
                away_team=away_team,
                sport=sport,
                league=league,
                match_date=match_date,
                context=context
            )
            
            logger.info(f"Requesting Gemini analysis for {home_team} vs {away_team}")
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }
            )
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Try to extract JSON if response includes markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                if json_end > json_start:
                    response_text = response_text[json_start:json_end].strip()
            
            # Parse JSON response
            try:
                analysis_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON response: {e}")
                logger.debug(f"Response text: {response_text[:500]}")
                # Return a structured error response
                return {
                    "error": "Failed to parse analysis response",
                    "raw_response": response_text[:1000],
                    "match_info": {
                        "home_team": home_team,
                        "away_team": away_team,
                        "sport": sport,
                        "league": league or "Unknown",
                    }
                }
            
            # Add metadata
            analysis_data["generated_at"] = datetime.utcnow().isoformat()
            analysis_data["source"] = "gemini_ai"
            
            logger.info(f"Successfully generated analysis for {home_team} vs {away_team}")
            return analysis_data
            
        except Exception as e:
            logger.error(f"Error generating Gemini analysis: {e}", exc_info=True)
            raise

    async def get_team_statistics(
        self,
        team_name: str,
        sport: str = "football",
        league: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive team statistics using Gemini AI.
        
        Args:
            team_name: Team name
            sport: Sport type (default: football)
            league: League name (optional)
        
        Returns:
            Dictionary with comprehensive team statistics
        """
        prompt = f"""You are an expert sports analyst. Provide comprehensive statistics for {team_name} in {sport}.

Include:
1. Current season performance (wins, draws, losses, goals for/against, points, position)
2. Recent form (last 5-10 matches)
3. Home and away records
4. Key players and their statistics
5. Tactical style and formation
6. Strengths and weaknesses
7. Average statistics per match (goals, shots, possession, passes, etc.)
8. Historical performance trends

Return as JSON with detailed statistics."""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 4096,
                }
            )
            
            response_text = response.text.strip()
            
            # Extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            try:
                stats = json.loads(response_text)
                stats["generated_at"] = datetime.utcnow().isoformat()
                stats["source"] = "gemini_ai"
                return stats
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse response",
                    "raw_response": response_text[:500],
                    "team_name": team_name
                }
                
        except Exception as e:
            logger.error(f"Error getting team statistics: {e}", exc_info=True)
            raise

    async def analyze_match_with_context(
        self,
        match_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze match using existing match data as context.
        
        Args:
            match_data: Dictionary with match information
        
        Returns:
            Enhanced analysis with context
        """
        home_team = match_data.get("home_team", "Unknown")
        away_team = match_data.get("away_team", "Unknown")
        sport = match_data.get("sport", "football")
        league = match_data.get("league")
        match_date = match_data.get("match_date")
        
        return await self.analyze_match(
            home_team=home_team,
            away_team=away_team,
            sport=sport,
            league=league,
            match_date=match_date,
            context=match_data
        )

