---
title: Docklens — Docker & Kubernetes Security Scanner
status: final
created: 2026-06-08
updated: 2026-06-08
---

# PRD: Docklens — Docker & Kubernetes Security Scanner

## 0. Document Purpose

This PRD defines the requirements for Docklens, a DevSecOps CLI/TUI tool that scans Docker images and Kubernetes workloads for known vulnerabilities without running containers. It is written for the developer (bkf), to serve as the single source of truth for all downstream artefacts: architecture, epics, and implementation stories. The document uses a Glossary-anchored vocabulary (§3); FRs are numbered globally; assumptions are tagged inline and indexed in §9.

---

## 1. Vision

Docklens gives developers and security engineers a single terminal command to know whether a Docker image is safe to deploy. It inspects images statically — pulling their layer filesystems, reading installed package databases, and cross-referencing them against global (NVD, OSV) and European (EUVD) vulnerability databases — without ever executing the image.

The output is a Rich-rendered terminal table: each detected vulnerability listed with its CVE/EUVD identifier, CVSS score, affected package, installed version, patched version (where known), and a link to the fix advisory. A composite risk score summarises the whole image.

In Mode B, the same engine extends to live Kubernetes clusters: Docklens reads the cluster's workload manifests (read-only RBAC), enumerates all referenced images, and runs the same scan pipeline — turning a single command into a cluster-wide security posture check with no container execution and no elevated privileges.

---

## 2. Target User

### 2.1 Jobs To Be Done

- **Developer (shift-left):** Confirm that a base image or application image is free of high/critical CVEs before pushing to CI or production.
- **Security engineer:** Audit images or an entire Kubernetes cluster for known vulnerabilities from the terminal, without deploying a dedicated scanning service.
- **DevOps / platform engineer:** Integrate image scanning into a CI pipeline as a step that fails the build when critical CVEs are present.
- **Student / learner:** Understand what vulnerabilities exist in common Docker images and how they are classified.

### 2.2 Non-Users (v1)

- Teams requiring a persistent SaaS dashboard with cross-team vulnerability tracking.
- Users needing Windows container support.
- Users needing runtime behavioural analysis (dynamic scanning).

### 2.3 Key User Journeys

- **UJ-1. Alex scans a local image before pushing.**
  Alex, a backend developer, has just built `myapp:1.4.2` locally. They run `docklens scan myapp:1.4.2` in the terminal. Docklens extracts the image filesystem, detects an Ubuntu base with dpkg packages plus Python pip packages, queries OSV and NVD, and within 30 seconds prints a Rich table of CVEs sorted by CVSS score descending. Alex spots a critical CVE in `libssl`, bumps the base image, rebuilds, and rescans.

- **UJ-2. Sonia audits her Kubernetes cluster.**
  Sonia, a platform engineer, runs `docklens scan --k8s` from her workstation. Docklens reads her `~/.kube/config`, enumerates all Deployments, DaemonSets, and Pods, collects the unique image list, scans each one, and prints an aggregate table grouped by namespace. Sonia exports the report to JSON for her security ticket.

- **UJ-3. CI pipeline fails on critical CVE.**
  A GitHub Actions job runs `docklens scan myapp:latest --exit-on-critical`. Docklens finds a CVSS 9.8 CVE and exits with code 1. The CI job fails and blocks the merge.

---

## 3. Glossary

- **Image** — A Docker image identified by `name:tag` or digest, stored locally or in a registry.
- **Layer** — A read-only filesystem delta that, stacked together, form an Image.
- **SBOM (Software Bill of Materials)** — The enumerated list of packages (name, version, ecosystem) present in an Image.
- **CVE** — A Common Vulnerabilities and Exposures identifier (e.g. `CVE-2024-1234`).
- **EUVD** — A European Union Vulnerability Database identifier; European counterpart to CVE.
- **CVSS** — Common Vulnerability Scoring System; a 0–10 numerical score for vulnerability severity.
- **CPE (Common Platform Enumeration)** — A structured naming scheme for software; used to match packages to CVE records.
- **Risk Score** — Docklens-computed composite score for an Image, derived from CVSS scores, exposure, and vulnerability age.
- **Mode A** — Local scan mode: target is an Image present on the local Docker daemon.
- **Mode B** — Kubernetes scan mode: target images are discovered from a live cluster's workloads.
- **Workload** — A Kubernetes resource that references Images (Pod, Deployment, DaemonSet, StatefulSet, Job, CronJob).
- **Cache** — Local SQLite database that stores CVE query results to avoid redundant API calls.

