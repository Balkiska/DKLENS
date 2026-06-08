---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - docs/summary.txt
  - docs/tasks.txt
---

# Docklens - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Docklens, decomposing the requirements from the PRD and Architecture into implementable stories. Each story maps to a GitHub issue. Stories are ordered by implementation dependency.

---

## Requirements Inventory

### Functional Requirements

FR-1: CLI entry point — `docklens --help` shows all commands and flags.
FR-2: Interactive TUI mode — running `docklens` without arguments opens InquirerPy menu.
FR-3: Non-interactive scan command — `docklens scan <image>` runs a full scan and prints results.
FR-4: Validate and resolve image reference — verify image exists locally or pull with `--pull`.
FR-5: Export image filesystem — extract image layers to temp dir using Docker SDK; no container execution.
FR-6: Dockerfile support — `--dockerfile` flag builds a temp image, scans, and discards.
FR-7: Detect Linux distribution — read `/etc/os-release` and fallbacks; return distro+version.
FR-8: Extract system packages — dpkg, apk, rpm package databases.
FR-9: Extract language-level packages — pip, npm (site-packages, node_modules).
FR-10: Map packages to CPE identifiers — bundled lookup table + heuristic fallback.
FR-11: Query OSV API — `https://api.osv.dev/v1/query` per package.
FR-12: Query NVD API v2 — CPE match strings; `NVD_API_KEY` env var for higher rate limits.
FR-13: Query EUVD API — supplement NVD/OSV results; graceful fallback on downtime.
FR-14: Local CVE cache — SQLite via SQLAlchemy; TTL default 24h; Alembic migrations; `--no-cache` flag.
FR-15: Per-CVE severity ranking — CVSS-based with age and exposure weighting.
FR-16: Image Risk Score — composite 0–100 score from CVE distribution.
FR-17: Exit-on-critical flag — exit code 1 when CRITICAL CVE found with `--exit-on-critical`.
FR-18: Patched version suggestion — display fixed version from CVE record.
FR-19: Fix advisory links — OSC-8 hyperlinks or plain URL fallback per CVE row.
FR-20: Rich terminal table — CVE ID, Package, Version, Fix, CVSS, Severity, Link columns.
FR-21: Summary header panel — image name, totals by severity, Risk Score, timestamp, duration.
FR-22: JSON export — `--output json` to stdout or `--output-file`.
FR-23: SBOM export — `--sbom` writes CycloneDX v1.4 JSON.
FR-24: K8s image enumeration — list images from Pods, Deployments, DaemonSets, StatefulSets, Jobs.
FR-25: RBAC requirements — read-only `get`/`list` only; no cluster state modification.
FR-26: Off-cluster and in-cluster support — kubeconfig + in-cluster ServiceAccount token.
FR-27: User config file — `~/.config/docklens/config.toml` with pydantic + tomli.
FR-28: POST /scan API endpoint — FastAPI; returns same JSON as `--output json`.
FR-29: API server command — `docklens serve --port 8080`.
FR-30: CI GitHub Actions workflow — `.github/workflows/scan.yml`; fails PR on CRITICAL CVE.

### Non-Functional Requirements

NFR-1: Performance — scan of a standard image (≤500 MB) completes in under 60 seconds including API calls (no cache).
NFR-2: Security — no image content transmitted externally; only `{name, version, ecosystem}` tuples sent to CVE APIs.
NFR-3: Reliability — API failures (NVD, OSV, EUVD) are non-fatal; scan completes with warning and partial results.
NFR-4: Portability — runs on Linux and macOS; Docker daemon must be accessible.
NFR-5: Observability — `--verbose` flag enables debug logging to stderr; structured Python `logging`.
NFR-6: Cache hygiene — TTL enforcement and eviction; cache must not grow unboundedly.

### Additional Requirements (Architecture)

