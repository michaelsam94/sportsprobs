"""Base API client for external services."""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import httpx
from httpx import AsyncClient, Response
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, message: str, status_code: int = None, response: Dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class RateLimitError(APIError):
    """Exception raised when API rate limit is exceeded."""

    pass


class APIClient:
    """Base API client with retry logic and rate limiting."""

    def __init__(
        self,
        base_url: str,
        api_key: str = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_per_minute: int = 60,
    ):
        """Initialize API client.

        Args:
            base_url: Base URL for the API
            api_key: API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds
            rate_limit_per_minute: Rate limit per minute
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_per_minute = rate_limit_per_minute

        # Rate limiting tracking
        self.request_times: List[datetime] = []
        self._rate_limit_lock = asyncio.Lock()

        # HTTP client
        self.client: Optional[AsyncClient] = None

    async def _get_client(self) -> AsyncClient:
        """Get or create HTTP client."""
        if self.client is None:
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            self.client = AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self.client

    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        async with self._rate_limit_lock:
            now = datetime.utcnow()
            # Remove requests older than 1 minute
            self.request_times = [
                t for t in self.request_times
                if now - t < timedelta(minutes=1)
            ]

            if len(self.request_times) >= self.rate_limit_per_minute:
                # Calculate wait time
                oldest_request = min(self.request_times)
                wait_until = oldest_request + timedelta(minutes=1)
                wait_seconds = (wait_until - now).total_seconds()

                if wait_seconds > 0:
                    logger.warning(
                        f"Rate limit reached. Waiting {wait_seconds:.2f} seconds."
                    )
                    await asyncio.sleep(wait_seconds)
                    # Clean up again after waiting
                    self.request_times = [
                        t for t in self.request_times
                        if now - t < timedelta(minutes=1)
                    ]

            # Record this request
            self.request_times.append(datetime.utcnow())

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> Response:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body data
            headers: Additional headers

        Returns:
            HTTP response

        Raises:
            APIError: If request fails after retries
            RateLimitError: If rate limit is exceeded
        """
        client = await self._get_client()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        request_headers = headers or {}
        if self.api_key and "X-API-Key" not in request_headers:
            request_headers["X-API-Key"] = self.api_key

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Check rate limit before request
                await self._check_rate_limit()

                # Make request
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=request_headers,
                )

                # Handle rate limit errors
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        wait_time = int(retry_after)
                    else:
                        wait_time = (2 ** attempt) * self.retry_delay

                    if attempt < self.max_retries:
                        logger.warning(
                            f"Rate limit exceeded. Retrying after {wait_time} seconds."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise RateLimitError(
                            "API rate limit exceeded",
                            status_code=429,
                            response=response.json() if response.content else None,
                        )

                # Handle other errors
                if response.status_code >= 400:
                    error_data = None
                    error_message = None
                    try:
                        error_data = response.json()
                        error_message = error_data.get('message', 'Unknown error')
                    except Exception:
                        # If response is HTML or plain text, extract a concise message
                        response_text = response.text
                        if response_text:
                            # For HTML responses, try to extract title or use status code
                            if response_text.strip().startswith('<!DOCTYPE') or response_text.strip().startswith('<html'):
                                error_message = f"HTTP {response.status_code} - {response.reason_phrase}"
                            else:
                                # Truncate long text responses
                                error_message = response_text[:500] if len(response_text) > 500 else response_text
                        else:
                            error_message = f"HTTP {response.status_code} - {response.reason_phrase}"
                        error_data = {"message": error_message}

                    if attempt < self.max_retries and response.status_code >= 500:
                        # Retry on server errors
                        wait_time = (2 ** attempt) * self.retry_delay
                        logger.warning(
                            f"Server error {response.status_code}. "
                            f"Retrying after {wait_time} seconds."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise APIError(
                            f"API request failed: {error_message}",
                            status_code=response.status_code,
                            response=error_data,
                        )

                return response

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = (2 ** attempt) * self.retry_delay
                    logger.warning(
                        f"Connection error: {e}. Retrying after {wait_time} seconds."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise APIError(
                        f"Connection failed after {self.max_retries} retries: {str(e)}"
                    )

        if last_exception:
            raise APIError(f"Request failed: {str(last_exception)}")

    async def get(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Make GET request.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            headers: Additional headers

        Returns:
            JSON response as dictionary
        """
        response = await self._make_request("GET", endpoint, params=params, headers=headers)
        return response.json()

    async def post(
        self,
        endpoint: str,
        json_data: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Make POST request.

        Args:
            endpoint: API endpoint path
            json_data: JSON body data
            params: Query parameters
            headers: Additional headers

        Returns:
            JSON response as dictionary
        """
        response = await self._make_request(
            "POST", endpoint, json_data=json_data, params=params, headers=headers
        )
        return response.json()

    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

