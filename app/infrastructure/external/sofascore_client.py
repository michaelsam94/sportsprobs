"""SofaScore web scraper client for match data and statistics."""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import re
import json
from urllib.parse import urlparse, parse_qs

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

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
        self._browser: Optional[Browser] = None

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

    async def _get_browser(self) -> Browser:
        """Get or create a browser instance."""
        if self._browser is None:
            playwright = await async_playwright().start()
            # Use chromium in headless mode
            self._browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']  # Required for Docker
            )
        return self._browser

    async def close_browser(self):
        """Close the browser instance."""
        if self._browser:
            await self._browser.close()
            self._browser = None

    async def search_and_select_result(
        self, 
        query: str, 
        result_index: int = 0,
        wait_timeout: int = 10000
    ) -> Dict[str, Any]:
        """Search for a query using the search input and select a result from dropdown.
        
        This method opens the SofaScore website, types the query into the search input,
        waits for dropdown results, and selects the specified result.
        
        Args:
            query: Search query (team name, match, competition, etc.)
            result_index: Index of the result to select from dropdown (default: 0 for first result)
            wait_timeout: Maximum time to wait for dropdown to appear (ms, default: 10000)
        
        Returns:
            Dictionary with selected result data including URL, title, and other metadata
        """
        browser = await self._get_browser()
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=self.headers['User-Agent']
        )
        page = await context.new_page()
        
        try:
            # Navigate to SofaScore homepage
            logger.info(f"Navigating to {self.base_url}")
            await page.goto(self.base_url, wait_until='networkidle', timeout=self.timeout * 1000)
            
            # Wait for and find the search input
            logger.info(f"Looking for search input with id='search-input'")
            search_input = await page.wait_for_selector(
                '#search-input',
                timeout=wait_timeout,
                state='visible'
            )
            
            # Type the query into the search input
            logger.info(f"Typing query: {query}")
            await search_input.fill(query)
            await page.wait_for_timeout(500)  # Wait a bit for search to trigger
            
            # Wait for dropdown to appear
            logger.info("Waiting for dropdown results to appear")
            try:
                # Wait for dropdown container - using the class pattern from user's description
                dropdown = await page.wait_for_selector(
                    '.z_dropdown',
                    timeout=wait_timeout,
                    state='visible'
                )
                
                # Wait a bit more for results to populate
                await page.wait_for_timeout(1000)
                
                # Find all clickable results in the dropdown
                # Look for clickable items in the dropdown (could be buttons, links, or divs)
                result_selectors = [
                    '.z_dropdown button',
                    '.z_dropdown a',
                    '.z_dropdown [role="button"]',
                    '.z_dropdown div[class*="result"]',
                    '.z_dropdown div[class*="item"]',
                ]
                
                results = []
                for selector in result_selectors:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        results = elements
                        logger.info(f"Found {len(results)} results using selector: {selector}")
                        break
                
                if not results:
                    # Fallback: try to find any clickable element in dropdown
                    results = await page.query_selector_all('.z_dropdown > * > *')
                    logger.info(f"Fallback: Found {len(results)} results in dropdown")
                
                if not results:
                    raise ValueError(f"No results found in dropdown for query: {query}")
                
                # Select the result at the specified index
                if result_index >= len(results):
                    logger.warning(
                        f"Requested result index {result_index} but only {len(results)} results found. "
                        f"Using last result."
                    )
                    result_index = len(results) - 1
                
                selected_result = results[result_index]
                
                # Extract information from the selected result before clicking
                result_data = {
                    "query": query,
                    "result_index": result_index,
                    "total_results": len(results),
                }
                
                # Try to extract text content
                text_content = await selected_result.text_content()
                if text_content:
                    result_data["text"] = text_content.strip()
                
                # Try to extract href if it's a link
                href = await selected_result.get_attribute('href')
                if href:
                    result_data["url"] = href if href.startswith('http') else f"{self.base_url}{href}"
                
                # Try to extract data attributes
                data_attrs = await selected_result.evaluate("""
                    (element) => {
                        const attrs = {};
                        for (let attr of element.attributes) {
                            if (attr.name.startsWith('data-')) {
                                attrs[attr.name] = attr.value;
                            }
                        }
                        return attrs;
                    }
                """)
                if data_attrs:
                    result_data["data_attributes"] = data_attrs
                
                logger.info(f"Selecting result {result_index}: {result_data.get('text', 'N/A')}")
                
                # Click on the selected result
                await selected_result.click()
                
                # Wait for navigation or page update
                await page.wait_for_timeout(2000)
                
                # Get the current URL after selection
                current_url = page.url
                result_data["final_url"] = current_url
                
                # Get page content for further processing
                page_content = await page.content()
                result_data["page_content_length"] = len(page_content)
                
                logger.info(f"Successfully selected result. Final URL: {current_url}")
                
                return result_data
                
            except PlaywrightTimeoutError:
                logger.error(f"Timeout waiting for dropdown results for query: {query}")
                raise ValueError(f"Search dropdown did not appear within {wait_timeout}ms for query: {query}")
            
        except Exception as e:
            logger.error(f"Error during search and select for query '{query}': {e}", exc_info=True)
            raise
        finally:
            await context.close()

    async def search_and_get_match_data(
        self,
        query: str,
        result_index: int = 0
    ) -> Dict[str, Any]:
        """Search for a match/team and get its data after selection.
        
        This is a convenience method that combines search_and_select_result with
        data extraction from the resulting page.
        
        Args:
            query: Search query (team name, match, etc.)
            result_index: Index of the result to select from dropdown
        
        Returns:
            Dictionary with match/team data extracted from the selected result page
        """
        try:
            # Perform search and selection
            search_result = await self.search_and_select_result(query, result_index)
            
            # Extract data from the resulting page
            browser = await self._get_browser()
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self.headers['User-Agent']
            )
            page = await context.new_page()
            
            try:
                final_url = search_result.get("final_url", self.base_url)
                await page.goto(final_url, wait_until='networkidle', timeout=self.timeout * 1000)
                
                # Get page content and parse it
                page_content = await page.content()
                soup = BeautifulSoup(page_content, 'html.parser')
                
                # Try to extract match data using existing methods
                match_data = self._extract_json_data(soup, page_content)
                
                if not match_data:
                    match_data = self._parse_html_structure(soup, final_url)
                
                # Merge search result metadata with extracted data
                match_data.update({
                    "search_query": query,
                    "search_result_index": result_index,
                    "source_url": final_url,
                })
                
                return match_data
                
            finally:
                await context.close()
                
        except Exception as e:
            logger.error(f"Error in search_and_get_match_data for query '{query}': {e}", exc_info=True)
            raise

