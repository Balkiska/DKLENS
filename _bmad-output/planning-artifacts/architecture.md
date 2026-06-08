---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - docs/summary.txt
  - docs/tasks.txt
  - _bmad-output/planning-artifacts/prd.md
workflowType: architecture
project_name: Docklens
user_name: bkf
date: 2026-06-08
---

# Architecture: Docklens — Docker & Kubernetes Security Scanner

## 1. Overview

Docklens is a Python 3.11+ CLI/TUI tool with a clean layered architecture:

```
CLI layer      (Typer + InquirerPy)
    │
Core layer     (scanner, sbom, cve, scoring)
    │
Adapter layer  (docker_adapter, k8s_adapter, cve_sources)
    │
Persistence    (SQLite via SQLAlchemy + Alembic)
    │
Config         (pydantic + tomli)
```

The design principle is **stateless core with pluggable adapters**: the scanner engine never imports Docker SDK or Kubernetes client directly — it depends on abstract interfaces that adapters implement. This makes the engine independently testable and keeps Mode A / Mode B concerns separated.

---

## 2. Repository Layout

```
docklens/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── main.py            # Typer app entrypoint
│   ├── tui.py             # InquirerPy interactive menus
│   └── output.py          # Rich tables, panels, JSON/SBOM serialisers
├── core/
│   ├── __init__.py
│   ├── scanner.py         # Orchestration: SBOM → CVE lookup → score
│   ├── sbom.py            # SBOM data model + extractor protocol
│   ├── scoring.py         # Risk score + per-CVE severity ranking
│   └── models.py          # Shared Pydantic models (Package, CVE, ScanResult)
├── extractors/
│   ├── __init__.py
│   ├── base.py            # Abstract PackageExtractor protocol
│   ├── dpkg.py            # Debian/Ubuntu dpkg extractor
│   ├── apk.py             # Alpine apk extractor
│   ├── rpm.py             # RPM-based extractor
│   ├── pip.py             # Python pip extractor
│   └── npm.py             # Node npm extractor
├── adapters/
│   ├── __init__.py
│   ├── docker_adapter.py  # Docker SDK image export + layer extraction
│   └── k8s_adapter.py     # kubernetes-client workload enumeration
├── cve/
│   ├── __init__.py
│   ├── base.py            # Abstract CVESource protocol
│   ├── osv.py             # OSV API client
│   ├── nvd.py             # NVD API v2 client
│   ├── euvd.py            # EUVD API client
│   └── cpe.py             # CPE identifier builder
├── cache/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy ORM models
│   ├── repository.py      # Cache read/write with TTL
│   └── migrations/        # Alembic migration scripts
│       └── versions/
├── config/
│   ├── __init__.py
│   └── settings.py        # Pydantic Settings model, tomli loader
└── api/                   # Post-MVP FastAPI wrapper
    ├── __init__.py
    └── server.py

tests/
├── unit/
│   ├── test_scoring.py
│   ├── test_sbom.py
│   └── test_cpe.py
├── integration/
│   ├── test_docker_adapter.py
│   └── test_cve_sources.py
└── fixtures/
    ├── images/            # Minimal fake image layer fixtures
    └── cve_responses/     # Recorded API response fixtures

pyproject.toml
devbox.json
.pre-commit-config.yaml
```

---

## 3. Core Data Models (`core/models.py`)

All models use **Pydantic v2**.

```python
class Package(BaseModel):
    name: str
    version: str
    ecosystem: str          # "deb", "apk", "rpm", "pypi", "npm", "gem"
    cpe: str | None = None  # populated by cpe.py after extraction

class Vulnerability(BaseModel):
    id: str                 # CVE-XXXX-XXXXX or EUVD-XXXX
    source: str             # "osv" | "nvd" | "euvd"
    description: str
    cvss_score: float | None
    cvss_version: str | None   # "3.1" | "2.0"
    severity: str           # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN"
    affected_package: str
    installed_version: str
    fixed_version: str | None
    advisory_url: str | None
    published_at: datetime | None

class ScanResult(BaseModel):
    image: str
    scanned_at: datetime
    duration_seconds: float
    packages: list[Package]
    vulnerabilities: list[Vulnerability]
    risk_score: float       # 0.0–100.0
    summary: dict[str, int] # {"CRITICAL": 2, "HIGH": 5, ...}
```

---

## 4. Extractor Protocol (`extractors/base.py`)

```python
from typing import Protocol
from pathlib import Path
from docklens.core.models import Package

class PackageExtractor(Protocol):
    def can_handle(self, rootfs: Path) -> bool: ...
    def extract(self, rootfs: Path) -> list[Package]: ...
```