- Python 3.11+ runtime; Poetry for dependency management; devbox for dev environment.
- Pydantic v2 for all data models (`Package`, `Vulnerability`, `ScanResult`).
- Layered architecture: CLI → Core → Adapters → Persistence; no Docker SDK or K8s client in core layer.
- `PackageExtractor` protocol — `can_handle(rootfs)` + `extract(rootfs)` — registered in `core/sbom.py`.
- `CVESource` protocol — `name` + `query(packages)` — registered in `core/scanner.py`.
- Docker adapter uses `image.save()` stream only; `docker.containers.*` APIs never used.
- Cache key format: `{ecosystem}:{name}:{version}`; SQLite at `~/.cache/docklens/cache.db`.
- Settings via `pydantic-settings` + `tomli`; env vars override with prefix `DOCKLENS_`.
- CPE lookup table bundled at `cve/data/cpe_lookup.json`; unmatchable packages flagged `cpe_unknown`.
- httpx for all HTTP calls (async-capable); pytest-httpx for integration test mocking.
- Temp directories via `tempfile.TemporaryDirectory`; cleaned on exit and SIGINT.

### UX Design Requirements

N/A — terminal/CLI product; no separate UX spec. Rich rendering requirements captured in FR-20 and FR-21.

---

### FR Coverage Map

FR-1 → Epic 1 — CLI entry point and help text
FR-2 → Epic 1 — Interactive TUI menu
FR-3 → Epic 1 — `docklens scan` command skeleton
FR-4 → Epic 2 — Validate and pull image
FR-5 → Epic 2 — Export image filesystem
FR-6 → Epic 2 — Dockerfile support
FR-7 → Epic 2 — Distro detection
FR-8 → Epic 2 — System package extraction
FR-9 → Epic 2 — Language package extraction
FR-10 → Epic 3 — CPE mapping
FR-11 → Epic 3 — OSV API query
FR-12 → Epic 3 — NVD API query
FR-13 → Epic 6 — EUVD API query
FR-14 → Epic 3 — Local CVE cache
FR-15 → Epic 4 — Per-CVE severity ranking
FR-16 → Epic 4 — Image Risk Score
FR-17 → Epic 4 — Exit-on-critical
FR-18 → Epic 4 — Patched version suggestion
FR-19 → Epic 4 — Fix advisory links
FR-20 → Epic 5 — Rich terminal table
FR-21 → Epic 5 — Summary header panel
FR-22 → Epic 5 — JSON export
FR-23 → Epic 5 — SBOM export
FR-24 → Post-MVP — K8s image enumeration
FR-25 → Post-MVP — K8s RBAC
FR-26 → Post-MVP — K8s off/in-cluster
FR-27 → Epic 1 — User config file
FR-28 → Epic 7 — POST /scan endpoint
FR-29 → Epic 7 — API server command
FR-30 → Epic 5 — GitHub Actions CI workflow

---

## Epic List

### Epic 1: Working CLI Foundation
Users can invoke `docklens`, navigate an interactive TUI menu, and run `docklens scan` with a meaningful (if stub) response. Config file is loaded on startup.
**FRs covered:** FR-1, FR-2, FR-3, FR-27
**GitHub issues:** #4

### Epic 2: Docker Image Inspection & SBOM
Users can point Docklens at a local Docker image and get a complete software inventory (SBOM) — distro, system packages, language packages — without running the container.
**FRs covered:** FR-4, FR-5, FR-6, FR-7, FR-8, FR-9
**GitHub issues:** #5, #6, #7, #8

### Epic 3: Vulnerability Detection Pipeline
Users can see which CVEs affect the packages in their image. Results are cached locally to avoid repeated API calls.
**FRs covered:** FR-10, FR-11, FR-12, FR-14
**GitHub issues:** #9, #10, #11

### Epic 4: Risk Assessment & Remediation
Users understand the severity of each CVE, see a composite image Risk Score, know which version fixes each vulnerability, and get direct advisory links.
**FRs covered:** FR-15, FR-16, FR-17, FR-18, FR-19
**GitHub issues:** #12, #13, #19

### Epic 5: Output, Reporting & CI Integration
Users see polished Rich terminal output, can export JSON/SBOM, and CI pipelines automatically fail when critical CVEs are detected.
**FRs covered:** FR-20, FR-21, FR-22, FR-23, FR-30
**GitHub issues:** #14, #2

