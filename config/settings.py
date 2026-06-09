# Application-wide settings for Docklens.
from pathlib import Path

from cache.repository import CacheRepository

# Where the SQLite cache file lives on the user's machine.
CACHE_DB_PATH: Path = Path.home() / ".cache" / "docklens" / "cache.db"

# How long (in hours) a cache entry is considered valid.
CACHE_TTL_HOURS: int = 24

# Module-level singleton — created once when the app starts.
# Pass no_cache=True (e.g. from the --no-cache CLI flag) to disable caching.
_cache_instance: CacheRepository | None = None


def get_cache(no_cache: bool = False) -> CacheRepository:
    """
    Return the shared CacheRepository instance.
    Creates it on first call; subsequent calls return the same object.
    """
    global _cache_instance
    if _cache_instance is None or _cache_instance.no_cache != no_cache:
        _cache_instance = CacheRepository(db_path=CACHE_DB_PATH, no_cache=no_cache, ttl_hours=CACHE_TTL_HOURS)
    return _cache_instance