---

## 4. Features

### 4.1 CLI Entry Point

**Description:** Docklens is invoked as `docklens` from the terminal. The CLI is built with Typer and offers an interactive TUI flow (InquirerPy menus) when called without arguments, and a fully scriptable non-interactive mode when arguments are supplied. Realises UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-1: CLI entry point and help
The user can run `docklens --help` and see all commands, flags, and examples. The binary is installed via Poetry/pip.

**Consequences (testable):**
- `docklens --help` exits 0 and prints command list.
- `docklens scan --help` prints all scan flags.

#### FR-2: Interactive TUI mode
When `docklens` is run without subcommands, InquirerPy presents a menu: scan local image / scan Kubernetes cluster / view cached results / quit. Realises UJ-1, UJ-2.

**Consequences (testable):**
- Running `docklens` (no args) opens an interactive prompt.
- All menu paths reach a scan or exit without error.

#### FR-3: Non-interactive scan command
`docklens scan <image>` runs a full scan and prints results to stdout without prompts. Realises UJ-1, UJ-3.

**Consequences (testable):**
- `docklens scan ubuntu:22.04` completes and prints a results table.
- Exit code 0 on success, 1 on critical CVE when `--exit-on-critical` is set.

---

### 4.2 Docker Image Inspection (Mode A)

**Description:** Docklens pulls or inspects an Image from the local Docker daemon, exports its filesystem as a tarball, and reads it without executing the Image. Realises UJ-1.

**Functional Requirements:**

#### FR-4: Validate and resolve image reference
The user provides `image:tag`; Docklens verifies it exists locally (or optionally pulls it) before scanning.

**Consequences (testable):**
- Providing a non-existent image without `--pull` prints a clear error and exits non-zero.
- `--pull` flag triggers `docker pull` before inspection.

#### FR-5: Export image filesystem
Docklens exports the image layers to a temporary directory using the Docker SDK (no container execution). The temp directory is cleaned up after the scan.

**Consequences (testable):**
- No container is created or started during the scan.
- Temp directory is removed on scan completion or on SIGINT.

#### FR-6: Dockerfile support
`docklens scan --dockerfile Dockerfile` builds a temporary image from the Dockerfile, scans it, and discards the image. [ASSUMPTION: build context is the current directory.]

**Consequences (testable):**
- Providing a valid Dockerfile path triggers a build-and-scan workflow.

---

### 4.3 SBOM Extraction

**Description:** From the extracted filesystem, Docklens identifies the Linux distribution and reads its native package database plus any language-level package manifests. Realises UJ-1, UJ-2.

**Functional Requirements:**

#### FR-7: Detect Linux distribution
Docklens reads `/etc/os-release` (and fallbacks `/etc/debian_version`, `/etc/alpine-release`, `/etc/redhat-release`) to identify the distro and version.

**Consequences (testable):**
- Returns correct distro for Debian, Ubuntu, Alpine, RHEL/CentOS images.
- Returns `unknown` (not an error) for distroless or scratch images.

#### FR-8: Extract system packages
Docklens reads the native package database:
- Debian/Ubuntu: `/var/lib/dpkg/status`
- Alpine: `/lib/apk/db/installed`
- RPM-based: `/var/lib/rpm/Packages`

**Consequences (testable):**
- Returns a list of `{name, version, ecosystem}` records for each supported distro.
- Empty list (not error) for unsupported or missing package database.

#### FR-9: Extract language-level packages
Docklens reads pip (`site-packages/*.dist-info/METADATA`), npm (`node_modules/*/package.json`), and gem (`specifications/*.gemspec`) package manifests found anywhere in the filesystem. [ASSUMPTION: v1 covers pip, npm, gem only.]

**Consequences (testable):**
- Pip packages detected in a Python image.
- npm packages detected in a Node image.

---

### 4.4 Vulnerability Lookup

**Description:** Docklens maps SBOM packages to CPE identifiers, queries CVE/EUVD sources, and caches results locally. Realises UJ-1, UJ-2.