### Epic 6: EUVD Vulnerability Source
Users get European vulnerability coverage (EUVD) supplementing NVD/OSV results.
**FRs covered:** FR-13
**GitHub issues:** #18

### Epic 7: REST API
Tool integrators can scan images programmatically via a local REST API.
**FRs covered:** FR-28, FR-29
**GitHub issues:** #22

### Epic 8: Documentation & Support
Users can understand the tool, its threat model, and get help when stuck.
**GitHub issues:** #15, #28, #3

---

## Epic 1: Working CLI Foundation

Users can invoke `docklens`, navigate the TUI menu, run `docklens scan <image>` (stub output), and have their config file loaded on startup.

### Story 1.1: CLI Entry Point, TUI Menu, and Scan Command Skeleton

*GitHub issue: #4*

As a developer,
I want a working `docklens` CLI with an interactive TUI and a `scan` subcommand,
So that I have a solid entry point to build all scanning features on top of.

**Acceptance Criteria:**

**Given** the package is installed via `pip install -e .` or `poetry install`
**When** the user runs `docklens --help`
**Then** the output lists the `scan` subcommand with its flags, and exits with code 0.

**Given** the user runs `docklens` with no arguments
**When** InquirerPy loads
**Then** a menu appears with options: Scan local image / Scan Kubernetes cluster / View cached results / Quit.

**Given** the user selects Quit from the TUI menu
**When** the selection is confirmed
**Then** the process exits with code 0 without error.

**Given** the user runs `docklens scan ubuntu:22.04`
**When** the scan command is invoked
**Then** the CLI prints a placeholder "Scan not yet implemented" message and exits 0 (stub — will be filled in Epic 2).

**Given** `~/.config/docklens/config.toml` exists with `cache_ttl_hours = 48`
**When** Docklens starts
**Then** `Settings.cache_ttl_hours` equals 48 without any CLI flag.

**Given** no config file exists
**When** Docklens starts
**Then** defaults are used (`cache_ttl_hours = 24`, `exit_on_critical = false`) without error.

---

## Epic 2: Docker Image Inspection & SBOM

Users can point Docklens at a local Docker image and receive a complete software inventory without running the container.

### Story 2.1: Validate and Pull Docker Image

*GitHub issue: #5*

As a developer,
I want Docklens to verify that a Docker image exists locally (and optionally pull it),
So that I get a clear error when I mistype an image name and a smooth experience when I want to pull first.

**Acceptance Criteria:**

**Given** the user runs `docklens scan myapp:1.0.0` and the image exists locally
**When** validation runs
**Then** no error is raised and the scan proceeds.

**Given** the user runs `docklens scan nonexistent:tag` without `--pull`
**When** validation runs
**Then** a user-friendly error "Image 'nonexistent:tag' not found locally. Use --pull to fetch it." is printed and the process exits non-zero.

**Given** the user runs `docklens scan ubuntu:22.04 --pull` and the image is not local
**When** validation runs
**Then** `docker pull ubuntu:22.04` is triggered, and on success the scan proceeds.

**Given** `--pull` is used and the pull fails (e.g. network error)
**When** the pull fails
**Then** a clear error message is shown and the process exits non-zero.

---

### Story 2.2: Extract Docker Image Filesystem

*GitHub issue: #6*

As a developer,
I want Docklens to export a Docker image's filesystem to a temporary directory using the Docker SDK,
So that package extractors can read it without any container ever being started.

**Acceptance Criteria:**

**Given** a valid local Docker image
**When** the filesystem export runs
**Then** a `tempfile.TemporaryDirectory` is created containing the merged layer rootfs.

**Given** the export completes or the user sends SIGINT
**When** the scan ends
**Then** the temporary directory is deleted and no orphan directories remain.

**Given** the Docker daemon is not running
**When** the export is attempted
**Then** a clear error "Docker daemon not reachable" is printed and the process exits non-zero.

**And** at no point is `docker.containers` API called or a container created.

---

### Story 2.3: Detect Linux Distribution Inside Image

*GitHub issue: #7*

As a developer,
I want Docklens to read the Linux distro and version from an extracted rootfs,
So that the correct package extractor is selected downstream.

