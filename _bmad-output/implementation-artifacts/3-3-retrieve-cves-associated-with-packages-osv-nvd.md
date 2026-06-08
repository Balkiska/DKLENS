# Story 3.3: Retrieve CVEs Associated with Packages (OSV + NVD)

Status: ready-for-dev

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

- [ ] Implement `docklens/cve/base.py` — `CVESource` Protocol (AC: all)
  - [ ] `name: str`; `query(packages: list[Package]) -> list[Vulnerability]`
- [ ] Implement `docklens/cve/osv.py` — `OSVSource` (AC: 1, 4, 5, 6, 7)
  - [ ] POST `https://api.osv.dev/v1/querybatch` with `{"queries": [{"package": {"name": name, "ecosystem": ecosystem}, "version": version}]}`
  - [ ] Map response to `Vulnerability` list; set `source = "osv"`
  - [ ] Exponential backoff on 429: `[1, 2, 4]` seconds, max 3 retries
  - [ ] On failure after retries: log WARNING, return `[]`
- [ ] Implement `docklens/cve/nvd.py` — `NVDSource` (AC: 2, 3, 5, 6, 7)
  - [ ] GET `https://services.nvd.nist.gov/rest/json/cves/2.0?cpeName={cpe}&resultsPerPage=100`
  - [ ] Add `apiKey` query param if `settings.nvd_api_key` is set
  - [ ] Skip packages where `cpe is None`
  - [ ] Map CVSSv3 (preferred) or CVSSv2 (fallback) to `cvss_score` and `cvss_version`
  - [ ] On 429 or failure: log WARNING, return `[]`
- [ ] Implement `docklens/core/scanner.py` — `Scanner.query_vulnerabilities(packages)` (AC: 2, 7)
  - [ ] Registered sources: `[OSVSource(), NVDSource()]`
  - [ ] For each package, check cache first; on miss call sources; write results to cache
  - [ ] Deduplicate by CVE ID: keep the record with non-null `cvss_score` preferentially
- [ ] Write integration tests `tests/integration/test_cve_sources.py` using `pytest-httpx` with recorded responses (AC: 1, 2, 4, 5)
  - [ ] Fixture files in `tests/fixtures/cve_responses/osv_requests.json`, `tests/fixtures/cve_responses/nvd_openssl.json`

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

### Completion Notes List

### File List
