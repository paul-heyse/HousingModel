"""Tests for cache and rate limiting functionality."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from aker_core.cache import Cache, RateLimiter, get_cache, is_offline_mode
from aker_core.run import RunContext


@pytest.fixture
def temp_cache() -> Cache:
    """Create a temporary cache for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = Cache(base_path=temp_dir, default_ttl="1h")  # Shorter TTL for tests
        yield cache


@pytest.fixture
def mock_run_context() -> RunContext:
    """Create a mock RunContext for testing."""
    return MagicMock(spec=RunContext)


class TestCacheOfflineMode:
    """Test offline mode detection."""

    def test_is_offline_mode_true_when_no_network(self) -> None:
        """Test offline mode detection when network is unavailable."""
        with patch("socket.create_connection", side_effect=OSError("Network unreachable")):
            assert is_offline_mode() is True

    def test_is_offline_mode_false_when_network_available(self) -> None:
        """Test offline mode detection when network is available."""
        with patch("socket.create_connection", return_value=MagicMock()):
            assert is_offline_mode() is False


class TestCacheBasic:
    """Test basic cache functionality."""

    def test_cache_init_creates_directories(self, temp_cache: Cache) -> None:
        """Test that cache initialization creates necessary directories."""
        assert temp_cache.base_path.exists()
        assert temp_cache.base_path.is_dir()

    def test_cache_key_generation(self, temp_cache: Cache) -> None:
        """Test cache key generation."""
        key1 = temp_cache._build_cache_key("https://example.com/test", "etl1")
        key2 = temp_cache._build_cache_key("https://example.com/test", "etl2")
        key3 = temp_cache._build_cache_key("https://example.com/other", "etl1")

        # Same URL + ETL key should produce same key
        assert key1 == temp_cache._build_cache_key("https://example.com/test", "etl1")
        # Different ETL key should produce different key
        assert key1 != key2
        # Different URL should produce different key
        assert key1 != key3

    def test_ttl_parsing(self, temp_cache: Cache) -> None:
        """Test TTL string parsing."""
        assert temp_cache._parse_ttl("30d") == 30 * 24 * 3600
        assert temp_cache._parse_ttl("1h") == 3600
        assert temp_cache._parse_ttl("5m") == 300
        assert temp_cache._parse_ttl("30s") == 30
        assert temp_cache._parse_ttl("3600") == 3600
        assert temp_cache._parse_ttl(None) == 30 * 24 * 3600  # default


class TestLocalStorage:
    """Test local data storage functionality."""

    def test_store_parquet_data(self, temp_cache: Cache) -> None:
        """Test storing Parquet data."""
        df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})

        result_path = temp_cache.store_local(df, "test_dataset", "test.parquet", "parquet")

        assert Path(result_path).exists()
        assert Path(result_path).suffix == ".parquet"

        # Check metadata file was created
        metadata_path = Path(result_path).with_suffix(".metadata.json")
        assert metadata_path.exists()

        # Verify metadata content
        with open(metadata_path) as f:
            metadata = json.load(f)
        assert metadata["data_type"] == "parquet"
        assert metadata["original_filename"] == "test.parquet"
        assert "created_at" in metadata
        assert "ttl_seconds" in metadata

    def test_store_gtfs_data(self, temp_cache: Cache) -> None:
        """Test storing GTFS data."""
        gtfs_data = b"test gtfs content"

        result_path = temp_cache.store_local(gtfs_data, "gtfs_dataset", "routes.txt", "gtfs")

        assert Path(result_path).exists()
        assert Path(result_path).name.startswith("routes_")

        # Verify content was stored
        with open(result_path, "rb") as f:
            stored_data = f.read()
        assert stored_data == gtfs_data

    def test_store_json_data(self, temp_cache: Cache) -> None:
        """Test storing generic JSON data."""
        json_data = {"key": "value", "number": 42}

        result_path = temp_cache.store_local(
            json_data, "json_dataset", "config.json", data_type="json"
        )

        assert Path(result_path).exists()

        # Verify content was stored
        with open(result_path) as f:
            stored_data = json.load(f)
        assert stored_data == json_data


