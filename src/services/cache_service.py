"""Cache service for NeuroNote."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from src.config import config
from src.database.repository import get_search_cache, save_search_cache
from src.utils.logging import setup_logging

logger = setup_logging(__name__)

# TTL in seconds for different cache types
CACHE_TTL = {
    "chat": 86400,  # 24 hours
    "study": 604800,  # 7 days
    "flashcards": 604800,
    "formula": 604800,
    "highlights": 604800,
    "search": 43200,  # 12 hours
    "general": 3600,  # 1 hour
}


class CacheService:
    """Manage caching of AI-generated content."""

    def __init__(self, default_ttl: int = 3600) -> None:
        self.default_ttl = default_ttl
        self._memory_cache: dict[str, tuple[Any, datetime]] = {}

    def lookup(self, key: str, cache_type: str = "general") -> Optional[dict[str, Any]]:
        """Lookup cached response by key.

        Args:
            key: Cache key.
            cache_type: Type of cache for TTL.

        Returns:
            Cached response dict or None.
        """
        # Check memory cache first
        if key in self._memory_cache:
            data, expiry = self._memory_cache[key]
            if datetime.now() < expiry:
                logger.debug("Memory cache hit: %s", key)
                return data
            del self._memory_cache[key]

        ttl = CACHE_TTL.get(cache_type, self.default_ttl)
        entry = get_search_cache(key)
        if not entry:
            return None

        created = entry.get("created_at")
        if isinstance(created, str):
            created_dt = datetime.fromisoformat(created)
        elif isinstance(created, datetime):
            created_dt = created
        else:
            return None

        if datetime.now() - created_dt > timedelta(seconds=ttl):
            logger.debug("Cache expired: %s", key)
            return None

        response = entry.get("response", {})
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                return None

        # Store in memory cache for faster subsequent access
        self._memory_cache[key] = (response, datetime.now() + timedelta(seconds=ttl))
        logger.debug("Cache hit: %s (%s)", key, cache_type)
        return response

    def store(self, key: str, data: dict[str, Any], cache_type: str = "general",
              document_ids: Optional[list[int]] = None) -> None:
        """Store response in cache.

        Args:
            key: Cache key.
            data: Data to cache.
            cache_type: Type of cache for TTL.
            document_ids: Related document IDs.
        """
        try:
            save_search_cache(
                query_hash=key,
                query_text=data.get("query", key),
                response=data,
                document_ids=document_ids or [],
            )
            ttl = CACHE_TTL.get(cache_type, self.default_ttl)
            self._memory_cache[key] = (data, datetime.now() + timedelta(seconds=ttl))
            logger.debug("Cache stored: %s (%s)", key, cache_type)
        except Exception as exc:
            logger.warning("Cache store failed: %s", exc)

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """Invalidate cache entries matching pattern.

        Args:
            pattern: Optional key prefix pattern to invalidate.

        Returns:
            Number of invalidated entries.
        """
        if pattern:
            keys_to_remove = [k for k in list(self._memory_cache.keys()) if k.startswith(pattern)]
            count = len(keys_to_remove)
            for k in keys_to_remove:
                del self._memory_cache[k]
            logger.info("Invalidated %d memory cache entries matching '%s'", count, pattern)
            return count

        count = len(self._memory_cache)
        self._memory_cache.clear()
        logger.info("Cleared all memory cache: %d entries", count)
        return count

    def clear_all(self) -> None:
        """Clear all cached data (memory only since SQLite needs explicit cleanup)."""
        self._memory_cache.clear()
        logger.info("Cleared all cache")

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with cache stats.
        """
        return {
            "memory_entries": len(self._memory_cache),
            "memory_keys": list(self._memory_cache.keys()),
        }


# Global cache instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create the global cache service instance.

    Returns:
        CacheService instance.
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service