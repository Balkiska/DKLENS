# CacheRepository: read/write CVE results to a local SQLite database.
import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from cache.models import CachedVulnerability

logger = logging.getLogger(__name__)


class CacheRepository:
    """
    Local SQLite cache for vulnerability query results.

    Usage:
        cache = CacheRepository(db_path=Path("~/.cache/dklens/cache.db").expanduser())
        result = cache.get("deb:libssl1.1:1.1.1f", "osv")
        if result is None:
            result = fetch_from_api(...)
            cache.set("deb:libssl1.1:1.1.1f", "osv", result)
    """

    def __init__(
        self, db_path: Path, no_cache: bool = False, ttl_hours: int = 24
    ) -> None:
        self.no_cache = no_cache
        self._disabled = False
        self._engine = None
        self._ttl_hours = ttl_hours

        if no_cache:
            # --no-cache flag: skip everything, don't touch the DB at all.
            return

        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._engine = create_engine(f"sqlite:///{db_path}")
            self._run_migrations(db_path)
        except Exception as exc:
            logger.warning(
                "Cache DB error on startup, cache disabled for this session: %s", exc
            )
            self._disabled = True

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def get(self, package_key: str, source: str) -> list | None:
        """
        Return cached vulnerabilities for (package_key, source), or None on miss/expiry.

        Returns None when:
        - no_cache=True
        - cache is disabled (corrupted DB)
        - no row found
        - the cached entry has expired
        """
        if self.no_cache or self._disabled or self._engine is None:
            return None

        try:
            with Session(self._engine) as session:
                row = (
                    session.query(CachedVulnerability)
                    .filter_by(package_key=package_key, source=source)
                    .order_by(CachedVulnerability.expires_at.desc())
                    .first()
                )
                if row is None:
                    return None
                if row.expires_at <= datetime.now(UTC).replace(tzinfo=None):
                    # Entry is stale — treat as a miss.
                    return None
                try:
                    return json.loads(row.payload)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(
                        "Corrupted cache payload for %s/%s, treating as miss",
                        package_key,
                        source,
                    )
                    return None
        except SQLAlchemyError as exc:
            logger.warning("Cache read error, disabling cache: %s", exc)
            self._disabled = True
            return None

    def set(
        self,
        package_key: str,
        source: str,
        vulnerabilities: list,
        ttl_hours: int | None = None,
    ) -> None:
        """
        Store vulnerability results in the cache with an expiry time.
        Does nothing when no_cache=True or the cache is disabled.
        Replaces any existing entry for the same (package_key, source) pair.
        """
        if self.no_cache or self._disabled or self._engine is None:
            return

        effective_ttl = ttl_hours if ttl_hours is not None else self._ttl_hours

        try:
            serialized = json.dumps(vulnerabilities)
        except (TypeError, ValueError) as exc:
            logger.warning(
                "Cache: cannot serialize vulnerabilities for %s, skipping set: %s",
                package_key,
                exc,
            )
            return

        try:
            now = datetime.now(UTC).replace(tzinfo=None)
            expires = now + timedelta(hours=effective_ttl)

            with Session(self._engine) as session:
                # Remove stale row (if any) before inserting the fresh one.
                session.query(CachedVulnerability).filter_by(
                    package_key=package_key, source=source
                ).delete()
                row = CachedVulnerability(
                    package_key=package_key,
                    source=source,
                    payload=serialized,
                    fetched_at=now,
                    expires_at=expires,
                )
                session.add(row)
                session.commit()
        except SQLAlchemyError as exc:
            logger.warning("Cache write error, disabling cache: %s", exc)
            self._disabled = True

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _run_migrations(self, db_path: Path) -> None:
        """Run Alembic migrations so the schema is always up to date."""
        from alembic import command as alembic_command
        from alembic.config import Config as AlembicConfig

        cfg = AlembicConfig()
        cfg.set_main_option(
            "script_location", str(Path(__file__).parent / "migrations")
        )
        cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
        alembic_command.upgrade(cfg, "head")
