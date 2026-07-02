# Alembic env.py — tells Alembic how to connect to the DB and where the models are.

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import our ORM models so Alembic knows what tables to manage.
from cache.models import Base

config = context.config
target_metadata = Base.metadata


def _get_url() -> str:
    """
    Return the database URL in this priority order:
    1. Explicit URL set by the programmatic caller (set_main_option)
    2. config/settings.py (runtime default for the real app)
    3. alembic.ini fallback
    """
    # When _run_migrations() calls alembic programmatically it sets this option.
    explicit = config.get_main_option("sqlalchemy.url", None)
    if explicit and "%(here)s" not in explicit:
        return explicit

    try:
        from config.settings import CACHE_DB_PATH

        return f"sqlite:///{CACHE_DB_PATH}"
    except ImportError:
        return explicit or ""


def run_migrations_offline() -> None:
    """Run migrations without a real DB connection (generates SQL script)."""
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = _get_url()

    connectable = engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