**Acceptance Criteria:**

**Given** a Debian/Ubuntu rootfs with `/etc/os-release`
**When** distro detection runs
**Then** returns `{"distro": "ubuntu", "version": "22.04"}` (or equivalent Debian variant).

**Given** an Alpine rootfs with `/etc/alpine-release`
**When** distro detection runs
**Then** returns `{"distro": "alpine", "version": "3.18"}`.

**Given** an RHEL/CentOS rootfs with `/etc/redhat-release`
**When** distro detection runs
**Then** returns `{"distro": "rhel", "version": "8"}`.

**Given** a distroless or scratch image with none of the expected files
**When** distro detection runs
**Then** returns `{"distro": "unknown", "version": null}` without raising an exception.

---

### Story 2.4: Extract Installed System and Language Packages

*GitHub issue: #8*

As a developer,
I want Docklens to extract all installed packages (system + language) from a rootfs,
So that I have a complete SBOM to feed into the CVE lookup.

**Acceptance Criteria:**

**Given** a Debian/Ubuntu rootfs with `/var/lib/dpkg/status`
**When** the dpkg extractor runs
**Then** returns a list of `Package(name, version, ecosystem="deb")` records matching the installed packages.

**Given** an Alpine rootfs with `/lib/apk/db/installed`
**When** the apk extractor runs
**Then** returns `Package` records with `ecosystem="apk"`.

**Given** an RHEL rootfs with `/var/lib/rpm/Packages`
**When** the rpm extractor runs
**Then** returns `Package` records with `ecosystem="rpm"`.

**Given** a Python image with `site-packages/*.dist-info/METADATA`
**When** the pip extractor runs
**Then** returns `Package` records with `ecosystem="pypi"`.

**Given** a Node image with `node_modules/*/package.json`
**When** the npm extractor runs
**Then** returns `Package` records with `ecosystem="npm"`.

**Given** a distroless image with no recognisable package database
**When** all extractors run
**Then** all return empty lists without raising exceptions.

---

## Epic 3: Vulnerability Detection Pipeline

Users can see which CVEs affect the packages in their image, with results cached locally.

### Story 3.1: Set Up Local CVE Data Storage

*GitHub issue: #9*

As a developer,
I want a local SQLite cache for CVE query results managed by SQLAlchemy and Alembic,
So that repeated scans of the same packages don't hit external APIs unnecessarily.

**Acceptance Criteria:**

**Given** first run on a clean machine
**When** Docklens initialises the cache
**Then** `~/.cache/docklens/cache.db` is created with the correct schema (table: `cached_vulnerabilities`).

**Given** the DB already exists with an older schema version
**When** Docklens starts
**Then** Alembic applies pending migrations automatically without data loss.

**Given** a package key `pypi:requests:2.28.0` is stored in cache with `expires_at` in the future
**When** the same package is queried
**Then** the cached payload is returned and no HTTP request is made.

**Given** a cached entry whose `expires_at` is in the past
**When** the package is queried
**Then** the cache entry is ignored and a fresh API call is made.

**Given** `--no-cache` flag is set
**When** any package is queried
**Then** cache is bypassed for both reads and writes.

**Given** the cache DB file is corrupted
**When** Docklens starts
**Then** a WARNING is logged, cache is disabled for the session, and the scan continues without crashing.

---

### Story 3.2: Map Installed Packages to CPE Identifiers

*GitHub issue: #10*

As a developer,
I want each SBOM package to be enriched with a CPE identifier,
So that NVD CPE-based queries can be performed accurately.

**Acceptance Criteria:**

**Given** a package `{name: "openssl", version: "1.1.1f", ecosystem: "deb"}`
**When** CPE mapping runs
**Then** the package's `cpe` field is set to `cpe:2.3:a:openssl:openssl:1.1.1f:*:*:*:*:*:*:*`.

**Given** a package not in the lookup table
**When** CPE mapping runs
**Then** the heuristic `cpe:2.3:a:{name}:{name}:{version}:*:*:*:*:*:*:*` is applied.

**Given** a package for which no CPE can be reliably constructed
**When** CPE mapping runs
**Then** `cpe = None` is set; the package is still included in the SBOM; OSV query still runs.

