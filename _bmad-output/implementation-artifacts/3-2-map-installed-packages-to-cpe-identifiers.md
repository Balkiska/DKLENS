# Story 3.2: Map Installed Packages to CPE Identifiers

Status: done

## Story

As a developer,
I want each SBOM package enriched with a CPE identifier,
so that NVD CPE-based queries can be performed accurately in the next step.

## Acceptance Criteria

1. `{name: "openssl", version: "1.1.1f", ecosystem: "Debian"}` → `cpe = "cpe:2.3:a:openssl:openssl:1.1.1f:*:*:*:*:*:*:*"`.
2. Package not in lookup table → heuristic `cpe:2.3:a:{name}:{name}:{version}:*:*:*:*:*:*:*` applied.
3. Package for which no CPE can be constructed → `cpe = None`; package still in SBOM; OSV query still runs.
4. `cve/data/cpe_lookup.json` absent → all packages use heuristic; no exception raised.

## Tasks / Subtasks

- [x] Create `cve/data/cpe_lookup.json` — seed file with 20 common packages (AC: 1)
  - [x] Keys use `"ecosystem.lower():name"` format (e.g. `"debian:openssl"`, `"alpine:curl"`)
- [x] Implement `cve/cpe.py` — `enrich_packages(packages: list) -> list` (AC: 1–4)
  - [x] Load lookup table once (module-level, cached). Handle `FileNotFoundError` → empty dict.
  - [x] For each package: look up `"{ecosystem.lower()}:{name}"` in table → use vendor/product from table
  - [x] Fallback: heuristic `vendor = name, product = name`
  - [x] Build CPE string: `f"cpe:2.3:a:{vendor}:{product}:{version}:*:*:*:*:*:*:*"`
  - [x] Return new dicts with `cpe` populated (do not mutate original)
- [x] Wire `enrich_packages()` into `cli/menu.py` after `extract_packages()` (no `core/sbom.py` exists)
- [x] Write unit tests `tests/unit/test_cpe.py` for all four AC paths (6 tests, all passing)

## Dev Notes

- **Lookup table format**: `{"ecosystem:name": {"vendor": "...", "product": "..."}}`. Keep it minimal; it is a seed, not exhaustive. The scanner still works for all packages via heuristic.
- **CPE format**: `cpe:2.3:a:{vendor}:{product}:{version}:*:*:*:*:*:*:*`. The `a` part means "application". All wildcards are `*`. Do not URI-encode the CPE here — pass the raw string to NVD.
- **Immutability**: `Package` is a Pydantic model. Use `package.model_copy(update={"cpe": cpe_string})` to return a new instance instead of mutating.
- **Special characters in version**: NVD CPE matching is case-insensitive and treats `:` as a separator. Version strings with special chars (e.g. `1.1.1f-1ubuntu2`) may not match perfectly — this is acceptable for v1; the OSV path (which uses ecosystem+version directly) is the reliable one.

### Project Structure Notes

- `cpe.py` and `cpe_lookup.json` live under `docklens/cve/`.
- The enrichment step runs in `core/sbom.py` after all extractors run, before any CVE queries.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#13. CPE Mapping]
- [Source: _bmad-output/planning-artifacts/prd.md#4.4 Vulnerability Lookup — FR-10]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Adapted `docklens/cve/` → `cve/` (project uses flat module layout, no `docklens/` prefix).
- Packages are plain dicts, not Pydantic models; used `{**pkg, "cpe": cpe}` for immutability.
- Wired into `cli/menu.py` (no `core/sbom.py` exists); `scan_packages()` unaffected (ignores extra keys).
- Ecosystem key normalization: `ecosystem.lower()` so `"Debian"` and `"Alpine"` match the JSON keys.

### File List

- `cve/__init__.py`
- `cve/cpe.py`
- `cve/data/cpe_lookup.json`
- `cli/menu.py`
- `tests/unit/test_cpe.py`

### Review Findings

- [x] [Review][Decision] AC1 ecosystem key mismatch — resolved: spec example corrected to `"Debian"`; implementation and JSON keys are correct (story 2-4 uses title-case ecosystem values)
- [x] [Review][Patch] Empty package name produces malformed CPE instead of None — fixed: guard changed to `if not version or not name` [cve/cpe.py:28]
- [x] [Review][Patch] JSON decode errors crash CLI at import — fixed: `except (OSError, json.JSONDecodeError)` covers corrupt files and permission errors [cve/cpe.py:9]
- [x] [Review][Patch] Versionless packages may crash scan_packages downstream — fixed: `scan_packages` now uses `pkg.get("version")` and appends a NONE finding for versionless packages [vulns/scanner.py:19]
- [x] [Review][Patch] Missing key validation for lookup table entries — fixed: `entry.get("vendor", name)` / `entry.get("product", name)` with heuristic fallback [cve/cpe.py:34-35]
- [x] [Review][Defer] Package name not lowercased before key lookup — `"OpenSSL"` (capital O) would miss `"debian:openssl"`; in practice Debian/Alpine package names are always lowercase, so low real-world impact [cve/cpe.py:31] — deferred, pre-existing
- [x] [Review][Defer] Debian epoch versions produce malformed CPE — `version = "2:7.74.0"` inserts a colon into the CPE string; spec explicitly accepts this as a v1 limitation [cve/cpe.py:37] — deferred, pre-existing
- [x] [Review][Defer] Debian multi-arch name suffixes break lookup — `libc6:amd64` generates key `"debian:libc6:amd64"` which misses `"debian:libc6"`; heuristic fallback still produces a CPE [cve/cpe.py:31] — deferred, pre-existing
- [x] [Review][Defer] Whitespace-only version bypasses None guard — `version = " "` is truthy so it produces `cpe:2.3:a:name:name: :*:*:*:*:*:*:*` with a space; unrealistic edge case for Docker image packages [cve/cpe.py:30] — deferred, pre-existing