Each extractor (`dpkg.py`, `apk.py`, etc.) implements this protocol. The SBOM builder in `core/sbom.py` iterates all registered extractors, calls `can_handle()`, then `extract()`. Extractors are registered via a list in `core/sbom.py` (no plugin magic — explicit list).

---

## 5. CVE Source Protocol (`cve/base.py`)

```python
from typing import Protocol
from docklens.core.models import Package, Vulnerability

class CVESource(Protocol):
    name: str
    def query(self, packages: list[Package]) -> list[Vulnerability]: ...
```

`core/scanner.py` calls each registered source in sequence, deduplicates by CVE ID, and merges results. Sources are registered explicitly in `scanner.py`.

---

## 6. Docker Adapter (`adapters/docker_adapter.py`)

Uses `docker` Python SDK (no subprocess shell calls).

**Flow:**
1. `client.images.get(image_ref)` — validate image exists locally.
2. `image.save()` → stream tarball to `tempfile.TemporaryDirectory`.
3. Extract tarball layers with `tarfile` stdlib module.
4. Return `Path` to merged rootfs directory.
5. Caller responsible for cleanup (context manager pattern).

**No container is ever created.** `client.containers.*` APIs are never used.

---

## 7. Kubernetes Adapter (`adapters/k8s_adapter.py`)

Uses `kubernetes` Python client.

**Flow:**
1. Load config: `config.load_incluster_config()` (try first) → `config.load_kube_config()` (fallback).
2. `CoreV1Api().list_pod_for_all_namespaces()` — collect all pod specs.
3. `AppsV1Api().list_deployment_for_all_namespaces()` etc. for Deployments, DaemonSets, StatefulSets.
4. `BatchV1Api()` for Jobs, CronJobs.
5. Deduplicate image references by `image:tag` string.
6. Return `list[str]` of unique image references.

**RBAC required (read-only):**
```yaml
rules:
- apiGroups: ["", "apps", "batch"]
  resources: ["pods", "deployments", "daemonsets", "statefulsets", "jobs", "cronjobs"]
  verbs: ["get", "list"]
```

---

## 8. Cache Layer (`cache/`)

**Technology:** SQLite (file at `~/.cache/docklens/cache.db`) via SQLAlchemy 2.x ORM. Alembic for migrations.

**ORM Model:**
```python
class CachedVulnerability(Base):
    __tablename__ = "cached_vulnerabilities"
    id: Mapped[int] = mapped_column(primary_key=True)
    package_key: Mapped[str]       # "pypi:requests:2.28.0"
    source: Mapped[str]            # "osv" | "nvd" | "euvd"
    payload: Mapped[str]           # JSON blob of Vulnerability list
    fetched_at: Mapped[datetime]
    expires_at: Mapped[datetime]
```

**Cache key format:** `{ecosystem}:{name}:{version}` (e.g. `deb:libssl1.1:1.1.1f-1ubuntu2`).

**TTL:** Default 24 h, configurable via `config.toml`. `--no-cache` skips reads and writes.

---

## 9. Configuration (`config/settings.py`)

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(toml_file="~/.config/docklens/config.toml")

    cache_ttl_hours: int = 24
    nvd_api_key: str | None = None
    default_output_format: str = "rich"   # "rich" | "json"
    exit_on_critical: bool = False
    cache_db_path: Path = Path("~/.cache/docklens/cache.db")
    log_level: str = "WARNING"
```

`tomli` reads the TOML file; Pydantic validates. Environment variables override file values (prefix `DOCKLENS_`).

---

## 10. Scoring Logic (`core/scoring.py`)

**Per-CVE adjusted score:**
```
adjusted = cvss_base * age_multiplier * exposure_factor

age_multiplier:
  < 30 days  → 1.0
  30–180 days → 1.1
  > 180 days  → 1.2

exposure_factor:
  package installed setuid/root context → 1.1  (heuristic, distro-based)
  otherwise → 1.0
```

**Severity label from adjusted score:**
- ≥ 9.0 → CRITICAL
- 7.0–8.9 → HIGH
- 4.0–6.9 → MEDIUM
- < 4.0 → LOW

**Image Risk Score (0–100):**
```
risk = min(100, sum(adjusted_score * weight for each CVE))

weight:
  CRITICAL → 10
  HIGH     → 4
  MEDIUM   → 1
  LOW      → 0.2
```

---

## 11. CLI Structure (`cli/main.py`)

```python
app = typer.Typer(name="docklens", help="Docker & Kubernetes security scanner")

