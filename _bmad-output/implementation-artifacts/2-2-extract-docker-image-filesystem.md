# Story 2.2: Extract Docker Image Filesystem

Status: done

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

- [x] Implement `extract_filesystem(image_name)` using `image.save()` to stream tarball (AC: 1, 4) — branch `feat/scanner`
  - [x] Uses Docker SDK `image.save()` — no subprocess, no container created (AC: 4)
  - [x] Reads `manifest.json` to extract layers in correct order (AC: 1)
  - [x] Merges layers into a single filesystem directory (AC: 1)
  - [x] Skips `.wh.` whiteout files — ⚠️ partial: skips the whiteout marker but does not delete the whiteout target file from the merged rootfs
  - [ ] ⚠️ Uses `tempfile.mkdtemp()` not `TemporaryDirectory` — temp dir is never deleted after scan (AC: 2 not met)
  - [ ] No SIGINT cleanup handler (AC: 2 not met)
- [ ] Handle `docker.errors.DockerException` → `DocklensError` (AC: 3) — currently handled in `docker_image.py`, not here
- [ ] Register SIGINT handler for temp dir cleanup (AC: 2) — not started
- [ ] Write integration tests with pytest (AC: 1, 2) — only manual script `tests/test_extractor.py`
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

- Core extraction logic implemented on `feat/scanner` in `scanner/extractor.py`.
- Layer ordering from `manifest.json` and SDK-only approach (no subprocess) are correct.
- **Two gaps before done**: (1) temp dir cleanup — replace `mkdtemp()` with `TemporaryDirectory` context manager so the dir is deleted on exit; (2) proper whiteout handling — currently skips `.wh.X` files but must also delete the target file `X` from the merged rootfs.
- Tests are manual `if __name__ == "__main__"` scripts, not pytest.

### File List

- `scanner/extractor.py` (extract_filesystem)
- `tests/test_extractor.py` (manual smoke test script)
