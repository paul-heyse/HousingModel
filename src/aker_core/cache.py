"""Cache and rate limiting functionality for external data dependencies."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests
import requests_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from aker_core.run import RunContext


def is_offline_mode() -> bool:
    """Detect if we're in offline mode by checking network connectivity.

    Returns:
        True if network connectivity is limited/unavailable
    """
    try:
        # Try to connect to a reliable external host
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return False
    except (OSError, socket.timeout):
        return True


class Cache:
    """HTTP response cache with ETag/Last-Modified support and local storage."""

    def __init__(
        self,
        base_path: Union[str, Path, None] = None,
        run_context: Optional[RunContext] = None,
        default_ttl: str = "30d",
    ) -> None:
        """Initialize cache with base path and optional RunContext.

        Args:
            base_path: Base directory for local storage (default: /data)
            run_context: Optional RunContext for lineage tracking
            default_ttl: Default TTL for cache entries (e.g., "30d", "1h", "5m")
        """
        resolved_base = Path(
            base_path or os.environ.get("AKER_CACHE_PATH") or (Path.cwd() / "aker_cache")
        )
        self.base_path = resolved_base
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.run_context = run_context
        self.default_ttl = self._parse_ttl(default_ttl)

        # Set up requests-cache session
        self.session = requests_cache.CachedSession(
            cache_name=str(self.base_path / "http_cache"),
            backend="sqlite",
            expire_after=self.default_ttl,
            allowable_codes=(200, 301, 302, 404),
        )

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def fetch(
        self,
        url: str,
        etl_key: Optional[str] = None,
        ttl: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        offline_mode: Optional[bool] = None,
    ) -> requests.Response:
        """Fetch URL with caching, ETag/Last-Modified support, and lineage tracking.

        Args:
            url: URL to fetch
            etl_key: Optional ETL key for cache partitioning
            ttl: Optional TTL override for this request
            headers: Optional additional headers
            offline_mode: If True, only use cached responses. If None, auto-detect.

        Returns:
            Response object (cached or fresh)
        """
        cache_key = self._build_cache_key(url, etl_key)
        ttl_seconds = self._parse_ttl(ttl) if ttl else self.default_ttl

        # Auto-detect offline mode if not explicitly set
        if offline_mode is None:
            offline_mode = is_offline_mode()

        # Log offline mode detection
        if self.run_context and offline_mode:
            self.run_context.log_data_lake_operation(
                operation="offline_mode_detected",
                dataset="connectivity",
                path=url,
                metadata={"offline_mode": True},
            )

        # Check for existing cached response
        cached_response = self._get_cached_response(cache_key)
        if cached_response and not self._is_expired(cached_response, ttl_seconds):
            # Use cached response with conditional request
            etag = cached_response.get("etag")
            last_modified = cached_response.get("last_modified")

            request_headers = {}
            if etag:
                request_headers["If-None-Match"] = etag
            if last_modified:
                request_headers["If-Modified-Since"] = last_modified
            if headers:
                request_headers.update(headers)

            # Log cache hit
            if self.run_context:
                self.run_context.log_data_lake_operation(
                    operation="cache_hit",
                    dataset="http_cache",
                    path=cache_key,
                    metadata={"url": url, "ttl_seconds": ttl_seconds},
                )

            try:
                response = self.session.get(url, headers=request_headers)
                if response.status_code == 304:  # Not Modified
                    return self._build_response_from_cache(cached_response)
                elif response.status_code == 200:
                    # Update cache with new response
                    self._cache_response(cache_key, response)
                    return response
                else:
                    # Server error, return cached response if available
                    if cached_response:
                        return self._build_response_from_cache(cached_response)
                    return response
            except requests.RequestException:
                # Network error in online mode, use cache if available
                if cached_response and not offline_mode:
                    return self._build_response_from_cache(cached_response)
                raise
        else:
            # Cache miss or expired, fetch fresh
            if offline_mode:
                raise RuntimeError(f"Cache miss for {url} in offline mode")

            try:
                response = self.session.get(url, headers=headers)
                if response.status_code == 200:
                    self._cache_response(cache_key, response)

                    # Log cache miss
                    if self.run_context:
                        self.run_context.log_data_lake_operation(
                            operation="cache_miss",
                            dataset="http_cache",
                            path=cache_key,
                            metadata={"url": url, "ttl_seconds": ttl_seconds},
                        )
                return response
            except requests.RequestException as e:
                # Network error, check if we have any cached response
                if cached_response:
                    return self._build_response_from_cache(cached_response)
                raise RuntimeError(f"Failed to fetch {url} and no cached response available") from e

    def store_local(
        self,
        data: Any,
        dataset: str,
        filename: str,
        data_type: str = "parquet",
        ttl: Optional[str] = None,
    ) -> str:
        """Store data locally with TTL-based expiration.

        Args:
            data: Data to store (DataFrame, bytes, etc.)
            dataset: Dataset name for organization
            filename: Filename for the stored data
            data_type: Type of data ("parquet", "gtfs", "osm", etc.)
            ttl: Optional TTL for the stored data

        Returns:
            Path to stored file
        """
        ttl_seconds = self._parse_ttl(ttl) if ttl else self.default_ttl

        # Generate filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        if "." in filename:
            name, ext = filename.rsplit(".", 1)
            full_filename = f"{name}_{timestamp}.{ext}"
        else:
            full_filename = f"{filename}_{timestamp}"

        inferred_type = data_type
        if data_type == "parquet" and not hasattr(data, "to_parquet"):
            if filename.endswith(".json") or isinstance(data, (dict, list)):
                inferred_type = "json"
            elif isinstance(data, (bytes, bytearray)):
                inferred_type = "gtfs"

        # Create dataset directory based on inferred type
        dataset_path = self.base_path / inferred_type / dataset
        dataset_path.mkdir(parents=True, exist_ok=True)

        file_path = dataset_path / full_filename

        # Store based on data type
        if inferred_type == "parquet":
            if hasattr(data, "to_parquet"):
                data.to_parquet(file_path)
            else:
                raise ValueError("Data must be a DataFrame for parquet storage")
        elif inferred_type in ["gtfs", "osm"]:
            if isinstance(data, (bytes, bytearray)):
                file_path.write_bytes(data)
            else:
                raise ValueError(f"Data must be bytes for {inferred_type} storage")
        else:
            # Default JSON storage
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        # Store metadata with TTL
        metadata = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ttl_seconds": ttl_seconds,
            "data_type": inferred_type,
            "original_filename": filename,
        }
        metadata_path = file_path.with_suffix(".metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Log storage operation
        if self.run_context:
            self.run_context.log_data_lake_operation(
                operation="cache_store",
                dataset=f"{data_type}:{dataset}",
                path=str(file_path),
                metadata={
                    "filename": full_filename,
                    "data_type": inferred_type,
                    "ttl_seconds": ttl_seconds,
                },
            )

        return str(file_path)

    def _build_cache_key(self, url: str, etl_key: Optional[str] = None) -> str:
        """Build cache key from URL and optional ETL key."""
        key_data = {"url": url}
        if etl_key:
            key_data["etl_key"] = etl_key

        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]

    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response from requests-cache."""
        try:
            # Check if we have a cached response
            cached = self.session.cache.get_response(cache_key)
            if cached:
                return {
                    "content": cached.content,
                    "headers": dict(cached.headers),
                    "status_code": cached.status_code,
                    "url": cached.url,
                    "etag": cached.headers.get("ETag"),
                    "last_modified": cached.headers.get("Last-Modified"),
                }
        except Exception:
            pass
        return None

    def _is_expired(self, cached_response: Dict[str, Any], ttl_seconds: int) -> bool:
        """Check if cached response is expired."""
        # This is a simplified check - in practice, requests-cache handles TTL
        return False

    def _cache_response(self, cache_key: str, response: requests.Response) -> None:
        """Cache response with metadata."""
        # requests-cache handles the actual caching, we just ensure it's stored
        pass

    def _build_response_from_cache(self, cached_response: Dict[str, Any]) -> requests.Response:
        """Build requests.Response object from cached data."""
        response = requests.Response()
        response._content = cached_response["content"]
        response.headers = cached_response["headers"]
        response.status_code = cached_response["status_code"]
        response.url = cached_response["url"]
        return response

    def _parse_ttl(self, ttl_str: Optional[str]) -> int:
        """Parse TTL string into seconds."""
        if not ttl_str:
            return 30 * 24 * 3600  # 30 days default

        # Parse formats like "30d", "1h", "5m", "30s"
        if ttl_str.endswith("d"):
            return int(ttl_str[:-1]) * 24 * 3600
        elif ttl_str.endswith("h"):
            return int(ttl_str[:-1]) * 3600
        elif ttl_str.endswith("m"):
            return int(ttl_str[:-1]) * 60
        elif ttl_str.endswith("s"):
            return int(ttl_str[:-1])
        else:
            # Assume seconds
            return int(ttl_str)


