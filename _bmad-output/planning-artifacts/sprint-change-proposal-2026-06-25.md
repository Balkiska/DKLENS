# Sprint Change Proposal — 2026-06-25

## 1. Issue Summary

The local vulnerability cache (`cache/`, Story 3.1) was implemented and unit-tested
in an earlier session but was never wired into the real scan pipeline
(`vulns/scanner.py` did not import `CacheRepository`). Separately, a bug in
`scanner/packages.py` sent the wrong OSV ecosystem string for Alpine packages
(`"Alpine"` instead of `"Alpine:vX.Y"`), which meant **OSV never returned a
single CVE for any Alpine image, regardless of package or version** — the
scanner ran without errors but silently found nothing.

Both issues were discovered and fixed on branch `fix/wire-cache-and-ecosystem-bug`
(commit `ea5eae8`), verified against real Docker images with Docker running
locally (`alpine:3.10`, `alpine:3.18`). A side effect, an invalid Poetry-style
`requires-python = "^3.12"` in `pyproject.toml`, was also fixed because it broke
the `ruff` pre-commit hook on every commit.

This proposal documents these changes in the bmad tracking artifacts, which had
drifted from the actual state of the code (several stories implementing
real, working functionality were still marked `ready-for-dev`).

## 2. Impact Analysis

- **Epic 3 (Vulnerability Detection Pipeline)**: Story 3.3 (retrieve CVEs) is
  functionally complete and verified — marked `done`. Epic 3 status updated
  `in-progress → done`.
- **Epic 6 (EUVD Vulnerability Source)**: Story 6.1 is functionally complete
  and verified — marked `done`. Epic 6 status updated `backlog → done`.
- **Story 3.1 (cache)**: no status change (already `done`), but its Change Log
  now reflects that the cache is actually called from the scan pipeline as of
  today, not just unit-tested in isolation.
- **Story 4.1 (severity ranking)**: no status change (already `done`), Debug
  Log now notes the Alpine bug that was silently preventing it from ever
  ranking anything on Alpine images.
- **Architecture drift (not changed in this proposal)**: Stories 3.3 and 6.1
  describe an OSV+NVD CVE pipeline behind a `CVESource` Protocol in
  `docklens/cve/`. The real implementation uses OSV+EUVD (no NVD client exists)
  in a flat `vulns/` module. This substitution is now explicitly documented in
  both story files' task lists and completion notes, without rewriting the
  architecture doc or claiming the original NVD-based scope was delivered.
- **No PRD or architecture document changes** — this is a documentation sync,
  not a scope or design change.
- **No code changes** as part of this proposal (code was already fixed and
  committed beforehand on the same branch).

## 3. Recommended Approach

**Direct Adjustment**: update story statuses and add completion notes to
match the verified, working state of the code. No rollback, no MVP scope
change. Effort: documentation only, already applied. Risk: none — purely
descriptive.

## 4. Detailed Change Proposals

### `sprint-status.yaml`
```
epic-3: in-progress → done
3-3-retrieve-cves-associated-with-packages-osv-nvd: ready-for-dev → done

epic-6: backlog → done
6-1-add-euvd-vulnerability-source-support: ready-for-dev → done
```
Rationale: both stories' core functionality is implemented and verified
end-to-end against real Docker images.

### Story 3.3 (`3-3-retrieve-cves-associated-with-packages-osv-nvd.md`)
- `Status: ready-for-dev → done`
- Task checklist updated: OSV querying and orchestration checked off (built as
  `vulns/osv_client.py` + `vulns/scanner.py`); NVD-specific and
  Protocol-abstraction tasks left unchecked with an explicit "not built" note,
  since EUVD was substituted for NVD project-wide.
- Debug Log: documents the Alpine ecosystem bug and fix.
- Completion Notes + File List added.

### Story 6.1 (`6-1-add-euvd-vulnerability-source-support.md`)
- `Status: ready-for-dev → done`
- Task checklist updated the same way: EUVD querying checked off as built
  (against the real `euvdservices.enisa.europa.eu/api/search` endpoint, which
  differs from the guessed endpoint in the original Dev Notes); Protocol/
  dedup-against-NVD tasks marked not applicable since there is no NVD source.
- Completion Notes + File List added.

### Story 3.1 (`3-1-set-up-local-cve-data-storage.md`)
- Change Log entry added: cache wired into the scan pipeline 2026-06-25,
  with measured before/after scan times (≈7.5s cold, ≈0.65s warm).

### Story 4.1 (`4-1-vulnerability-severity-ranking.md`)
- Debug Log entry added: notes the Alpine ecosystem bug that prevented
  severity ranking from ever firing on Alpine images, now fixed.

## 5. Implementation Handoff

**Scope: Minor.** This was a documentation-only correction; the underlying
code fix was already implemented, tested, and committed
(`fix/wire-cache-and-ecosystem-bug`, commit `ea5eae8`). No further handoff
required — Epics 3 and 6 are closed. Epics 4 and 5 remain `in-progress`/
`backlog` as their non-implemented stories (composite risk score, OSC-8
hyperlinks, Rich summary panel, JSON-to-file/SBOM export) are genuinely not
built and were left untouched.
