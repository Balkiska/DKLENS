# Story 2.2: Extract Docker Image Filesystem

Status: ready-for-dev

## Story

As a developer,
I want Docklens to export a Docker image's filesystem to a temporary directory using the Docker SDK,
so that package extractors can read it without any container ever being started.

## Acceptance Criteria

1. A valid local Docker image is exported to a `tempfile.TemporaryDirectory` containing the merged layer rootfs.
2. The temp directory is deleted on scan completion or SIGINT — no orphan directories remain.
3. Docker daemon not running → "Docker daemon not reachable" error and non-zero exit.
4. `docker.containers.*` API is never called; no container is created.

## Tasks / Subtasks

- [ ] Add `export_filesystem(image: docker.models.images.Image) -> ContextManager[Path]` to `DockerAdapter` (AC: 1, 2, 4)
  - [ ] Use `image.save()` to stream the image tarball
  - [ ] Write stream to `tempfile.TemporaryDirectory`
  - [ ] Extract tarball layers with `tarfile` stdlib; merge layers in order (later layers override earlier)
  - [ ] Return a context manager (`contextlib.contextmanager`) that yields the rootfs `Path` and cleans up on exit
- [ ] Handle `docker.errors.DockerException` (daemon not running) → raise `DocklensError` (AC: 3)
- [ ] Register SIGINT handler in `cli/main.py` to ensure temp dir cleanup on Ctrl+C (AC: 2)
- [ ] Write integration test `tests/integration/test_docker_adapter.py` against a minimal scratch image fixture (AC: 1, 2)
  - [ ] Fixture: a tiny pre-built tar in `tests/fixtures/images/minimal.tar`
- [ ] Verify no containers appear in `docker ps -a` after a scan

## Dev Notes

- **Layer merging**: Docker image tarballs contain a `manifest.json` listing layer tarballs in order. Extract each layer tar over the previous, so later layers (which delete or override files via `.wh.` whiteout markers) win. Handle `.wh.` whiteout files: if a layer contains `.wh.{filename}`, delete `{filename}` from the merged rootfs.
- **Whiteout files**: `tarfile` extraction does not handle Docker whiteouts automatically. After extracting each layer, post-process to apply whiteouts.
- **Context manager pattern**: use `@contextlib.contextmanager` + `try/finally` to guarantee cleanup even on exception.
- **Stream memory**: `image.save()` returns a generator of bytes chunks. Write to a temp file first, then open with `tarfile.open(mode="r")`. Avoid loading the whole image into RAM.
- **No subprocess**: do not call `docker save` via subprocess — use the SDK's `image.save()` only.

### Project Structure Notes

- `export_filesystem` is a method on `DockerAdapter` in `docklens/adapters/docker_adapter.py`.
- Test fixtures go in `tests/fixtures/images/` as pre-built minimal tarballs.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#6. Docker Adapter]
- [Source: _bmad-output/planning-artifacts/prd.md#4.2 Docker Image Inspection — FR-5]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
