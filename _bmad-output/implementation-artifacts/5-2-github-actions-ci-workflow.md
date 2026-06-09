# Story 5.2: GitHub Actions CI Workflow

Status: ready-for-dev

## Story

As a DevOps engineer,
I want a GitHub Actions workflow that scans the project's Docker image on every PR and fails the build on critical CVEs,
so that vulnerabilities are caught before code reaches main.

## Acceptance Criteria

1. PR opened/updated → workflow runs `docklens scan` against the built image.
2. Image contains CRITICAL CVE + `--exit-on-critical` → workflow job exits non-zero; PR check fails.
3. No CRITICAL CVEs → workflow exits 0; PR check passes.
4. Docklens installed in runner before scanning (via `pip install` or `poetry install`).

## Tasks / Subtasks

- [ ] Create `.github/workflows/scan.yml` — Docker image scan on PR (AC: 1–4)
  - [ ] Trigger: `on: [pull_request]`
  - [ ] Steps: checkout → set up Python → install Poetry → `poetry install` → build Docker image → `docklens scan $IMAGE --exit-on-critical`
  - [ ] Set `IMAGE` env var from the built image tag
- [ ] Create `.github/workflows/tests.yml` — run pytest on PR (bonus, keeps CI complete)
  - [ ] Steps: checkout → set up Python → install Poetry → `poetry install` → `pytest`
- [ ] Verify workflow YAML is valid (no syntax errors) using `yamllint` or GitHub Actions validator
- [ ] Document required GitHub Actions secrets/env vars in `README.md` (e.g. `NVD_API_KEY` as optional secret)

## Dev Notes

- **Image build step**: use `docker build -t docklens-test:${{ github.sha }} .` to get a unique tag per commit. Pass this tag to `docklens scan`.
- **Python version**: pin to `3.11` in the workflow to match the project's target runtime.
- **Poetry cache**: add a `actions/cache` step for `~/.cache/pypoetry` to speed up subsequent runs.
- **NVD_API_KEY**: add as an optional secret `${{ secrets.NVD_API_KEY }}` in the env block. The scan works without it (with rate limiting); the secret just improves performance.
- **Exit code propagation**: GitHub Actions propagates the exit code of each `run:` step. `docklens scan --exit-on-critical` exiting 1 will automatically fail the step.
- **Dockerfile**: this story assumes a `Dockerfile` already exists or will be created as part of the workflow. If not yet present, add a minimal one (e.g. `FROM python:3.11-slim`) as a placeholder.

### Project Structure Notes

- Workflow files go in `.github/workflows/` — these ARE committed to the repository (not gitignored).
- `_bmad/` and `.claude/` remain gitignored per `.gitignore` setup.

### References

- [Source: _bmad-output/planning-artifacts/prd.md#4.11 CI Integration — FR-30]
- [Source: _bmad-output/planning-artifacts/prd.md#2.3 Key User Journeys — UJ-3]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