**Functional Requirements:**

#### FR-10: Map packages to CPE identifiers
Docklens constructs CPE strings (`cpe:2.3:a:{vendor}:{product}:{version}:*:*:*:*:*:*:*`) from package names and versions using heuristics and a lookup table.

**Consequences (testable):**
- Common packages (openssl, curl, python3) map to correct CPE strings.
- Unmatchable packages are flagged as `cpe_unknown` and still returned in SBOM.

#### FR-11: Query OSV API
Docklens queries `https://api.osv.dev/v1/query` for each package using its ecosystem and version. [ASSUMPTION: OSV is the primary source for language packages.]

**Consequences (testable):**
- Returns list of OSV vulnerability records for a known-vulnerable package.
- Handles 429 rate-limit responses with backoff.

#### FR-12: Query NVD API
Docklens queries the NVD REST API v2 (`https://services.nvd.nist.gov/rest/json/cves/2.0`) using CPE match strings. Requires `NVD_API_KEY` env var for higher rate limits.

**Consequences (testable):**
- Returns CVE records for known-vulnerable CPE.
- Works without API key at reduced rate; logs warning when key absent.

#### FR-13: Query EUVD API
Docklens queries the EUVD endpoint (`https://euvd.enisa.europa.eu/api`) for European vulnerability records, supplementing NVD/OSV results.

**Consequences (testable):**
- Returns EUVD entries for packages with EU-catalogued vulnerabilities.
- Gracefully handles EUVD API downtime (returns empty, logs warning, does not abort scan).

#### FR-14: Local CVE cache
Docklens stores query results in a local SQLite database via SQLAlchemy. Cache entries expire after a configurable TTL (default 24 h). Alembic manages schema migrations.

**Consequences (testable):**
- Second scan of the same package hits cache, not the network.
- `--no-cache` flag forces fresh API queries.
- Cache TTL is configurable via `~/.config/docklens/config.toml`.

---

### 4.5 Scoring & Prioritisation

**Description:** Docklens computes a per-CVE adjusted score and a per-image Risk Score, sorting output to surface the most actionable findings first. Realises UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-15: Per-CVE severity ranking
Each CVE is ranked using its CVSS base score (v3 preferred, v2 fallback), weighted by vulnerability age (older = higher urgency) and exposure (packages installed as root = higher).

**Consequences (testable):**
- CVEs with CVSS ≥ 9.0 are labelled CRITICAL.
- CVEs with CVSS 7.0–8.9 are labelled HIGH.
- Output table is sorted by adjusted score descending.

#### FR-16: Image Risk Score
A composite 0–100 Risk Score is computed per image from the distribution and weight of detected CVEs.

**Consequences (testable):**
- An image with zero CVEs scores 0.
- An image with one CVSS 10.0 CVE scores ≥ 90.

#### FR-17: Exit-on-critical flag
`--exit-on-critical` causes Docklens to exit with code 1 if any CRITICAL CVE is found. Realises UJ-3.

**Consequences (testable):**
- `echo $?` is 1 after scanning an image with a CRITICAL CVE and `--exit-on-critical`.
- Exit code is 0 when no CRITICAL CVEs are found.

---

### 4.6 Remediation & Fix Links

**Description:** For each CVE, Docklens surfaces the patched version (where available) and a direct link to the fix advisory. Realises UJ-1.

**Functional Requirements:**

#### FR-18: Patched version suggestion
Where the CVE record includes a fixed version, Docklens displays it in the results table alongside the installed version.

**Consequences (testable):**
- Results table shows "Fix: upgrade to X.Y.Z" for CVEs with known fixes.
- "No fix available" displayed when no patched version is recorded.

#### FR-19: Fix advisory links
Each CVE row includes a hyperlink (OSC-8 terminal escape or plain URL fallback) to the CVE page on cve.org and/or the OSV advisory page.

**Consequences (testable):**
- Clicking the link in a supporting terminal opens the correct advisory.
- Plain URL is printed in non-supporting terminals.

---

### 4.7 Terminal Output & Reporting

**Description:** Results are rendered with Rich: a summary header (image name, risk score, scan duration, total CVEs by severity), then a scrollable table of CVEs. JSON and plain-text export are supported for CI integration. Realises UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-20: Rich terminal table
Results are displayed in a Rich table with columns: CVE ID, Package, Installed Version, Fixed Version, CVSS, Severity, Fix Link.