**Given** the lookup table file `cve/data/cpe_lookup.json` is absent
**When** CPE mapping runs
**Then** all packages fall through to heuristic; no exception is raised.

---

### Story 3.3: Retrieve CVEs Associated with Packages (OSV + NVD)

*GitHub issue: #11*

As a developer,
I want Docklens to query OSV and NVD for each SBOM package and return a deduplicated list of CVEs,
So that I know which vulnerabilities are present in the image.

**Acceptance Criteria:**

**Given** a package `{ecosystem: "pypi", name: "requests", version: "2.27.0"}` with a known CVE
**When** the OSV source queries `https://api.osv.dev/v1/query`
**Then** the corresponding `Vulnerability` record is returned with id, description, cvss_score, severity.

**Given** a package with a CPE and a known NVD CVE
**When** the NVD source queries the v2 API
**Then** the `Vulnerability` record is returned and merged with OSV results; duplicate CVE IDs are deduplicated.

**Given** `NVD_API_KEY` is not set
**When** NVD is queried
**Then** queries proceed at the unauthenticated rate limit; a WARNING is logged once per session.

**Given** the OSV API returns HTTP 429
**When** the response is received
**Then** exponential backoff is applied (max 3 retries) before failing with a non-fatal warning.

**Given** any CVE source API is unreachable
**When** the query is attempted
**Then** that source's results are empty; a WARNING is logged; the scan continues with results from other sources.

**Given** packages with no known CVEs
**When** all sources are queried
**Then** an empty vulnerability list is returned; no error is raised.

---

## Epic 4: Risk Assessment & Remediation

Users understand the severity of each CVE, see a composite Risk Score, know which version fixes each vulnerability, and get direct advisory links.

### Story 4.1: Vulnerability Severity Ranking

*GitHub issue: #12*

As a developer,
I want each CVE scored and labelled by severity using CVSS with age and exposure weighting,
So that I can triage the most critical issues first.

**Acceptance Criteria:**

**Given** a CVE with CVSS v3 base score 9.8, published 200 days ago
**When** scoring runs
**Then** the adjusted score > 9.8 and severity label is "CRITICAL".

**Given** a CVE with CVSS v3 base score 7.2, published 10 days ago
**When** scoring runs
**Then** severity label is "HIGH".

**Given** a CVE with only CVSS v2 score available
**When** scoring runs
**Then** the v2 score is used as fallback and severity is correctly labelled.

**Given** a CVE with no CVSS score
**When** scoring runs
**Then** severity label is "UNKNOWN" and the CVE is still included in results.

**Given** a scan result
**When** the vulnerability list is returned
**Then** it is sorted by adjusted score descending (CRITICAL first).

---

### Story 4.2: Image Risk Score Computation

*GitHub issue: #12 (sub-task) / linked to #13*

As a developer,
I want a single composite 0–100 Risk Score for the scanned image,
So that I can compare images and gate deployments at a glance.

**Acceptance Criteria:**

**Given** an image with zero CVEs
**When** the risk score is computed
**Then** the score is exactly 0.

**Given** an image with one CVSS 10.0 CVE
**When** the risk score is computed
**Then** the score is ≥ 90.

**Given** an image with only LOW severity CVEs
**When** the risk score is computed
**Then** the score is < 20.

**Given** `--exit-on-critical` is set and at least one CRITICAL CVE is found
**When** the scan completes
**Then** the process exits with code 1.

**Given** `--exit-on-critical` is set and no CRITICAL CVEs are found
**When** the scan completes
**Then** the process exits with code 0.

---

### Story 4.3: Patch & Fix Recommendation Engine

*GitHub issue: #13*

As a developer,
I want each CVE to show the fixed version and a direct advisory link,
So that I know exactly what to upgrade and where to read more.

**Acceptance Criteria:**

**Given** a CVE record that includes a `fixed_in` version
**When** results are assembled
**Then** `Vulnerability.fixed_version` is populated with that version string.

**Given** a CVE with no known fix
**When** results are assembled
**Then** `Vulnerability.fixed_version` is `None`; displayed as "No fix available".

