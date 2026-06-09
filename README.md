# Docklens
Container/Docker image vulnerability scanner

A Python CLI tool that:
- Takes a Docker image
- Analyses the installed packages
- Compares them with a CVE database
- Classifies vulnerabilities by severity
- Suggests patches/upgrades
- Displays everything in a clean terminal menu

# Environnement
install devbox
```
curl -fsSL https://get.jetify.com/devbox | bash
```
run devbox
```
devbox shell
```

# Pre-commit Hooks
With every new commit, verification hooks will be executed. To bypass them, run the following command:
```
git commit -m "what my commit does blablabla" --no-verify
```
### Pre-commit tools
**pre-commit-hooks**: repository hygiene checks
- trailing whitespace, end-of-file, YAML validation, large files, etc.
-> https://github.com/pre-commit/pre-commit-hooks

**ruff**: linting + auto-fix + import sorting + code formatting
- replaces flake8, isort, and black
-> https://docs.astral.sh/ruff/

**gitleaks**: secret detection
- detects API keys, tokens, passwords (160+ secret types)
-> https://github.com/gitleaks/gitleaks
# Auto-activation (direnv)
The devbox environment activates automatically when entering the repository directory.
This requires a **one-time setup per machine**:
```
sudo apt install direnv
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
source ~/.bashrc
direnv allow
```
After that, opening the repository directory will activate the environment automatically.

## Testing the CVE cache (Story 3.1)

The cache module stores vulnerability query results in a local SQLite database so the same package is never looked up twice.

Dependencies (`sqlalchemy`, `alembic`) are declared in `pyproject.toml` and installed automatically when the devbox shell starts (`poetry install`).

**Run the unit tests:**
```
pytest tests/unit/test_cache_repository.py -v
```

You should see 9 tests pass, covering:
- Cache hit (fresh entry returned)
- Cache miss (unknown package → `None`)
- Expiry (old entry ignored → `None`)
- `--no-cache` flag (reads and writes both skipped)
- Corrupted DB (warning logged, scan continues)

**Try it manually in a Python shell:**
```python
from pathlib import Path
from cache.repository import CacheRepository

# Opens (or creates) ~/.cache/docklens/cache.db automatically
cache = CacheRepository(db_path=Path.home() / ".cache/docklens/cache.db")

# Store some fake results
cache.set("deb:libssl1.1:1.1.1f", "osv", [{"id": "CVE-2023-1234", "severity": "HIGH"}])

# Read them back — returns the list, no HTTP call
print(cache.get("deb:libssl1.1:1.1.1f", "osv"))

# Unknown package → None (would trigger a real API call)
print(cache.get("deb:unknown:0.0.1", "osv"))
```

**Disable the cache** (useful for debugging):
```python
cache = CacheRepository(db_path=..., no_cache=True)
# get() always returns None, set() does nothing
```

The database file lives at `~/.cache/docklens/cache.db`. You can inspect it with any SQLite viewer or:
```
sqlite3 ~/.cache/docklens/cache.db "SELECT package_key, source, expires_at FROM cached_vulnerabilities;"
```

## License

This project is licensed under a Non-Commercial license.
Commercial use (including SaaS, resale, or paid services) requires prior written permission from the author.
See LICENSE for details.
