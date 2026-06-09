# Unit tests for CacheRepository using an in-memory SQLite database.
# We never hit the real filesystem — all DB operations happen in RAM.
import logging
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from cache.models import Base, CachedVulnerability
from cache.repository import CacheRepository


# --------------------------------------------------------------------------- #
#  Helpers / fixtures                                                          #
# --------------------------------------------------------------------------- #

def _make_repo(no_cache: bool = False) -> CacheRepository:
    """
    Build a CacheRepository backed by an in-memory SQLite database.
    We bypass the constructor's Alembic run and just use create_all() instead.
    """
    repo = CacheRepository.__new__(CacheRepository)
    repo.no_cache = no_cache
    repo._disabled = False
    repo._ttl_hours = 24

    if no_cache:
        repo._engine = None
        return repo

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    repo._engine = engine
    return repo


SAMPLE_VULNS = [
    {"id": "CVE-2023-1234", "severity": "HIGH", "description": "Test vuln"},
]

PACKAGE_KEY = "deb:libssl1.1:1.1.1f-1ubuntu2"
SOURCE = "osv"


# --------------------------------------------------------------------------- #
#  AC 3 — cache hit (valid entry)                                              #
# --------------------------------------------------------------------------- #

class TestCacheHit:
    def test_get_returns_data_when_entry_is_fresh(self):
        """AC 3: stored entry with future expires_at → cache hit."""
        repo = _make_repo()
        repo.set(PACKAGE_KEY, SOURCE, SAMPLE_VULNS, ttl_hours=24)

        result = repo.get(PACKAGE_KEY, SOURCE)

        assert result == SAMPLE_VULNS

    def test_get_returns_none_for_unknown_package(self):
        """No row in DB → cache miss (None)."""
        repo = _make_repo()

        result = repo.get("deb:unknown:0.0.1", SOURCE)

        assert result is None


# --------------------------------------------------------------------------- #
#  AC 4 — expired entry → miss                                                #
# --------------------------------------------------------------------------- #

class TestCacheExpiry:
    def test_get_returns_none_when_entry_is_expired(self):
        """AC 4: entry with past expires_at is ignored (cache miss)."""
        repo = _make_repo()

        # Insert a row that already expired an hour ago.
        past = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
        from sqlalchemy.orm import Session

        with Session(repo._engine) as session:
            row = CachedVulnerability(
                package_key=PACKAGE_KEY,
                source=SOURCE,
                payload='[{"id": "CVE-OLD", "severity": "LOW"}]',
                fetched_at=past - timedelta(hours=25),
                expires_at=past,
            )
            session.add(row)
            session.commit()

        result = repo.get(PACKAGE_KEY, SOURCE)

        assert result is None

    def test_set_then_get_with_zero_ttl_is_immediately_expired(self):
        """Edge-case: ttl_hours=0 expires instantly."""
        repo = _make_repo()
        repo.set(PACKAGE_KEY, SOURCE, SAMPLE_VULNS, ttl_hours=0)

        result = repo.get(PACKAGE_KEY, SOURCE)

        # expires_at == fetched_at, which is <= utcnow() → miss
        assert result is None


# --------------------------------------------------------------------------- #
#  AC 5 — --no-cache flag                                                      #
# --------------------------------------------------------------------------- #

class TestNoCacheFlag:
    def test_get_returns_none_when_no_cache(self):
        """AC 5: no-cache flag → get() always returns None."""
        repo = _make_repo(no_cache=True)

        result = repo.get(PACKAGE_KEY, SOURCE)

        assert result is None

    def test_set_is_silently_ignored_when_no_cache(self):
        """AC 5: no-cache flag → set() does nothing (no error raised)."""
        repo = _make_repo(no_cache=True)

        # Should not raise even though there is no DB engine.
        repo.set(PACKAGE_KEY, SOURCE, SAMPLE_VULNS)


# --------------------------------------------------------------------------- #
#  AC 6 — corrupted DB → WARNING logged, cache disabled, no crash             #
# --------------------------------------------------------------------------- #

class TestCorruptedDB:
    def test_get_disables_cache_and_logs_warning_on_db_error(self, caplog):
        """AC 6: OperationalError during get() → WARNING + _disabled=True."""
        repo = _make_repo()

        with patch.object(
            repo._engine, "connect", side_effect=OperationalError("simulated corruption", None, None)
        ):
            with caplog.at_level(logging.WARNING, logger="cache.repository"):
                result = repo.get(PACKAGE_KEY, SOURCE)

        assert result is None
        assert repo._disabled is True
        assert any("Cache read error" in r.message for r in caplog.records)

    def test_set_disables_cache_and_logs_warning_on_db_error(self, caplog):
        """AC 6: OperationalError during set() → WARNING + _disabled=True."""
        repo = _make_repo()

        with patch.object(
            repo._engine, "connect", side_effect=OperationalError("simulated corruption", None, None)
        ):
            with caplog.at_level(logging.WARNING, logger="cache.repository"):
                repo.set(PACKAGE_KEY, SOURCE, SAMPLE_VULNS)

        assert repo._disabled is True
        assert any("Cache write error" in r.message for r in caplog.records)

    def test_subsequent_calls_are_no_ops_after_disable(self):
        """Once disabled, further get/set calls do nothing and don't crash."""
        repo = _make_repo()
        repo._disabled = True

        assert repo.get(PACKAGE_KEY, SOURCE) is None
        repo.set(PACKAGE_KEY, SOURCE, SAMPLE_VULNS)  # should not raise
