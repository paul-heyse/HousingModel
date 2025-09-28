"""
Risk Panel state management and caching utilities.

This module provides state management, caching, and data persistence
for the Risk Panel dashboard.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..components.data_vintage_banner import get_freshness_status


class RiskStateManager:
    """Manages state persistence and caching for the Risk Panel dashboard."""

    def __init__(self):
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = 3600  # 1 hour default TTL

    def get_state(self, scope: str, target_id: str, key: str) -> Any:
        """
        Get cached state for a specific scope and target.

        Args:
            scope: Analysis scope (market or asset)
            target_id: Target identifier (MSA ID or asset ID)
            key: State key to retrieve

        Returns:
            Cached state value or None if not found/expired
        """
        cache_key = f"{scope}:{target_id}:{key}"

        # Check if cache entry exists and is not expired
        if cache_key in self._cache:
            timestamp = self._cache_timestamps.get(cache_key, 0)
            if datetime.now().timestamp() - timestamp < self._cache_ttl:
                return self._cache[cache_key]

        return None

    def set_state(self, scope: str, target_id: str, key: str, value: Any) -> None:
        """
        Set cached state for a specific scope and target.

        Args:
            scope: Analysis scope (market or asset)
            target_id: Target identifier (MSA ID or asset ID)
            key: State key to set
            value: Value to cache
        """
        cache_key = f"{scope}:{target_id}:{key}"
        self._cache[cache_key] = value
        self._cache_timestamps[cache_key] = datetime.now().timestamp()

    def clear_state(self, scope: Optional[str] = None, target_id: Optional[str] = None) -> None:
        """
        Clear cached state.

        Args:
            scope: Optional scope filter (clears all scopes if None)
            target_id: Optional target filter (clears all targets if None)
        """
        keys_to_remove = []

        for cache_key in self._cache.keys():
            scope_part, target_part, _ = cache_key.split(":", 2)

            if scope is None or scope_part == scope:
                if target_id is None or target_part == target_id:
                    keys_to_remove.append(cache_key)

        for key in keys_to_remove:
            del self._cache[key]
            del self._cache_timestamps[key]

    def get_risk_data(self, scope: str, target_id: str) -> Dict[str, Any]:
        """
        Get cached risk data for a scope and target.

        Args:
            scope: Analysis scope
            target_id: Target identifier

        Returns:
            Cached risk data or empty dict if not found
        """
        return self.get_state(scope, target_id, "risk_data") or {}

    def set_risk_data(self, scope: str, target_id: str, data: Dict[str, Any]) -> None:
        """
        Set cached risk data for a scope and target.

        Args:
            scope: Analysis scope
            target_id: Target identifier
            data: Risk data to cache
        """
        self.set_state(scope, target_id, "risk_data", data)

    def get_peril_overlays(self, msa_id: str) -> Dict[str, Any]:
        """
        Get cached peril overlay data for an MSA.

        Args:
            msa_id: MSA identifier

        Returns:
            Cached overlay data or empty dict if not found
        """
        return self.get_state("market", msa_id, "peril_overlays") or {}

    def set_peril_overlays(self, msa_id: str, overlays: Dict[str, Any]) -> None:
        """
        Set cached peril overlay data for an MSA.

        Args:
            msa_id: MSA identifier
            overlays: Overlay data to cache
        """
        self.set_state("market", msa_id, "peril_overlays", overlays)

    def get_scenario_results(self, scope: str, target_id: str) -> Dict[str, Any]:
        """
        Get cached scenario calculation results.

        Args:
            scope: Analysis scope
            target_id: Target identifier

        Returns:
            Cached scenario results or empty dict if not found
        """
        return self.get_state(scope, target_id, "scenario_results") or {}

    def set_scenario_results(self, scope: str, target_id: str, results: Dict[str, Any]) -> None:
        """
        Set cached scenario calculation results.

        Args:
            scope: Analysis scope
            target_id: Target identifier
            results: Scenario results to cache
        """
        self.set_state(scope, target_id, "scenario_results", results)

    def cleanup_expired_cache(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        current_time = datetime.now().timestamp()
        expired_keys = []

        for cache_key, timestamp in self._cache_timestamps.items():
            if current_time - timestamp >= self._cache_ttl:
                expired_keys.append(cache_key)

        for key in expired_keys:
            if key in self._cache:
                del self._cache[key]
            if key in self._cache_timestamps:
                del self._cache_timestamps[key]

        return len(expired_keys)


class RiskDataCache:
    """Intelligent caching for risk panel data with ETags and freshness tracking."""

    def __init__(self, cache_ttl_hours: int = 24):
        self.state_manager = RiskStateManager()
        self.cache_ttl = cache_ttl_hours * 3600  # Convert to seconds
        self.state_manager._cache_ttl = self.cache_ttl

    def get_overlay_data(self, msa_id: str, peril: str) -> Optional[Dict[str, Any]]:
        """
        Get cached overlay data for a specific MSA and peril.

        Args:
            msa_id: MSA identifier
            peril: Peril type

        Returns:
            Cached overlay data or None if not found/expired
        """
        cache_key = f"overlay:{msa_id}:{peril}"
        return self.state_manager.get_state("market", msa_id, cache_key)

    def set_overlay_data(self, msa_id: str, peril: str, data: Dict[str, Any], etag: str = None) -> None:
        """
        Set cached overlay data for a specific MSA and peril.

        Args:
            msa_id: MSA identifier
            peril: Peril type
            data: Overlay data to cache
            etag: Optional ETag for cache validation
        """
        cache_key = f"overlay:{msa_id}:{peril}"
        cached_data = data.copy()
        if etag:
            cached_data["_etag"] = etag
        cached_data["_cached_at"] = datetime.now().isoformat()

        self.state_manager.set_state("market", msa_id, cache_key, cached_data)

    def is_overlay_fresh(self, msa_id: str, peril: str) -> bool:
        """
        Check if cached overlay data is still fresh.

        Args:
            msa_id: MSA identifier
            peril: Peril type

        Returns:
            True if data is fresh, False if expired
        """
        cache_key = f"overlay:{msa_id}:{peril}"
        cached_data = self.state_manager.get_state("market", msa_id, cache_key)

        if not cached_data:
            return False

        cached_at_str = cached_data.get("_cached_at")
        if not cached_at_str:
            return False

        try:
            cached_at = datetime.fromisoformat(cached_at_str)
            age_seconds = (datetime.now() - cached_at).total_seconds()
            return age_seconds < self.cache_ttl
        except ValueError:
            return False

    def get_overlay_etag(self, msa_id: str, peril: str) -> Optional[str]:
        """
        Get ETag for cached overlay data.

        Args:
            msa_id: MSA identifier
            peril: Peril type

        Returns:
            ETag string or None if not found
        """
        cache_key = f"overlay:{msa_id}:{peril}"
        cached_data = self.state_manager.get_state("market", msa_id, cache_key)
        return cached_data.get("_etag") if cached_data else None

    def validate_overlay_cache(self, msa_id: str, peril: str, server_etag: str) -> bool:
        """
        Validate if cached overlay data matches server ETag.

        Args:
            msa_id: MSA identifier
            peril: Peril type
            server_etag: ETag from server

        Returns:
            True if cache is valid, False if needs refresh
        """
        cached_etag = self.get_overlay_etag(msa_id, peril)
        return cached_etag == server_etag

    def cleanup_cache(self) -> int:
        """
        Clean up expired cache entries.

        Returns:
            Number of entries removed
        """
        return self.state_manager.cleanup_expired_cache()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics and health information.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "total_entries": len(self.state_manager._cache),
            "cache_ttl_hours": self.cache_ttl / 3600,
            "expired_entries_removed": self.cleanup_cache(),
            "fresh_entries": sum(
                1 for key in self.state_manager._cache.keys()
                if self._is_entry_fresh(key)
            ),
        }

    def _is_entry_fresh(self, cache_key: str) -> bool:
        """Check if a cache entry is still fresh."""
        timestamp = self.state_manager._cache_timestamps.get(cache_key, 0)
        return (datetime.now().timestamp() - timestamp) < self.cache_ttl


# Global cache instance
risk_cache = RiskDataCache()
