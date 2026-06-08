# Story 4.3: Patch & Fix Recommendation Engine

Status: ready-for-dev

## Story

As a developer,
I want each CVE to show the fixed version and a direct advisory link,
so that I know exactly what to upgrade and where to read more.

## Acceptance Criteria

1. CVE record with a `fixed_in` version → `Vulnerability.fixed_version` populated.
2. CVE with no known fix → `fixed_version = None`; displayed as "No fix available".
3. CVE from OSV → `advisory_url = "https://osv.dev/vulnerability/{id}"`.
4. CVE from NVD → `advisory_url = "https://nvd.nist.gov/vuln/detail/{id}"`.

## Tasks / Subtasks

- [ ] Update `docklens/cve/osv.py` — extract `fixed_version` from OSV response (AC: 1, 2, 3)
  - [ ] OSV response `affected[].ranges[].events` contains `{fixed: "version"}` entries — extract the first `fixed` value
  - [ ] Set `advisory_url = f"https://osv.dev/vulnerability/{vuln_id}"`
- [ ] Update `docklens/cve/nvd.py` — extract `fixed_version` from NVD response (AC: 1, 2, 4)
  - [ ] NVD `cve.configurations[].nodes[].cpeMatch[].versionEndExcluding` is the fix version — extract if present
  - [ ] Set `advisory_url = f"https://nvd.nist.gov/vuln/detail/{cve_id}"`
- [ ] Update integration tests `tests/integration/test_cve_sources.py` — verify `fixed_version` and `advisory_url` are populated from recorded fixtures (AC: 1–4)

## Dev Notes

- **OSV fix version**: OSV structures vulnerabilities with `affected[].ranges[]`. Each range has `events: [{introduced: "..."}, {fixed: "..."}]`. Take the last `fixed` event value. If no `fixed` event exists, `fixed_version = None`.
- **NVD fix version**: NVD uses `versionEndExcluding` (exclusive) or `versionEndIncluding` (inclusive) in CPE match criteria. `versionEndExcluding` is more common and means the fix is that version. Extract from the first matching node.
- **Both sources for same CVE**: if NVD and OSV both have a fix version, prefer NVD's (more precise versioning format for system packages). Keep `model_copy(update={...})` pattern.
- **advisory_url fallback**: if EUVD also has the CVE (Epic 6), its URL will be `https://euvd.enisa.europa.eu/...` — handled in Story 6.1. This story covers OSV and NVD only.

### Project Structure Notes

- These changes are additive updates to existing `osv.py` and `nvd.py` — no new files.

### References

- [Source: _bmad-output/planning-artifacts/prd.md#4.6 Remediation & Fix Links — FR-18]
- [Source: _bmad-output/planning-artifacts/architecture.md#5. CVE Source Protocol]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