class TestRateLimiter:
    """Test rate limiter functionality."""

    def test_rate_limiter_init(self) -> None:
        """Test rate limiter initialization."""
        limiter = RateLimiter("test_token", requests_per_minute=60, burst_size=10)

        assert limiter.token == "test_token"
        assert limiter.requests_per_minute == 60
        assert limiter.burst_size == 10
        assert limiter.tokens == 10
        assert limiter.consecutive_failures == 0

    def test_rate_limiter_wrap_success(self, mock_run_context: RunContext) -> None:
        """Test rate limiter wrapping a successful function."""
        limiter = RateLimiter("test_token", run_context=mock_run_context)

        def dummy_function():
            return "success"

        wrapped_func = limiter.wrap(dummy_function)
        result = wrapped_func()

        assert result == "success"
        # Should have recorded success (resetting failure count)
        assert limiter.consecutive_failures == 0

    def test_rate_limiter_wrap_failure(self, mock_run_context: RunContext) -> None:
        """Test rate limiter wrapping a failing function."""
        limiter = RateLimiter("test_token", run_context=mock_run_context)

        def failing_function():
            raise ValueError("Test error")

        wrapped_func = limiter.wrap(failing_function)

        with pytest.raises(ValueError):
            wrapped_func()

        # Should have recorded failure
        assert limiter.consecutive_failures == 1

    def test_rate_limiter_token_refill(self) -> None:
        """Test token bucket refill over time."""
        limiter = RateLimiter("test_token", requests_per_minute=60, burst_size=10)

        # Use all tokens
        for _ in range(10):
            limiter._wait_for_token()

        assert limiter.tokens < 1

        # Wait a bit and check if tokens are refilled
        import time

        time.sleep(0.1)  # Small delay to allow token refill

        # Tokens should be partially refilled
        assert limiter.tokens > 0


class TestLineageIntegration:
    """Test lineage tracking integration."""

    def test_cache_operations_log_lineage(self, mock_run_context: RunContext) -> None:
        """Test that cache operations are logged to lineage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = Cache(base_path=temp_dir, run_context=mock_run_context)

        # Test cache hit logging (mock a cached response)
        with patch.object(cache, "_get_cached_response", return_value={"content": b"test"}):
            with patch.object(cache, "_is_expired", return_value=False):
                try:
                    cache.fetch("https://example.com/test")
                except Exception:
                    pass  # We expect this to fail but lineage should still be logged

        # Verify lineage was logged
        mock_run_context.log_data_lake_operation.assert_called()

    def test_rate_limiter_logs_lineage(self, mock_run_context: RunContext) -> None:
        """Test that rate limiter operations are logged to lineage."""
        limiter = RateLimiter("test_token", run_context=mock_run_context)

        def failing_function():
            raise ValueError("Test error")

        wrapped_func = limiter.wrap(failing_function)

        with pytest.raises(ValueError):
            wrapped_func()

        # Verify lineage was logged for failure
        mock_run_context.log_data_lake_operation.assert_called()


class TestOfflineMode:
    """Test offline mode functionality."""

    def test_fetch_in_offline_mode_with_cache(
        self, temp_cache: Cache, mock_run_context: RunContext
    ) -> None:
        """Test fetching in offline mode when cache is available."""
        temp_cache = Cache(base_path=tempfile.mkdtemp(), run_context=mock_run_context)

        # Mock a cached response
        cached_response = {
            "content": b'{"test": "data"}',
            "headers": {"content-type": "application/json"},
            "status_code": 200,
            "url": "https://example.com/api",
        }

        with patch.object(temp_cache, "_get_cached_response", return_value=cached_response):
            with patch.object(temp_cache, "_is_expired", return_value=False):
                with patch.object(
                    temp_cache, "_build_response_from_cache", return_value=MagicMock()
                ):
                    response = temp_cache.fetch("https://example.com/api", offline_mode=True)
                    assert response is not None

    def test_fetch_in_offline_mode_no_cache(self) -> None:
        """Test fetching in offline mode when no cache is available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_cache = Cache(base_path=temp_dir)
            with patch.object(temp_cache, "_get_cached_response", return_value=None):
                with pytest.raises(RuntimeError, match="Cache miss.*offline mode"):
                    temp_cache.fetch("https://example.com/api", offline_mode=True)


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_cache_and_rate_limiter_together(self, mock_run_context: RunContext) -> None:
        """Test cache and rate limiter working together."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = Cache(base_path=temp_dir, run_context=mock_run_context)
            limiter = RateLimiter("test_token", run_context=mock_run_context)

        # Create a function that uses both cache and rate limiting
        @limiter.wrap
        def fetch_with_rate_limit(url):
            return cache.fetch(url)

        # This should work without errors
        # (We can't easily test the full flow without mocking HTTP requests)
        assert callable(fetch_with_rate_limit)

    def test_get_cache_singleton(self, mock_run_context: RunContext) -> None:
        """Test that get_cache returns a singleton."""
        # Note: This test is limited because get_cache creates a cache with /data path
        # In real usage, you'd want to use a different base path or patch the creation
        with patch("aker_core.cache.Cache") as mock_cache_class:
            mock_cache_instance = MagicMock()
            mock_cache_class.return_value = mock_cache_instance

            cache1 = get_cache(mock_run_context)
            cache2 = get_cache(mock_run_context)

            assert cache1 is cache2
            assert cache1 is mock_cache_instance
