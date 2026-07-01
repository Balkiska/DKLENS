# Story 4.4: Remediation Fix Links in Output

Status: ready-for-dev

## Story

As a developer,
I want fix advisory links rendered as clickable hyperlinks (or plain URLs) in the terminal output,
so that I can navigate directly to the fix from my terminal.

## Acceptance Criteria

1. OSC-8-supporting terminal → advisory URL column shows a clickable hyperlink labelled with the CVE ID.
2. Non-OSC-8 terminal → plain URL string printed in the Link column.
3. `advisory_url = None` → Link cell shows "—" (dash); no crash.

## Tasks / Subtasks

- [ ] Add `format_link(url: str | None, label: str) -> str` to `docklens/cli/output.py` (AC: 1–3)
  - [ ] If `url is None` → return `"—"`
  - [ ] Detect OSC-8 support: check `os.environ.get("TERM")` and Rich's `Console().is_terminal`
  - [ ] OSC-8 format: `f"\x1b]8;;{url}\x1b\\{label}\x1b]8;;\x1b\\"`
  - [ ] Fallback: return `url` (plain string)
- [ ] Use `format_link()` in the CVE table's Link column rendering (Story 5.1 will wire the full table; this story adds the helper and connects it to the vulnerability model)
- [ ] Write unit tests `tests/unit/test_output.py` — test `format_link` for all three cases (AC: 1–3)
  - [ ] Mock `Console().is_terminal` to test both paths without a real terminal

## Dev Notes

- **OSC-8 detection**: Rich's `Console(force_terminal=True)` does not mean OSC-8 is supported. A pragmatic heuristic: check `os.environ.get("COLORTERM") in ("truecolor", "24bit")` as a proxy for a modern terminal. This is imperfect but good enough for v1.
- **Rich `Text` with hyperlinks**: Rich supports hyperlinks natively via `Text("label", style="link url")`. Prefer this over raw OSC-8 escape sequences when rendering inside a Rich `Table` — it handles terminal capability detection internally.
- **`"—"` character**: use the em-dash U+2014, not a hyphen. Ensure the terminal's encoding supports it (UTF-8 default).

### Project Structure Notes

- `format_link` is a utility in `docklens/cli/output.py`.
- Story 5.1 uses this helper when building the Rich CVE table.

### References

- [Source: _bmad-output/planning-artifacts/prd.md#4.6 Remediation & Fix Links — FR-19]
- [Source: _bmad-output/planning-artifacts/architecture.md#12. Output Layer]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
