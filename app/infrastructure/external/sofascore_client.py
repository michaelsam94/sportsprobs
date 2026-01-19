"""SofaScore web scraper client for match data and statistics."""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import re
import json
from urllib.parse import urlparse, parse_qs

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings

logger = logging.getLogger(__name__)


class SofaScoreClient:
    """Client for scraping SofaScore match data."""

    def __init__(self):
        """Initialize SofaScore client."""
        self.base_url = "https://www.sofascore.com"
        self.timeout = 30
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client."""
        return httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.headers,
            follow_redirects=True,
        )

    async def get_match_data(self, match_url: str) -> Dict[str, Any]:
        """Scrape match data from SofaScore URL.
        
        Args:
            match_url: SofaScore match URL (e.g., https://www.sofascore.com/football/match/nk-maribor-debreceni-vsc/wNsvY#id:15389642)
        
        Returns:
            Dictionary with match data, statistics, and historical data
        """
        try:
            async with await self._get_client() as client:
                response = await client.get(match_url)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to extract JSON data from script tags (SofaScore often embeds data in JS)
                match_data = self._extract_json_data(soup, response.text)
                
                if not match_data:
                    # Fallback: parse HTML structure
                    match_data = self._parse_html_structure(soup, match_url)
                
                return match_data
                
        except Exception as e:
            logger.error(f"Error scraping SofaScore match {match_url}: {e}", exc_info=True)
            raise

    def _extract_json_data(self, soup: BeautifulSoup, html_text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON data embedded in script tags."""
        # Look for JSON-LD structured data
        json_ld = soup.find_all('script', type='application/ld+json')
        for script in json_ld:
            try:
                data = json.loads(script.string)
                if data.get('@type') == 'SportsEvent':
                    return self._parse_json_ld(data)
            except:
                continue
        
        # Look for window.__INITIAL_STATE__ or similar
        pattern = r'window\.__INITIAL_STATE__\s*=\s*({.+?});'
        match = re.search(pattern, html_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                return self._parse_initial_state(data)
            except:
                pass
        
        # Look for any JSON data in script tags
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and ('match' in script.string.lower() or 'event' in script.string.lower()):
                # Try to extract JSON objects
                json_pattern = r'\{[^{}]*"id"[^{}]*"name"[^{}]*\}'
                matches = re.findall(json_pattern, script.string)
                for match_str in matches:
                    try:
                        data = json.loads(match_str)
                        if 'id' in data and 'name' in data:
                            return data
                    except:
                        continue
        
        return None

    def _parse_json_ld(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSON-LD structured data."""
        result = {
            "match_id": data.get('identifier', {}).get('value'),
            "home_team": data.get('homeTeam', {}).get('name'),
            "away_team": data.get('awayTeam', {}).get('name'),
            "start_date": data.get('startDate'),
            "status": "scheduled",
        }
        return result

    def _parse_initial_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse window.__INITIAL_STATE__ data."""
        # This structure varies, so we'll try common paths
        if 'event' in data:
            event = data['event']
            return {
                "match_id": event.get('id'),
                "home_team": event.get('homeTeam', {}).get('name'),
                "away_team": event.get('awayTeam', {}).get('name'),
                "home_score": event.get('homeScore', {}).get('current'),
                "away_score": event.get('awayScore', {}).get('current'),
                "status": event.get('status', {}).get('type'),
            }
        return {}

    def _parse_html_structure(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Parse HTML structure as fallback."""
        result = {
            "url": url,
            "scraped_at": datetime.utcnow().isoformat(),
        }
        
        # Extract match ID from URL
        match_id_match = re.search(r'#id:(\d+)', url)
        if match_id_match:
            result["match_id"] = int(match_id_match.group(1))
        
        # Try to find team names
        team_elements = soup.find_all(['span', 'div'], class_=re.compile(r'team|participant', re.I))
        teams = []
        for elem in team_elements[:4]:  # Limit to first 4 matches
            text = elem.get_text(strip=True)
            if text and len(text) > 2 and len(text) < 50:
                teams.append(text)
        
        if len(teams) >= 2:
            result["home_team"] = teams[0]
            result["away_team"] = teams[1]
        
        # Try to find score
        score_elements = soup.find_all(['span', 'div'], class_=re.compile(r'score', re.I))
        for elem in score_elements:
            text = elem.get_text(strip=True)
            if re.match(r'^\d+[:\-]\d+$', text):
                scores = re.split(r'[:\-]', text)
                if len(scores) == 2:
                    result["home_score"] = int(scores[0])
                    result["away_score"] = int(scores[1])
                    result["status"] = "finished"
                break
        
        return result

    async def get_match_statistics(self, match_id: int) -> Dict[str, Any]:
        """Get detailed match statistics from SofaScore API.
        
        Args:
            match_id: SofaScore match ID
        
        Returns:
            Dictionary with match statistics
        """
        try:
            # SofaScore API endpoint (may require authentication)
            api_url = f"{self.base_url}/api/v1/event/{match_id}"
            
            async with await self._get_client() as client:
                response = await client.get(api_url)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"SofaScore API returned {response.status_code} for match {match_id}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error fetching SofaScore statistics for match {match_id}: {e}")
            return {}

    async def get_team_historical_matches(self, team_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get historical matches for a team.
        
        Args:
            team_name: Team name to search for
            limit: Maximum number of matches to return
        
        Returns:
            List of historical match dictionaries
        """
        try:
            # Search for team
            search_url = f"{self.base_url}/search"
            params = {"q": team_name, "type": "team"}
            
            async with await self._get_client() as client:
                response = await client.get(search_url, params=params)
                
                if response.status_code != 200:
                    return []
                
                # Parse search results to find team ID
                soup = BeautifulSoup(response.text, 'html.parser')
                team_links = soup.find_all('a', href=re.compile(r'/team/'))
                
                if not team_links:
                    return []
                
                # Get first team's URL
                team_url = team_links[0].get('href')
                team_id_match = re.search(r'/team/(\d+)', team_url)
                
                if not team_id_match:
                    return []
                
                team_id = team_id_match.group(1)
                
                # Get team's recent matches
                matches_url = f"{self.base_url}/api/v1/team/{team_id}/events/last/{limit}"
                matches_response = await client.get(matches_url)
                
                if matches_response.status_code == 200:
                    data = matches_response.json()
                    return data.get('events', [])
                
                return []
                
        except Exception as e:
            logger.error(f"Error fetching historical matches for team {team_name}: {e}")
            return []

    def parse_match_url(self, url: str) -> Dict[str, Any]:
        """Parse SofaScore URL to extract match information.
        
        Args:
            url: SofaScore match URL
        
        Returns:
            Dictionary with parsed URL components
        """
        parsed = urlparse(url)
        fragment = parsed.fragment
        
        result = {
            "url": url,
            "path": parsed.path,
        }
        
        # Extract match ID from fragment (#id:15389642)
        id_match = re.search(r'id:(\d+)', fragment)
        if id_match:
            result["match_id"] = int(id_match.group(1))
        
        # Extract team names from path
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 3 and path_parts[0] == 'football' and path_parts[1] == 'match':
            match_slug = path_parts[2]
            # Format: "nk-maribor-debreceni-vsc"
            teams = match_slug.split('-')
            # This is a heuristic - might need adjustment
            if len(teams) >= 2:
                result["home_team_slug"] = '-'.join(teams[:len(teams)//2])
                result["away_team_slug"] = '-'.join(teams[len(teams)//2:])
        
        return result

