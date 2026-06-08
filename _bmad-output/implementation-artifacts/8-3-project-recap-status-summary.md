# Story 8.3: Project Recap & Status Summary

Status: ready-for-dev

## Story

As a project contributor,
I want a concise project status document summarising what has been built, what remains, and any known limitations,
so that anyone joining the project can quickly understand its current state.

## Acceptance Criteria

1. Recap document in `docs/` lists: completed features, backlog items, known limitations, technology decisions.
2. Document reflects the current state of the codebase (updated as part of each epic's completion).

## Tasks / Subtasks

- [ ] Create `docs/recap.md` — living status document (AC: 1, 2)
  - [ ] Section: **What's built** — table of implemented stories and their status
  - [ ] Section: **What remains** — table of backlog stories
  - [ ] Section: **Known limitations** — document v1 limitations (no runtime scanning, Linux only, CPE matching accuracy, etc.)
  - [ ] Section: **Technology decisions** — condensed version of architecture decisions table
- [ ] Add a note to `CONTRIBUTING.md` (or `README.md`) indicating that `docs/recap.md` should be updated when an epic is completed

## Dev Notes

- **This is a living document**: it does not need to be perfect at creation time. The important thing is that it exists and has the right structure. It will be updated as epics are completed.
- **Known limitations to document from day one**:
  - CPE matching accuracy: heuristic-based, ~60% accurate without the lookup table
  - Linux only: Windows containers not supported
  - Local images only (Mode A MVP): no direct registry scan without pull
  - NVD rate limiting without API key
  - No Kubernetes support in MVP
  - EUVD API stability: schema may change
- **Technology decisions**: summarise from `architecture.md#14` — just the table, no explanations needed here.

### Project Structure Notes

- `docs/recap.md` — new file, committed to repo.
- Updated on each epic completion (not automated — manual update by the developer).

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#14. Technology Decisions]
- [Source: _bmad-output/planning-artifacts/prd.md#5. Non-Goals]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
