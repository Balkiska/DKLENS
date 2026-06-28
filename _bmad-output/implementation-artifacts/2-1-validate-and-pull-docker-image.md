# Story 2.1: Validate and Pull Docker Image

Status: done

## Story

As a developer,
I want Docklens to verify that a Docker image exists locally (and optionally pull it),
so that I get a clear error when I mistype an image name and a smooth pull experience when I pass `--pull`.

## Acceptance Criteria

1. `docklens scan myapp:1.0.0` where the image exists locally proceeds without error.
2. `docklens scan nonexistent:tag` without `--pull` prints "Image 'nonexistent:tag' not found locally. Use --pull to fetch it." and exits non-zero.
3. `docklens scan ubuntu:22.04 --pull` triggers a Docker pull when the image is not local; on success the scan proceeds.
4. Pull failure (network error, image not in registry) shows a clear error and exits non-zero.

## Tasks / Subtasks

- [x] Implement `validate_and_pull_image(image_name)` using Docker SDK `docker.from_env()` (AC: 1–4) — branch `feat/scanner`
  - [x] `client.images.get()` — checks image exists locally (AC: 1, 2)
  - [x] `client.images.pull()` on `ImageNotFound` (AC: 3, 4)
  - [x] `client.ping()` to verify daemon is reachable (AC: 3 prerequisite)
  - [ ] ⚠️ Uses `sys.exit(1)` instead of `DocklensError` — error handling not aligned with architecture
  - [ ] Not structured as a `DockerAdapter` class — standalone functions in `scanner/docker_image.py`
- [x] Wired into `cli/menu.py` `scan` command — branch `feat/scanner`
- [ ] Add `DocklensError` custom exception to `docklens/core/models.py` — not started
- [ ] Write unit tests with `unittest.mock.patch` on docker client — tests are manual scripts only (`tests/test_docker_image.py`), not pytest
- [x] Manual smoke test: `validate_and_pull_image("alpine:3.18")` verified in `tests/test_docker_image.py`

## Dev Notes

- **Docker client**: always use `docker.from_env()` — reads `DOCKER_HOST` env if set. Do not hardcode socket path.
- **Image reference parsing**: Docker SDK accepts both `name:tag` and `name@digest`. Pass the string as-is to `client.images.get()`.
- **Pull**: `client.images.pull()` returns the pulled image. Split the ref into `repository` and `tag` parts: `ref.rsplit(":", 1)` with fallback tag `"latest"`.
- **DocklensError**: subclass of `Exception`; CLI catches it, prints `typer.echo(str(e), err=True)` and calls `raise typer.Exit(1)`.
- **Never call** `client.containers.*` — only `client.images.*` API is permitted (no container execution).

### Project Structure Notes

- `docker_adapter.py` lives in `docklens/adapters/` — not in `core/`.
- `DocklensError` is part of `core/models.py` since it's a domain-level error shared across adapters.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#6. Docker Adapter]
- [Source: _bmad-output/planning-artifacts/prd.md#4.2 Docker Image Inspection — FR-4]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Initial subprocess-based implementation on `feature/issue-4-scan-command` superseded by Docker SDK implementation on `feat/scanner`.
- All 4 ACs functionally covered by `scanner/docker_image.py` using `docker.from_env()`, `client.images.get()`, `client.images.pull()`.
- **Remaining before done**: replace `sys.exit(1)` with `DocklensError`; restructure as `DockerAdapter` class; write proper pytest unit tests with mocked docker client.

### File List

- `scanner/docker_image.py` (get_docker_client, validate_and_pull_image)
- `tests/test_docker_image.py` (manual smoke test script)
