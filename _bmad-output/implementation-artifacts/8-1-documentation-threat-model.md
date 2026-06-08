# Story 8.1: Documentation & Threat Model

Status: ready-for-dev

## Story

As a user and security reviewer,
I want comprehensive documentation covering installation, usage, security model, and threat model,
so that I can use Docklens confidently and understand its security boundaries.

## Acceptance Criteria

1. README covers: what Docklens does, installation, quick-start example, all CLI flags, config file format, CI integration example.
2. Threat model document covers: data that leaves the machine (package tuples only), APIs called, no container execution, CVE cache privacy model.
3. Architecture overview and module structure summarised in `docs/architecture.md` or `CONTRIBUTING.md`.

## Tasks / Subtasks

- [ ] Update `README.md` to be user-facing and complete (AC: 1)
  - [ ] Section: What is Docklens (2-3 sentences)
  - [ ] Section: Installation (`pip install docklens` or `poetry add docklens`)
  - [ ] Section: Quick start — `docklens scan ubuntu:22.04`
  - [ ] Section: All CLI flags with descriptions (can reference `--help` output)
  - [ ] Section: Config file (`~/.config/docklens/config.toml` with example)
  - [ ] Section: CI integration (GitHub Actions snippet)
- [ ] Create `docs/threat-model.md` (AC: 2)
  - [ ] What data leaves the machine: only `{name, version, ecosystem}` tuples to OSV/NVD/EUVD
  - [ ] What APIs are called and their data usage
  - [ ] No container execution guarantee: no `docker.containers.*` API used
  - [ ] Cache: stored locally at `~/.cache/docklens/cache.db`; not uploaded anywhere
  - [ ] Credentials: `NVD_API_KEY` never logged; only sent as query param over HTTPS
- [ ] Create `docs/architecture.md` — summary of module structure and key decisions (AC: 3)
  - [ ] High-level layered diagram (ASCII)
  - [ ] Module structure table (path → purpose)
  - [ ] Key technology decisions table

## Dev Notes

- **README tone**: user-facing, concise, practical. No internal implementation details. Focus on "how do I use this" not "how does this work".
- **Threat model**: write for a security reviewer, not a developer. State explicitly what Docklens does NOT do (no container execution, no registry credentials stored, no telemetry).
- **docs/architecture.md**: derive from `_bmad-output/planning-artifacts/architecture.md` but simplify for contributors. Remove implementation-level detail; keep module map and technology choices.
- **These docs are committed to the repo** — they go in `docs/` and `README.md` at the project root, not in `_bmad-output/`.

### Project Structure Notes

- `README.md` — project root (update existing file)
- `docs/threat-model.md` — new file
- `docs/architecture.md` — new file (contributor-facing, shorter than the planning artifact)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#17. Security Considerations]
- [Source: _bmad-output/planning-artifacts/prd.md — Cross-Cutting NFRs]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
