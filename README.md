# Docklens

Docker image vulnerability scanner with an interactive terminal menu.

- Lists your local Docker images
- Extracts installed packages from the image filesystem
- Checks them against CVE databases (OSV + EUVD)
- Classifies vulnerabilities by severity (CRITICAL → LOW)
- Suggests fix versions and upgrade commands
- Exports results as PDF or JSON

## Supported distributions

| Distribution | Package format | Example images |
|---|---|---|
| Alpine Linux | APK | `alpine`, `python:alpine`, `node:alpine`, … |
| Wolfi / Chainguard | APK | `cgr.dev/chainguard/*`, `wolfi-base`, … |
| Debian | dpkg | `debian`, `python`, `node`, … |
| Ubuntu | dpkg | `ubuntu`, `python:slim`, … |

---

## Requirements

- [Docker](https://docs.docker.com/get-docker/) (running)
- [Devbox](https://www.jetify.com/devbox/docs/installing_devbox/)

```bash
curl -fsSL https://get.jetify.com/devbox | bash
```

---

## Installation

```bash
git clone https://github.com/Balkiska/Docklens.git
cd Docklens
devbox shell
```

Devbox automatically installs Python, Poetry, and all dependencies on first run.

---

## Usage

### Interactive menu (recommended)

```bash
./docklens start
```

This opens a full interactive menu:

1. Select a local Docker image with arrow keys
2. Docklens scans it automatically
3. After the scan, choose what to do:
   - Filter by severity (CRITICAL / HIGH / MEDIUM)
   - Export as PDF
   - Export as JSON
   - Scan another image
   - Quit

> No need to run `devbox shell` first — `./docklens start` works directly.

### CLI scan (non-interactive)

First enter the devbox shell:
```bash
devbox shell
```

Then run:
```bash
# Scan and display results as a table
poetry run python main.py scan <image>

# Output as JSON
poetry run python main.py scan <image> --format json

# Export to PDF
poetry run python main.py scan <image> --export report.pdf

# Bypass the local cache
poetry run python main.py scan <image> --no-cache
```

---

## Development

### Run the app

```bash
./docklens start
```

### Required for unit tests

```bash
devbox shell
```

### Run unit tests
```bash
poetry run pytest tests/unit/ -v
```

### Run lint

```bash
poetry run ruff check .
```

### Auto-fix lint errors

```bash
poetry run ruff check . --fix
```

---

## Local cache

Scan results are cached locally in SQLite so the same package is never looked up twice.

```bash
# Inspect the cache
sqlite3 ~/.cache/docklens/cache.db "SELECT package_key, source, expires_at FROM cached_vulnerabilities;"
```

---

## Pre-commit hooks

Hooks run automatically on every commit:

- **ruff** — lint, format, import sorting
- **pre-commit-hooks** — trailing whitespace, YAML validation, large files
- **gitleaks** — secret detection (API keys, tokens, passwords)

To bypass hooks (not recommended):

```bash
git commit -m "my message" --no-verify
```

---

## Auto-activation (optional)

The devbox environment can activate automatically when entering the project directory:

```bash
sudo apt install direnv
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
source ~/.bashrc
direnv allow
```

---

## License

Non-Commercial license. Commercial use requires prior written permission from the authors.
See [LICENSE](LICENSE) for details.