**Given** a CVE sourced from OSV
**When** the advisory URL is built
**Then** `Vulnerability.advisory_url` points to `https://osv.dev/vulnerability/{id}`.

**Given** a CVE sourced from NVD
**When** the advisory URL is built
**Then** `Vulnerability.advisory_url` points to `https://nvd.nist.gov/vuln/detail/{id}`.

---

### Story 4.4: Remediation Fix Links in Output

*GitHub issue: #19*

As a developer,
I want fix advisory links rendered as clickable hyperlinks (or plain URLs) in the terminal output,
So that I can navigate directly to the fix from my terminal.

**Acceptance Criteria:**

**Given** a terminal that supports OSC-8 escape sequences (e.g. iTerm2, GNOME Terminal)
**When** the CVE table is rendered
**Then** the advisory URL column shows a clickable hyperlink labelled with the CVE ID.

**Given** a terminal that does not support OSC-8 (e.g. basic CI log output)
**When** the CVE table is rendered
**Then** the plain URL string is printed in the Link column.

**Given** a CVE with `advisory_url = None`
**When** the table is rendered
**Then** the Link cell shows "—" (dash) instead of crashing.

---

## Epic 5: Output, Reporting & CI Integration

Users see polished Rich terminal output, can export JSON/SBOM, and CI pipelines fail automatically when critical CVEs are found.

### Story 5.1: Rich Terminal Output & Reporting

*GitHub issue: #14*

As a developer,
I want Docklens to display scan results as a Rich summary panel and sortable CVE table,
So that I can immediately understand the security posture of my image.

**Acceptance Criteria:**

**Given** a completed scan with CVEs
**When** results are rendered in Rich mode
**Then** a summary panel shows: image name, Risk Score, total CVEs (C/H/M/L), scan duration, timestamp.

**Given** a completed scan
**When** the CVE table is rendered
**Then** columns are: CVE ID, Package, Installed Version, Fixed Version, CVSS, Severity, Link — with severity colour-coded (red=CRITICAL, orange=HIGH, yellow=MEDIUM, default=LOW).

**Given** an 80-column terminal
**When** the table is rendered
**Then** no line wrapping occurs.

**Given** a scan with zero CVEs
**When** results are rendered
**Then** the summary panel shows Risk Score = 0 and a "" message; no empty table is shown.

**Given** `--output json` flag
**When** the scan completes
**Then** valid JSON is printed to stdout matching the `ScanResult` Pydantic schema.

**Given** `--output json --output-file results.json`
**When** the scan completes
**Then** the JSON is written to `results.json` and nothing is printed to stdout.

**Given** `--sbom` flag
**When** the scan completes
**Then** a CycloneDX v1.4 JSON file is written to `sbom.json` (or `--output-file` path).

---

### Story 5.2: GitHub Actions CI Workflow

*GitHub issue: #2*

As a DevOps engineer,
I want a GitHub Actions workflow that scans the project's Docker image on every PR and fails the build on critical CVEs,
So that vulnerabilities are caught before code reaches main.

**Acceptance Criteria:**

**Given** a PR is opened or updated
**When** the GitHub Actions workflow runs
**Then** `docklens scan` is executed against the built image.

**Given** the scanned image contains a CRITICAL CVE
**When** the workflow runs with `--exit-on-critical`
**Then** the workflow job exits non-zero and the PR check shows as failed.

**Given** the scanned image has no CRITICAL CVEs
**When** the workflow runs
**Then** the workflow job exits 0 and the PR check passes.

**Given** Docklens is not installed in the runner
**When** the workflow runs
**Then** a `pip install` or `poetry install` step installs it before scanning.

---

## Epic 6: EUVD Vulnerability Source

Users get European vulnerability (EUVD) data supplementing NVD/OSV results.

### Story 6.1: Add EUVD Vulnerability Source Support

*GitHub issue: #18*

As a developer,
I want Docklens to query the EUVD API for European vulnerability records,
So that I have broader coverage beyond NVD and OSV.

**Acceptance Criteria:**