@app.command()
def scan(
    image: str | None = typer.Argument(None),
    k8s: bool = typer.Option(False, "--k8s"),
    pull: bool = typer.Option(False, "--pull"),
    exit_on_critical: bool = typer.Option(False, "--exit-on-critical"),
    output: OutputFormat = typer.Option(OutputFormat.rich, "--output"),
    output_file: Path | None = typer.Option(None, "--output-file"),
    sbom: bool = typer.Option(False, "--sbom"),
    no_cache: bool = typer.Option(False, "--no-cache"),
    namespace: str | None = typer.Option(None, "--namespace"),
    verbose: bool = typer.Option(False, "--verbose"),
): ...
```

When `image` is None and `--k8s` is False, the TUI menu is presented via `cli/tui.py`.

---

## 12. Output Layer (`cli/output.py`)

**Rich output:**
- `render_summary_panel(result: ScanResult)` → Rich `Panel`
- `render_cve_table(result: ScanResult)` → Rich `Table` (columns: CVE ID, Package, Version, Fix, CVSS, Severity, Link)
- Severity column coloured via Rich markup: `[red]CRITICAL[/red]`, `[orange3]HIGH[/orange3]`, `[yellow]MEDIUM[/yellow]`, `[white]LOW[/white]`

**JSON output:**
- `result.model_dump_json(indent=2)` written to stdout or file.

**SBOM output:**
- CycloneDX v1.4 JSON schema — hand-written serialiser in `output.py` (no heavy CycloneDX library dependency in v1).

---

## 13. CPE Mapping (`cve/cpe.py`)

Strategy (in priority order):
1. **Known-package table** — a bundled JSON lookup table mapping `{ecosystem}:{name}` → `{cpe_vendor}:{cpe_product}`.
2. **Heuristic** — vendor = package name, product = package name (works for ~60% of packages).
3. **Fallback** — mark `cpe = None`, include in SBOM but skip NVD CPE query; OSV query still runs by ecosystem+version.

The lookup table is maintained in `cve/data/cpe_lookup.json` and updated by a separate maintenance script (out of scope for v1 stories).

---

## 14. Technology Decisions

| Decision | Choice | Rationale |
|---|---|---|
| HTTP client | `httpx` (async-capable) | Native async support for concurrent CVE API calls; replaces requests |
| ORM | SQLAlchemy 2.x | Type-safe mapped_column API; Alembic migration support |
| Config | pydantic-settings + tomli | Type validation + TOML parsing; tomli is stdlib in Python 3.11 |
| CLI | Typer | Thin wrapper over Click; native type annotations |
| TUI prompts | InquirerPy | Rich-compatible interactive prompts |
| Terminal output | Rich | De facto standard for Python terminal UIs |
| Image inspection | Docker SDK (no subprocess) | Official SDK; no shell injection risk |
| K8s client | kubernetes-client/python | Official; supports in-cluster + kubeconfig |
| Testing | pytest + pytest-httpx | pytest-httpx mocks httpx calls without monkey-patching |

---

## 15. Error Handling Conventions

- **CVE API failures** — caught at the source adapter level; logged as WARNING; scan continues with partial results. `ScanResult` includes a `warnings: list[str]` field.
- **Docker image not found** — raises `DocklensError` (custom exception in `core/models.py`); CLI prints user-facing message and exits non-zero.
- **K8s connection failure** — raises `DocklensError`; CLI prints message suggesting `kubectl get pods` as a connectivity test.
- **Cache DB corruption** — caught on startup; cache silently disabled for the session; WARNING logged.

---

## 16. Testing Strategy

- **Unit tests** (`tests/unit/`): pure logic — scoring formula, CPE builder, extractor parsing. No I/O. Fast.
- **Integration tests** (`tests/integration/`): Docker adapter tested against a real minimal image (scratch + one layer); CVE sources tested with `pytest-httpx` recorded responses.
- **Fixtures** (`tests/fixtures/`): minimal rootfs directories simulating dpkg/apk layouts; recorded JSON API responses.
- **No mocking of SQLAlchemy** — integration tests use an in-memory SQLite DB (`sqlite:///:memory:`).

---

## 17. Security Considerations

- No image filesystem content leaves the local machine. Only `{name, version, ecosystem}` tuples are sent to CVE APIs.
- `NVD_API_KEY` is read from environment or config file; never logged.
- The Docker adapter uses the SDK's `image.save()` stream — no `docker export` subprocess, no shell expansion.
- Temp directories created with `tempfile.TemporaryDirectory` are cleaned up on exit and SIGINT.

---

## 18. Phased Delivery Map

| Phase | Scope |
|---|---|
| **MVP (Mode A)** | CLI entry, Docker adapter, SBOM extractors (dpkg/apk/pip/npm), OSV + NVD CVE lookup, SQLite cache, scoring, Rich output, JSON export, `--exit-on-critical`, config, GitHub Actions |
| **v2** | Mode B (Kubernetes), EUVD source, gem/Go/Rust extractors, CycloneDX SBOM export, REST API |
