# Deferred Work

## Deferred from: code review of 3-1-set-up-local-cve-data-storage (2026-06-08)

- `get_cache()` singleton not thread-safe — no lock around `_cache_instance` assignment in `config/settings.py`. Relevant if the app ever uses threading.
- Old SQLAlchemy engine not disposed when `get_cache()` recreates the instance — can cause `ResourceWarning` in tests and file-lock contention on Windows.
- `_disabled` flag never reset after transient `OperationalError` — any brief DB lock disables caching for the entire process. Relevant for long-running or batch-scan mode.
- Tests bypass `__init__` via `__new__` — Alembic migration path (`_run_migrations`) is never exercised by the test suite. A divergence between the ORM model and migration script would go undetected.
- Expired rows are never deleted — `cache.db` grows indefinitely; a future `purge()` method or `DELETE WHERE expires_at < now` in `get()` would fix this.
- No payload size guard in `set()` — very large CVE lists are stored without validation or truncation. Add a max-size check before `json.dumps`.
- `_run_migrations()` called on every `CacheRepository` construction — minor repeated Alembic round-trips; a class-level "already migrated" flag would eliminate the overhead.
- Tests missing compound `(package_key, source)` lookup coverage — no test verifies that two sources for the same package are stored and retrieved independently.

## Deferred from: code review of 3-1-set-up-local-cve-data-storage, Run 2 (2026-06-08)

- Tests bypass `__init__` via `__new__` — real startup/migration path never exercised by the test suite.
- `get_cache()` singleton not thread-safe; old engine not disposed on recreation.
- `get()` returns raw dicts, not `Vulnerability(**d)` model instances as Dev Notes specify — `Vulnerability` type not yet built; fix when the vulnerability model is introduced.
- Delete-before-insert in `set()` has a brief race window in WAL mode — relevant only if the CLI is ever run in parallel (e.g., `xargs`).
- `CACHE_DB_PATH` evaluated at import time; crashes if `$HOME` is unset — add lazy evaluation or a fallback path.
- `_get_url()` returns empty string when nothing configured → cryptic Alembic error; add a guard that raises with a helpful message.
- `_engine` non-None after migration fails with `_disabled=True`; if `_disabled` is ever manually reset externally, queries hit an uninitialised schema.
- Expired rows never cleaned up — `cache.db` grows indefinitely; a periodic `DELETE WHERE expires_at < now` would help.

## Deferred from: code review of 3-1-set-up-local-cve-data-storage, Run 3 (2026-06-08)

- Negative `ttl_hours` silently creates permanently-expired cache entries — `get()` always returns None with no error raised. Add a `ttl_hours >= 0` guard or let the caller own the validation.
