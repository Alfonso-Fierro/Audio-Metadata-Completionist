"""HTTP client with retry logic and error handling."""

import asyncio
from typing import Any, Dict, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class HTTPClient:
    """Async HTTP client with retry logic and connection pooling."""

    def __init__(
        self,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        """
        Initialize HTTP client.

        Args:
            timeout: Request timeout in seconds (defaults to settings.http_timeout)
            max_retries: Maximum retry attempts (defaults to settings.http_max_retries)
        """
        self.timeout = timeout or settings.http_timeout
        self.max_retries = max_retries or settings.http_max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "HTTPClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True,
    )
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """
        Perform GET request with retry logic.

        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: On request failure after retries
        """
        if not self._client:
            raise RuntimeError("HTTPClient must be used as async context manager")

        logger.debug(f"GET request to {url}")
        try:
            response = await self._client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
            raise
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout for {url}, retrying...")
            raise
        except httpx.NetworkError as e:
            logger.warning(f"Network error for {url}, retrying...")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise

    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """
        Perform POST request with retry logic.

        Args:
            url: Request URL
            data: Form data
            json: JSON data
            headers: Request headers

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: On request failure after retries
        """
        if not self._client:
            raise RuntimeError("HTTPClient must be used as async context manager")

        logger.debug(f"POST request to {url}")
        try:
            response = await self._client.post(url, data=data, json=json, headers=headers)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise

    async def download_file(self, url: str, output_path: str) -> bool:
        """
        Download file from URL to local path.

        Args:
            url: File URL
            output_path: Local file path

        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self.get(url)
            with open(output_path, "wb") as f:
                f.write(response.content)
            logger.debug(f"Downloaded {url} to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return False
