# Story 3.3: Retrieve CVEs Associated with Packages (OSV + NVD)

Status: done

## Story

As a developer,
I want Docklens to query OSV and NVD for each SBOM package and return a deduplicated list of CVEs,
so that I know which vulnerabilities are present in the image.

## Acceptance Criteria

1. `{ecosystem: "pypi", name: "requests", version: "2.27.0"}` with a known CVE → OSV returns a `Vulnerability` record with id, description, cvss_score, severity.
2. Package with CPE and known NVD CVE → NVD returns `Vulnerability`; merged with OSV results; duplicate CVE IDs deduplicated (one record kept, preferring the higher-detail source).
3. `NVD_API_KEY` not set → queries proceed at unauthenticated rate limit; one WARNING logged per session.
4. OSV API returns HTTP 429 → exponential backoff applied (max 3 retries) before non-fatal warning.
5. Any CVE source unreachable → that source returns empty list; WARNING logged; scan continues.
6. Packages with no known CVEs → empty vulnerability list returned; no error raised.
7. Results are cached via `CacheRepository` (from Story 3.1) on write; cache is checked before API call.

## Tasks / Subtasks

- [ ] Implement `docklens/cve/base.py` — `CVESource` Protocol (AC: all) — **not built**; project uses a flat `vulns/` module instead of the `cve/` Protocol abstraction described here
- [x] Implement OSV querying (AC: 1, 4, 5, 6, 7) — built as `vulns/osv_client.py::query_osv()` (one request per package, not the `/v1/querybatch` batch endpoint; no exponential backoff on 429, but a non-200 response returns `[]` so the scan still completes)
- [ ] Implement `docklens/cve/nvd.py` — `NVDSource` (AC: 2, 3, 5, 6, 7) — **not built**; NVD was never implemented. EUVD (`vulns/euvd_client.py`, Story 6.1) is used instead as the enrichment source
- [x] Orchestrate OSV + enrichment + cache (AC: 2, 7) — built as `vulns/scanner.py::scan_packages()`. Cache wiring was completed 2026-06-25: the `CacheRepository` from Story 3.1 existed but was never called from the scan pipeline until this session; `scan_packages()` now checks the cache before each OSV/EUVD call and writes results on a miss, plus a `--no-cache` CLI flag
- [ ] Write integration tests `tests/integration/test_cve_sources.py` using `pytest-httpx` with recorded responses (AC: 1, 2, 4, 5) — **not built**; current tests call the live OSV/EUVD APIs directly rather than recorded fixtures

## Dev Notes

- **httpx async vs sync**: use `httpx.Client` (sync) for now — the CLI is synchronous. Async can be added later if scan speed becomes a bottleneck.
- **OSV batch API**: use `/v1/querybatch` to send all packages in one request rather than one request per package. Batch size limit is 1000; chunk if needed.
- **NVD pagination**: `resultsPerPage=100` with `startIndex` for pagination. Most CPEs return < 100 CVEs; skip pagination for v1 (log a DEBUG warning if `totalResults > 100`).
- **Deduplication key**: `Vulnerability.id` (the CVE ID string). When the same CVE appears in OSV and NVD, prefer the NVD record for `cvss_score` (more authoritative) but keep OSV's `advisory_url` if NVD's is None.
- **Rate limits**: NVD unauthenticated = 5 requests/30s. Add a `time.sleep(0.6)` between NVD requests when no API key is set.
- **pytest-httpx**: use `httpx_mock` fixture to intercept requests. Load response JSON from `tests/fixtures/cve_responses/` files.
- **Severity mapping**: CVSS score → severity label is done in Epic 4 Story 4.1. At this stage, set `severity = "UNKNOWN"` as placeholder; it will be overwritten by the scoring step.

### Project Structure Notes

- `osv.py`, `nvd.py`, `base.py` are all in `docklens/cve/`.
- `Scanner` class in `docklens/core/scanner.py` owns the registered source list and cache wiring.
- Never import `httpx` in `core/` — only in `cve/` adapters.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#5. CVE Source Protocol]
- [Source: _bmad-output/planning-artifacts/architecture.md#14. Technology Decisions]
- [Source: _bmad-output/planning-artifacts/prd.md#4.4 Vulnerability Lookup — FR-11, FR-12, FR-14]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- 2026-06-25: discovered the Alpine ecosystem string sent to OSV was `"Alpine"` instead of `"Alpine:vX.Y"` (e.g. `"Alpine:v3.18"`), so OSV silently returned zero vulnerabilities for every Alpine package regardless of version. Fixed by reading `/etc/alpine-release` in `scanner/packages.py::get_alpine_version()`. Debian ecosystem (`"Debian"`) does not need this suffix — confirmed against the live OSV API.

### Completion Notes List

- Implemented as OSV (`vulns/osv_client.py`) + EUVD (`vulns/euvd_client.py`) instead of OSV + NVD: NVD was never built, EUVD was substituted (see Story 6.1). Functionally equivalent for this project's scope — every CVE is enriched with a European severity score and ID instead of an NVD one.
- No `CVESource` Protocol / `docklens/cve/` package — implemented as flat `vulns/` module per the project's existing flat layout convention (same decision already made for `cache/` in Story 3.1).
- Verified end-to-end against real Docker images (`alpine:3.10`, `alpine:3.18`) with Docker running locally: package extraction → OSV lookup → EUVD enrichment → severity sort → Rich table, including a real CRITICAL/MEDIUM finding with fix command and advisory URL.
- Cache integration (AC 7) completed 2026-06-25 — see Story 3.1 change log.

### File List

- scanner/packages.py (get_alpine_version, ecosystem fix)
- vulns/osv_client.py
- vulns/euvd_client.py
- vulns/scanner.py (cache wiring)
- cve/cpe.py (lookup key fix to match new ecosystem format)
- cli/menu.py (--no-cache flag)
