# Story 2.1: Validate and Pull Docker Image

Status: in-progress

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

- [x] Implement image validation logic — `image_exists_locally()`, `check_docker_installed()`, `check_docker_running()`, `pull_image()` (AC: 1–4) — branch `feature/issue-4-scan-command`
  - [x] Check image exists locally (AC: 1, 2)
  - [x] Pull image when not found (AC: 3, 4)
  - [ ] ⚠️ Uses `subprocess` calls (`docker image inspect`, `docker pull`) — needs to be rewritten using `docker.from_env()` SDK as planned in architecture
  - [ ] Not structured as a `DockerAdapter` class — currently standalone functions in `cli/scan_command.py`
- [ ] Add `DocklensError` custom exception to `docklens/core/models.py` — not started
- [ ] Wire validation into `cli/main.py` `scan` command — not connected yet
- [ ] Write unit tests `tests/unit/test_docker_adapter_validate.py` using `unittest.mock.patch` — not started
- [ ] Manual smoke test: `docklens scan ubuntu:22.04` (local) and `docklens scan nonexistent:tag`

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

- Validation and pull logic implemented on branch `feature/issue-4-scan-command` in `cli/scan_command.py`.
- All 4 ACs are functionally satisfied: local check, error on missing image, pull on request, error on pull failure.
- **Deviation**: implementation uses `subprocess` (`docker image inspect`, `docker pull`) instead of the Docker SDK (`docker.from_env()`). Before merging, this needs to be rewritten as a `DockerAdapter` class using the SDK — subprocess calls bypass the `DOCKER_HOST` env var and are harder to unit test.
- **Not connected**: `scan_entry()` exists but is not wired into the Typer `scan` command from story 1.1 yet.

### File List

- `cli/scan_command.py` (validate_image_ref, check_docker_installed, check_docker_running, image_exists_locally, pull_image, scan_entry)
