# Story 2.3: Detect Linux Distribution Inside Image

Status: in-progress

## Story

As a developer,
I want Docklens to read the Linux distro and version from an extracted rootfs,
so that the correct package extractor is selected for the next step.

## Acceptance Criteria

1. Ubuntu/Debian rootfs with `/etc/os-release` → `{"distro": "ubuntu"|"debian", "version": "22.04"|...}`.
2. Alpine rootfs with `/etc/alpine-release` → `{"distro": "alpine", "version": "3.18"|...}`.
3. RHEL/CentOS rootfs with `/etc/redhat-release` → `{"distro": "rhel", "version": "8"|...}`.
4. Distroless/scratch image with none of the expected files → `{"distro": "unknown", "version": None}` — no exception raised.

## Tasks / Subtasks

- [x] Implement `detect_distro(fs_path)` in `scanner/packages.py` (AC: 2, 4) — branch `feat/scanner`
  - [x] Detects Alpine via `/lib/apk/db/installed` (AC: 2 — partial: no version extracted)
  - [x] Detects Debian via `/var/lib/dpkg/status` (AC: 1 — partial: no version extracted)
  - [x] Returns `"unknown"` when no known DB found (AC: 4 — partial: returns string not dict)
  - [ ] Version not extracted — returns plain string (`"alpine"`, `"debian"`, `"unknown"`) not `{"distro": ..., "version": ...}`
  - [ ] Does not read `/etc/os-release` — detection based on package DB presence only
  - [ ] RHEL/CentOS not detected (AC: 3 not met)
- [ ] Write unit tests with pytest `tmp_path` fixture — only manual script `tests/test_packages.py`

## Dev Notes

- **`/etc/os-release` format**: key=value pairs, values may be quoted. Use a simple parser: split on `=`, strip quotes. Do not use `shlex` for this; a two-line parser is sufficient.
- **ID field normalisation**: `ID=ubuntu` → `"ubuntu"`, `ID=debian` → `"debian"`. Return `ID` value lowercase.
- **No subprocess**: read files directly with `(rootfs / "etc" / "os-release").read_text(errors="replace")`.
- **Return type**: plain `dict` is fine here — do not use Pydantic for this small utility function. The caller (`scanner.py`) will use the result to select extractors.
- **Distro `"unknown"`** is a valid, non-error result — log it at DEBUG level only.

### Project Structure Notes

- `detect_distro` lives in `docklens/extractors/distro.py` (not in `core/` — it's extraction logic).
- Test fixtures are simple directory trees created with pytest `tmp_path` — no pre-built tarballs needed here.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#4. Extractor Protocol]
- [Source: _bmad-output/planning-artifacts/prd.md#4.3 SBOM Extraction — FR-7]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Detection implemented on `feat/scanner` in `scanner/packages.py` as part of `detect_distro()`.
- Alpine and Debian are detected correctly. RHEL not yet handled.
- **Gaps before done**: (1) extract and return version (read `/etc/alpine-release` for Alpine, parse `/etc/os-release` for Debian); (2) add RHEL detection via `/etc/redhat-release`; (3) return a dict `{"distro": ..., "version": ...}` instead of a plain string.

### File List

- `scanner/packages.py` (detect_distro)
