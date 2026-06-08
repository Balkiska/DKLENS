# Story 4.2: Image Risk Score Computation

Status: ready-for-dev

## Story

As a developer,
I want a single composite 0–100 Risk Score for the scanned image,
so that I can compare images and gate deployments at a glance.

## Acceptance Criteria

1. Image with zero CVEs → Risk Score exactly 0.
2. Image with one CVSS 10.0 CVE → Risk Score ≥ 90.
3. Image with only LOW severity CVEs → Risk Score < 20.
4. `--exit-on-critical` set + CRITICAL CVE found → exit code 1.
5. `--exit-on-critical` set + no CRITICAL CVEs → exit code 0.

## Tasks / Subtasks

- [ ] Add `compute_risk_score(vulns: list[Vulnerability]) -> float` to `docklens/core/scoring.py` (AC: 1–3)
  - [ ] `risk = min(100.0, sum(adjusted_score * weight for vuln in vulns))`
  - [ ] Weights: CRITICAL → 10, HIGH → 4, MEDIUM → 1, LOW → 0.2, UNKNOWN → 1
  - [ ] Use `vuln.adjusted_score or vuln.cvss_score or 0.0` as the base for weight multiplication
- [ ] Populate `ScanResult.risk_score` and `ScanResult.summary` in `core/scanner.py` (AC: 1–3)
  - [ ] `summary = {"CRITICAL": count, "HIGH": count, "MEDIUM": count, "LOW": count, "UNKNOWN": count}`
- [ ] Implement `--exit-on-critical` logic in `cli/main.py` (AC: 4, 5)
  - [ ] After scan: if `exit_on_critical and result.summary["CRITICAL"] > 0` → `raise typer.Exit(1)`
  - [ ] Also honour `settings.exit_on_critical` from config file
- [ ] Write unit tests `tests/unit/test_scoring.py` — add cases for risk score formula (AC: 1–3)

## Dev Notes

- **Weight rationale**: weights are calibrated so one CRITICAL (CVSS 10, adjusted ~12) × 10 = 120, clamped to 100. One LOW (CVSS 1, adjusted ~1) × 0.2 = 0.2 — many LOWs are needed to hit 20.
- **`ScanResult.risk_score`**: round to one decimal place: `round(risk, 1)`.
- **`ScanResult.summary`**: computed after scoring; all severity keys always present (value 0 if no CVEs of that level).
- **Exit code**: `raise typer.Exit(code=1)` in Typer exits cleanly without printing a traceback.

### Project Structure Notes

- `compute_risk_score` is a pure function in `docklens/core/scoring.py` — no I/O, no side effects.
- `Scanner.scan()` calls `score_vulnerabilities()` (Story 4.1) then `compute_risk_score()` to populate `ScanResult`.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#10. Scoring Logic]
- [Source: _bmad-output/planning-artifacts/prd.md#4.5 Scoring & Prioritisation — FR-16, FR-17]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
