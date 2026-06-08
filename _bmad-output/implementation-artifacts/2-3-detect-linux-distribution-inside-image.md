# Story 2.3: Detect Linux Distribution Inside Image

Status: ready-for-dev

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

- [ ] Create `docklens/extractors/distro.py` — `detect_distro(rootfs: Path) -> dict` (AC: 1–4)
  - [ ] Try `/etc/os-release` first: parse `ID=` and `VERSION_ID=` fields
  - [ ] Fallback `/etc/debian_version` → distro `"debian"`
  - [ ] Fallback `/etc/alpine-release` → distro `"alpine"`, version = file content stripped
  - [ ] Fallback `/etc/redhat-release` → distro `"rhel"`, parse version with regex
  - [ ] All files missing → return `{"distro": "unknown", "version": None}`
- [ ] Write unit tests `tests/unit/test_distro.py` with minimal fake rootfs directories for each distro (AC: 1–4)
  - [ ] Use `tmp_path` pytest fixture to create fake `/etc/os-release` files

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

### File List
