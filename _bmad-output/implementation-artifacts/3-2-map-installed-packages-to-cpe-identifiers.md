# Story 3.2: Map Installed Packages to CPE Identifiers

Status: ready-for-dev

## Story

As a developer,
I want each SBOM package enriched with a CPE identifier,
so that NVD CPE-based queries can be performed accurately in the next step.

## Acceptance Criteria

1. `{name: "openssl", version: "1.1.1f", ecosystem: "deb"}` → `cpe = "cpe:2.3:a:openssl:openssl:1.1.1f:*:*:*:*:*:*:*"`.
2. Package not in lookup table → heuristic `cpe:2.3:a:{name}:{name}:{version}:*:*:*:*:*:*:*` applied.
3. Package for which no CPE can be constructed → `cpe = None`; package still in SBOM; OSV query still runs.
4. `cve/data/cpe_lookup.json` absent → all packages use heuristic; no exception raised.

## Tasks / Subtasks

- [ ] Create `docklens/cve/data/cpe_lookup.json` — seed file with ~20 common packages (AC: 1)
  - [ ] Entries: `{"deb:openssl": {"vendor": "openssl", "product": "openssl"}, "pypi:requests": {"vendor": "python-requests", "product": "requests"}, ...}`
- [ ] Implement `docklens/cve/cpe.py` — `enrich_packages(packages: list[Package]) -> list[Package]` (AC: 1–4)
  - [ ] Load lookup table once (module-level, cached). Handle `FileNotFoundError` → empty dict.
  - [ ] For each package: look up `"{ecosystem}:{name}"` in table → use vendor/product from table
  - [ ] Fallback: heuristic `vendor = name, product = name`
  - [ ] Build CPE string: `f"cpe:2.3:a:{vendor}:{product}:{version}:*:*:*:*:*:*:*"`
  - [ ] Return new `Package` instances with `cpe` populated (do not mutate in place)
- [ ] Wire `enrich_packages()` into `core/sbom.py` after extraction — returns enriched package list
- [ ] Write unit tests `tests/unit/test_cpe.py` for all three paths (AC: 1–4)

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

### File List