**Consequences (testable):**
- Table renders without line-wrapping on an 80-column terminal.
- Severity column is colour-coded: red=CRITICAL, orange=HIGH, yellow=MEDIUM, grey=LOW.

#### FR-21: Summary header
A Rich Panel above the table shows: image name, total CVEs (Critical / High / Medium / Low), Risk Score, scan timestamp, scan duration.

**Consequences (testable):**
- Header fields are present and non-empty for every scan.

#### FR-22: JSON export
`--output json` prints machine-readable JSON to stdout (or to a file with `--output-file`).

**Consequences (testable):**
- Output is valid JSON parseable with `jq`.
- JSON schema includes all table fields plus full CVE description.

#### FR-23: SBOM export
`--sbom` writes the extracted SBOM to a file in CycloneDX JSON format. [ASSUMPTION: CycloneDX v1.4.]

**Consequences (testable):**
- Output file is valid CycloneDX JSON.

---

### 4.8 Kubernetes Mode (Mode B)

**Description:** `docklens scan --k8s` discovers all images referenced by workloads in the target cluster and runs Mode A scan against each unique image. Realises UJ-2.

**Functional Requirements:**

#### FR-24: Cluster image enumeration
Docklens uses the `kubernetes` Python client to list images from Pods, Deployments, DaemonSets, StatefulSets, Jobs, CronJobs across all namespaces (or a specified namespace with `--namespace`).

**Consequences (testable):**
- Returns a deduplicated image list from a multi-workload cluster.
- `--namespace kube-system` limits enumeration to that namespace.

#### FR-25: RBAC requirements
Docklens requires only `get`/`list` on pods, deployments, daemonsets, statefulsets, jobs, cronjobs. No write permissions.

**Consequences (testable):**
- Scan completes with a ServiceAccount that has read-only RBAC.
- No cluster state is modified.

#### FR-26: Off-cluster and in-cluster support
Off-cluster: reads `~/.kube/config` (or `KUBECONFIG` env). In-cluster: uses mounted ServiceAccount token automatically.

**Consequences (testable):**
- Scan works from a developer workstation with kubeconfig.
- Scan works from a Pod running inside the cluster.

---

### 4.9 Configuration

**Description:** User preferences are stored in `~/.config/docklens/config.toml`, read with `tomli` and validated with Pydantic. Realises UJ-1, UJ-2.

**Functional Requirements:**

#### FR-27: User config file
Docklens reads `~/.config/docklens/config.toml` on startup. Supported keys: `cache_ttl_hours`, `nvd_api_key`, `default_output_format`, `exit_on_critical`.

**Consequences (testable):**
- Setting `exit_on_critical = true` in config has the same effect as `--exit-on-critical`.
- Missing config file is not an error; defaults are used.

---

### 4.10 REST API (Optional / Post-MVP)

**Description:** A thin FastAPI wrapper exposes the scan engine as a local REST API for integration with other tools. [ASSUMPTION: v1 API is unauthenticated, local-only.]

**Functional Requirements:**

#### FR-28: POST /scan endpoint
`POST /scan` accepts `{"image": "name:tag"}` and returns the same JSON payload as `--output json`.

**Consequences (testable):**
- `curl -X POST localhost:8080/scan -d '{"image":"ubuntu:22.04"}'` returns valid JSON scan result.

#### FR-29: API server command
`docklens serve --port 8080` starts the API server.

**Consequences (testable):**
- Server starts and responds to health check at `GET /health`.

---

### 4.11 CI Integration (GitHub Actions)

**Description:** A GitHub Actions workflow runs Docklens on each pull request and fails the build when critical CVEs are found. Realises UJ-3.

**Functional Requirements:**

#### FR-30: CI scan workflow
A reusable `.github/workflows/scan.yml` runs `docklens scan` with `--exit-on-critical` on the PR's Docker image.

**Consequences (testable):**
- PR with a CRITICAL CVE image fails the CI check.
- PR with a clean image passes.

---

## 5. Non-Goals (Explicit)

