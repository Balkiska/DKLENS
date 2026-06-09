# SQLAlchemy ORM model for the local CVE cache.
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CachedVulnerability(Base):
    """One cache entry = all vulnerabilities for one (package_key, source) pair."""

    __tablename__ = "cached_vulnerabilities"
    __table_args__ = (UniqueConstraint("package_key", "source", name="uq_cached_pkg_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Format: "{ecosystem}:{name}:{version}"  e.g. "deb:libssl1.1:1.1.1f-1ubuntu2"
    package_key: Mapped[str] = mapped_column(String(200), index=True)
    # Which API produced this data: "osv", "euvd", …
    source: Mapped[str] = mapped_column(String(50))
    # JSON-serialised list of vulnerability dicts
    payload: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
