# Story 2.4: Extract Installed System and Language Packages

Status: ready-for-dev

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

- [ ] Implement `docklens/extractors/base.py` — `PackageExtractor` Protocol (AC: all)
  - [ ] `can_handle(rootfs: Path) -> bool`
  - [ ] `extract(rootfs: Path) -> list[Package]`
- [ ] Implement `docklens/extractors/dpkg.py` — Debian dpkg parser (AC: 1)
  - [ ] Parse `/var/lib/dpkg/status` stanza format (blank-line separated records)
  - [ ] Extract `Package:` and `Version:` fields
- [ ] Implement `docklens/extractors/apk.py` — Alpine apk parser (AC: 2)
  - [ ] Parse `/lib/apk/db/installed` format (key:value lines, blank-line separated)
  - [ ] `P:` = name, `V:` = version
- [ ] Implement `docklens/extractors/rpm.py` — RPM DB reader (AC: 3)
  - [ ] Use `rpm` Python bindings if available; fallback to parsing `/var/lib/rpm/` with `rpmfile` or subprocess `rpm --dbpath`
  - [ ] [ASSUMPTION: rpm bindings or `rpmfile` library available as optional dep]
- [ ] Implement `docklens/extractors/pip.py` — pip METADATA reader (AC: 4)
  - [ ] `glob(rootfs / "**" / "*.dist-info" / "METADATA")` — read `Name:` and `Version:` headers
- [ ] Implement `docklens/extractors/npm.py` — npm package.json reader (AC: 5)
  - [ ] `glob(rootfs / "**/node_modules/*/package.json")` — parse `name` and `version` fields
- [ ] Implement `docklens/core/sbom.py` — `SBOMExtractor` that runs all registered extractors (AC: 6)
  - [ ] Registered list: `[DpkgExtractor(), ApkExtractor(), RpmExtractor(), PipExtractor(), NpmExtractor()]`
  - [ ] Calls `can_handle()` on each; collects results; returns combined `list[Package]`
- [ ] Write unit tests `tests/unit/test_extractors.py` using `tmp_path` fake rootfs fixtures (AC: 1–6)

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

### File List
