# Story 2.4: Extract Installed System and Language Packages

Status: in-progress

## Story

As a developer,
I want Docklens to extract all installed packages (system + language) from a rootfs,
so that I have a complete SBOM to feed into the CVE lookup pipeline.

## Acceptance Criteria

1. Debian/Ubuntu rootfs `/var/lib/dpkg/status` → list of `Package(name, version, ecosystem="deb")`.
2. Alpine rootfs `/lib/apk/db/installed` → `Package` records with `ecosystem="apk"`.
3. RHEL rootfs `/var/lib/rpm/Packages` → `Package` records with `ecosystem="rpm"`.
4. Python image `site-packages/*.dist-info/METADATA` → `Package` records with `ecosystem="pypi"`.
5. Node image `node_modules/*/package.json` → `Package` records with `ecosystem="npm"`.
6. Distroless / no package database → all extractors return empty lists without exception.

## Tasks / Subtasks

- [x] Implement `parse_dpkg_packages(fs_path)` — Debian/Ubuntu dpkg parser (AC: 1) — branch `feat/scanner`
  - [x] Parses `/var/lib/dpkg/status`, extracts `Package:` and `Version:` fields
  - [x] Returns list of dicts `{name, version, ecosystem: "Debian"}`
  - [ ] ⚠️ Returns plain dicts, not `Package` model objects — needs conversion when `core/models.py` is created
- [x] Implement `parse_apk_packages(fs_path)` — Alpine apk parser (AC: 2) — branch `feat/scanner`
  - [x] Parses `/lib/apk/db/installed`, extracts `P:` (name) and `V:` (version) fields
  - [x] Returns list of dicts `{name, version, ecosystem: "Alpine"}`
- [x] Implement `extract_packages(fs_path)` — auto-selects parser based on `detect_distro()` (AC: 6 partial)
  - [x] Returns empty list for unknown distro without exception (AC: 6)
- [ ] Implement RPM parser (AC: 3) — not started
- [ ] Implement pip extractor (AC: 4) — not started
- [ ] Implement npm extractor (AC: 5) — not started
- [ ] Implement `PackageExtractor` Protocol and `SBOMExtractor` orchestrator — not started
- [ ] Write pytest unit tests with `tmp_path` fake rootfs — only manual script `tests/test_packages.py`

## Dev Notes

- **Glob depth**: `glob("**/*.dist-info/METADATA", recursive=True)` can be slow on large images. Set a reasonable depth limit or use `rglob` with a max-depth guard.
- **dpkg stanza parser**: split file on `\n\n` to get records; split each record on `\n` to get fields; take `field.split(": ", 1)` for key/value. This is more reliable than regex on multi-line fields.
- **apk parser**: records are separated by blank lines. Fields start with a single uppercase letter followed by `:`. Only `P:` (name) and `V:` (version) are needed.
- **rpm**: prefer `rpmfile` library (pure Python) over invoking `rpm` subprocess. If neither is available, return empty list with a DEBUG log — do not fail.
- **Package model**: `cpe` field is `None` at this stage — it gets populated in Epic 3 Story 3.2.
- **No deduplication here**: the SBOM extractor returns all packages including potential duplicates across ecosystems. Deduplication (if needed) is the caller's responsibility.

### Project Structure Notes

- Each extractor is a class in its own file under `docklens/extractors/`.
- `SBOMExtractor` in `docklens/core/sbom.py` owns the registered list — no dynamic plugin discovery.
- `Package` model is in `docklens/core/models.py` (established in Story 1.1).

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#4. Extractor Protocol]
- [Source: _bmad-output/planning-artifacts/prd.md#4.3 SBOM Extraction — FR-8, FR-9]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- dpkg (Debian) and apk (Alpine) parsers implemented on `feat/scanner` in `scanner/packages.py`.
- Both parsers return plain dicts — will need to be wrapped in `Package` model objects once `core/models.py` is created in Story 1.1.
- **Remaining before done**: RPM, pip, npm extractors; `PackageExtractor` protocol; `SBOMExtractor` orchestrator; proper pytest tests.

### File List

- `scanner/packages.py` (detect_distro, parse_apk_packages, parse_dpkg_packages, extract_packages)
- `tests/test_packages.py` (manual smoke test script)