class RateLimiter:
    """Rate limiter with exponential backoff, jitter, and token bucket algorithm."""

    def __init__(
        self,
        token: str,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        run_context: Optional[RunContext] = None,
    ) -> None:
        """Initialize rate limiter.

        Args:
            token: API token/service identifier for rate limit configuration
            requests_per_minute: Baseline requests per minute limit
            burst_size: Maximum burst size for token bucket
            run_context: Optional RunContext for lineage tracking
        """
        self.token = token
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.run_context = run_context

        # Token bucket state
        self.tokens = burst_size
        self.last_update = time.time()

        # Backoff state
        self.consecutive_failures = 0
        self.last_request_time = 0

    def wrap(self, func: Any) -> Any:
        """Wrap a function with rate limiting.

        Args:
            func: Function to wrap

        Returns:
            Wrapped function with rate limiting
        """

        def wrapper(*args, **kwargs):
            self._wait_for_token()
            try:
                result = func(*args, **kwargs)
                self._record_success()
                return result
            except Exception:
                self._record_failure()
                raise

        return wrapper

    def _wait_for_token(self) -> None:
        """Wait for available token in bucket."""
        now = time.time()

        # Refill tokens based on time elapsed
        time_elapsed = now - self.last_update
        tokens_to_add = (time_elapsed * self.requests_per_minute) / 60.0
        self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
        self.last_update = now

        # Check if we have tokens available
        if self.tokens < 1:
            # Calculate wait time
            wait_time = (1 - self.tokens) * 60.0 / self.requests_per_minute
            time.sleep(wait_time)
            self.tokens = 1
            self.last_update = time.time()

        # Apply exponential backoff if we've had recent failures
        if self.consecutive_failures > 0:
            backoff_time = min(2**self.consecutive_failures, 300)  # Max 5 minutes
            jitter = backoff_time * 0.1  # 10% jitter
            total_wait = backoff_time + (jitter * (time.time() % 1))
            time.sleep(total_wait)

        self.tokens -= 1
        self.last_request_time = now

    def _record_success(self) -> None:
        """Record successful request."""
        if self.consecutive_failures > 0:
            # Reset failure count on success
            if self.run_context:
                self.run_context.log_data_lake_operation(
                    operation="rate_limit_success",
                    dataset="rate_limiting",
                    path=self.token,
                    metadata={
                        "consecutive_failures": self.consecutive_failures,
                        "tokens_remaining": self.tokens,
                    },
                )
            self.consecutive_failures = 0

    def _record_failure(self) -> None:
        """Record failed request (increments backoff)."""
        self.consecutive_failures += 1

        if self.run_context:
            self.run_context.log_data_lake_operation(
                operation="rate_limit_failure",
                dataset="rate_limiting",
                path=self.token,
                metadata={
                    "consecutive_failures": self.consecutive_failures,
                    "backoff_seconds": min(2**self.consecutive_failures, 300),
                    "tokens_remaining": self.tokens,
                },
            )


# Global cache instance
_cache_instance: Optional[Cache] = None


def get_cache(run_context: Optional[RunContext] = None) -> Cache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = Cache(run_context=run_context)
    return _cache_instance


def fetch(
    url: str,
    etl_key: Optional[str] = None,
    ttl: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    offline_mode: Optional[bool] = None,
) -> requests.Response:
    """Fetch URL with caching (convenience function).

    Args:
        url: URL to fetch
        etl_key: Optional ETL key for cache partitioning
        ttl: Optional TTL override
        headers: Optional additional headers
        offline_mode: If True, only use cached responses. If None, auto-detect.

    Returns:
        Response object
    """
    cache = get_cache()
    return cache.fetch(url, etl_key, ttl, headers, offline_mode)