**Given** a package with a known EUVD record
**When** the EUVD source queries the API
**Then** the `Vulnerability` record is returned with `source = "euvd"` and correct id, description, cvss_score.

**Given** the EUVD API is unreachable or returns a non-200 response
**When** the query is attempted
**Then** the EUVD source returns an empty list; a WARNING is logged; the scan continues normally.

**Given** a CVE ID that exists in both NVD and EUVD
**When** results are merged
**Then** only one `Vulnerability` record is kept (deduplication by CVE ID).

**Given** EUVD returns a result for a CVE not in NVD/OSV
**When** results are assembled
**Then** the EUVD-only vulnerability is included in the output.

---

## Epic 7: REST API

Tool integrators can scan images programmatically via a local REST API.

### Story 7.1: FastAPI REST API Server

*GitHub issue: #22*

As a tool integrator,
I want a local REST API server that exposes Docklens scan functionality,
So that I can trigger scans and consume results from other tools without using the CLI directly.

**Acceptance Criteria:**

**Given** the user runs `docklens serve --port 8080`
**When** the server starts
**Then** `GET http://localhost:8080/health` returns HTTP 200 with `{"status": "ok"}`.

**Given** the API server is running
**When** `POST http://localhost:8080/scan` is called with `{"image": "ubuntu:22.04"}`
**Then** the response is HTTP 200 with the same JSON payload as `docklens scan ubuntu:22.04 --output json`.

**Given** the image does not exist locally
**When** `POST /scan` is called
**Then** HTTP 404 is returned with `{"error": "Image not found"}`.

**Given** no `image` key in the request body
**When** `POST /scan` is called
**Then** HTTP 422 is returned with a validation error message.

**Given** the API server is running
**When** any valid scan completes
**Then** the response Content-Type is `application/json`.

---

## Epic 8: Documentation & Support

Users can understand the tool, its threat model, and get help when stuck.

### Story 8.1: Documentation & Threat Model

*GitHub issue: #15*

As a user and security reviewer,
I want comprehensive documentation covering installation, usage, security model, and threat model,
So that I can use Docklens confidently and understand its security boundaries.

**Acceptance Criteria:**

**Given** the project README
**When** a new user reads it
**Then** it covers: what Docklens does, installation steps, quick-start `docklens scan` example, all CLI flags, config file format, and CI integration example.

**Given** the threat model document
**When** a security reviewer reads it
**Then** it documents: what data leaves the machine (only package tuples), which APIs are called, that no containers are executed, and the CVE cache privacy model.

**Given** the documentation
**When** a developer reads it
**Then** the architecture overview and module structure (from `architecture.md`) are summarised in a `CONTRIBUTING.md` or `docs/architecture.md`.

---

### Story 8.2: Help Desk & In-Tool Help

*GitHub issue: #28*

As a user,
I want useful help text and error messages inside the tool,
So that I can resolve common issues without reading external documentation.

**Acceptance Criteria:**

**Given** the user runs `docklens --help`
**When** the output is printed
**Then** every flag includes a one-line description of its effect.

**Given** the user runs `docklens scan --help`
**When** the output is printed
**Then** usage examples are shown (e.g. `docklens scan ubuntu:22.04 --exit-on-critical`).

**Given** an unexpected error occurs during a scan
**When** the error is caught
**Then** a user-friendly message is printed (no raw Python traceback unless `--verbose`); the `--verbose` flag prints the full traceback.

**Given** `NVD_API_KEY` is not set
**When** a scan begins
**Then** a one-time notice "NVD API key not set — rate-limited to X req/min. Set DOCKLENS_NVD_API_KEY for better performance." is logged at INFO level.

---

### Story 8.3: Project Recap & Status Summary

*GitHub issue: #3*

As a project contributor,
I want a concise project status document summarising what has been built, what remains, and any known limitations,
So that anyone joining the project can quickly understand its current state.

**Acceptance Criteria:**

**Given** the recap document exists in `docs/`
**When** a new contributor reads it
**Then** it lists: completed features, backlog items, known limitations, and the technology decisions from `architecture.md`.

**Given** the recap document
**When** it is read after a milestone
**Then** it reflects the current state of the codebase (updated as part of each epic's completion).
