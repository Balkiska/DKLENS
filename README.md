# DKLENS

> [!WARNING]
> This tool is intended for legitimate security testing only. Users are solely responsible for ensuring they have authorization before scanning any system or image. Any misuse is strictly prohibited.

Docker image vulnerability scanner with an interactive terminal menu, usable as a CLI, a standalone REST API, or deployed in a Kubernetes cluster.

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
| Fedora | RPM | `fedora` |
| Rocky Linux | RPM | `rockylinux/rockylinux`, `rockylinux/rockylinux:8` |
| AlmaLinux | RPM | `almalinux` |
| Red Hat UBI | RPM | `registry.access.redhat.com/ubi8/ubi`, `ubi9/ubi` |

> RPM databases come in three formats (SQLite, NDB, BerkeleyDB) depending on the distro/version. DKLENS auto-detects the format. Reading BerkeleyDB RPM databases (Rocky/UBI 8, CentOS 7) requires the `rpm` and `db-util` system packages — already included in the Devbox shell and the Docker image.

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
git clone https://github.com/Balkiska/DKLENS.git
cd DKLENS
devbox shell
```

Devbox automatically installs Python, Poetry, and all dependencies on first run.

---

## Usage

### Interactive menu (recommended)

```bash
./dklens start
```

This opens a full interactive menu:

1. Select a local Docker image with arrow keys
2. DKLENS scans it automatically
3. After the scan, choose what to do:
   - Filter by severity (CRITICAL / HIGH / MEDIUM / LOW)
   - Export as PDF
   - Export as JSON
   - Scan another image
   - Quit

---
#### Preview
<img width="1146" height="548" alt="image" src="https://github.com/user-attachments/assets/e27f4724-b6cf-4680-b25a-ecb35ea788c1" />

<img width="1325" height="820" alt="image" src="https://github.com/user-attachments/assets/500c1f58-fd90-4cb8-8867-e95a7b67be62" />

<img width="1176" height="461" alt="image" src="https://github.com/user-attachments/assets/71e8e468-9a21-442d-aab8-6144412f1b47" />

---
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

### Report formats

#### PDF report

A ready-to-share PDF report with severity breakdown, affected packages, and suggested fix versions.

```bash
poetry run python main.py scan <image> --export report.pdf
```


#### JSON report

Machine-readable output, handy for piping into other tools or CI pipelines.

```bash
poetry run python main.py scan <image> --format json
```


### REST API

DKLENS also ships a FastAPI server so other tools can trigger scans over HTTP.

```bash
devbox shell
poetry run uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Or via Docker (image also published to `ghcr.io/balkiska/dklens` on GHCR, rebuilt automatically on every version tag):

```bash
docker build -t dklens .
docker run -p 8000:8000 -v /var/run/docker.sock:/var/run/docker.sock dklens
```

> **The [Dockerfile](Dockerfile) in this repo is intentionally basic — it exists to validate that the project runs as a container, not as a hardened production image.** It runs as root (needed to access the Docker socket) and has no non-root user/GID mapping. Mounting `/var/run/docker.sock` also grants the container effective root access to the host. Before running it in production or on a shared cluster, harden it: non-root user, read-only filesystem, restricted socket access, etc.
>
> The API also serves plain **HTTP** with no authentication. That's fine for local testing, but if you expose it beyond your own machine (including inside a cluster), put a reverse proxy in front of it with **HTTPS** and authentication.

Endpoints:

| Method | Path | Description |
|---|---|---|
| GET | `/` | Basic API info |
| GET | `/health` | Health check |
| POST | `/scan` | Scan an image — body: `{"image": "<name>", "no_cache": false}` |

### Kubernetes

Since it's a plain container image exposing an HTTP API, DKLENS can also run as a pod in a Kubernetes cluster, using the image already published on GHCR (`ghcr.io/balkiska/dklens:latest`) — no need to build anything yourself.

> The only hard requirement: the pod needs access to a Docker daemon (DKLENS talks to it directly via the Docker socket to pull and inspect images) — typically by mounting the node's `/var/run/docker.sock`. The same security notes above apply here too: this is a plain-HTTP, unauthenticated, root-privileged setup, so put an Ingress/reverse proxy with TLS and access control in front of it before exposing it beyond a test cluster.

Once exposed through a Service/Ingress, the REST API becomes reachable over the internet like any other web app — including its interactive Swagger docs at `/docs`, which can be opened directly from a browser to trigger scans without writing any code.

---
#### Preview
<img width="1446" height="863" alt="image" src="https://github.com/user-attachments/assets/de6e3acd-3d95-42b1-9ef8-ab7a734778f2" />

<img width="896" height="546" alt="image" src="https://github.com/user-attachments/assets/b99740fb-03da-4554-852d-c55b9d8a34e0" />

<img width="896" height="546" alt="image" src="https://github.com/user-attachments/assets/d70903f5-9109-4d42-8788-ecb23e530458" />


---

## Development

### Run the app

```bash
./dklens start
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
sqlite3 ~/.cache/dklens/cache.db "SELECT package_key, source, expires_at FROM cached_vulnerabilities;"
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