- **Runtime / dynamic scanning** — Docklens does not execute images or monitor container behaviour.
- **Registry scanning without local pull** — v1 requires the image to be present locally or explicitly pulled.
- **Windows containers** — only Linux-based images are supported in v1.
- **Custom CVE databases** — v1 supports OSV, NVD, EUVD only; no plugin API for private databases.
- **SaaS / multi-tenant dashboard** — Docklens is a local CLI tool; no remote backend or persistent cloud state.
- **Automated remediation** — Docklens identifies and suggests fixes; it does not apply them.
- **SBOM signing / attestation** — CycloneDX export only; no Sigstore/cosign integration in v1.

---

## 6. MVP Scope

### 6.1 In Scope (Mode A — Local, MVP)

- CLI entry point (`docklens scan <image>`) with Rich output
- Interactive TUI mode
- Docker image extraction (no container execution)
- Distro detection (Debian/Ubuntu, Alpine, RHEL)
- System package SBOM (dpkg, apk, rpm)
- Language package SBOM (pip, npm)
- OSV + NVD CVE lookup with local SQLite cache
- Per-CVE CVSS scoring and severity labelling
- Image Risk Score
- Fix version and advisory link display
- JSON export
- `--exit-on-critical` for CI use
- Configuration via `~/.config/docklens/config.toml`
- GitHub Actions workflow

### 6.2 Out of Scope for MVP

- Kubernetes mode (Mode B) — deferred to v2 [NOTE FOR PM: high-value, schedule after Mode A is stable]
- EUVD source — deferred to v2 (API still maturing)
- REST API — deferred to v2
- Gem / Go module / Rust crate SBOM — deferred to v2
- CycloneDX SBOM export — deferred to v2
- Dockerfile build-and-scan — deferred to v2

---

## 7. Success Metrics

**Primary**
- **SM-1:** Scan completes for a standard Ubuntu 22.04 image in under 30 seconds on a modern laptop (first scan, no cache). Validates FR-5, FR-8, FR-11, FR-12.
- **SM-2:** Zero false-negative rate for CVEs present in the OSV database for packages in the test image set. Validates FR-11, FR-15.

**Secondary**
- **SM-3:** Cache hit rate ≥ 80% for repeated scans of the same image within the TTL window. Validates FR-14.
- **SM-4:** `--exit-on-critical` correctly fails CI in 100% of test cases with known-critical images. Validates FR-17, FR-30.

**Counter-metrics (do not optimise)**
- **SM-C1:** Do not optimise scan speed at the cost of false negatives — completeness over speed.
- **SM-C2:** Do not grow cache size unboundedly — enforce TTL and eviction.

---

## 8. Open Questions

1. Should `docklens scan` pull images not present locally by default (with a `--no-pull` flag to disable), or require explicit `--pull`? [Affects FR-4 UX.]
2. What is the acceptable cache database location on non-Linux OSes if the tool is later ported?
3. Should the Risk Score formula be configurable (e.g. weight CVSS v3 vs v2 differently)?
4. EUVD API stability: what is the fallback if the EUVD endpoint is down or changes its schema?
5. Should Mode B (Kubernetes) also support scanning images directly from a registry (without local pull)?

---

## 9. Assumptions Index

- **§4.2 FR-6** — Dockerfile build context is the current working directory.
- **§4.3 FR-9** — v1 covers pip, npm, and gem language ecosystems only.
- **§4.10 FR-28** — v1 REST API is unauthenticated and listens on localhost only.
- **§6.1** — Mode A MVP scope; Mode B and EUVD deferred to v2.
- **General** — Python 3.11+ runtime; Poetry for dependency management; devbox for dev environment.

---

## Cross-Cutting NFRs

- **Performance:** Scan of a standard image (≤ 500 MB) completes in under 60 seconds including API calls (no cache).
- **Security:** No image content is transmitted to third parties; only package name/version tuples are sent to CVE APIs.
- **Reliability:** API failures (NVD, OSV, EUVD) are non-fatal; scan completes with a warning and partial results.
- **Portability:** Runs on Linux and macOS; Docker daemon must be accessible.
- **Observability:** `--verbose` flag enables debug logging to stderr; structured logs use Python `logging` module.

## Language / Runtime Targets

- Python 3.11+
- Poetry for dependency management
- Devbox for reproducible dev environment
- Pre-commit hooks for code quality (already configured)
