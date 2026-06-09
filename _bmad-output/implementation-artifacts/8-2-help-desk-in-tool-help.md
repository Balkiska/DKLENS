# Story 8.2: Help Desk & In-Tool Help

Status: ready-for-dev

## Story

As a user,
I want useful help text and error messages inside the tool,
so that I can resolve common issues without reading external documentation.

## Acceptance Criteria

1. `docklens --help` — every flag has a one-line description.
2. `docklens scan --help` — usage examples shown.
3. Unexpected error → user-friendly message printed (no raw traceback unless `--verbose`); `--verbose` prints full traceback.
4. `NVD_API_KEY` not set → one-time INFO notice about rate limiting shown at scan start.

## Tasks / Subtasks

- [ ] Audit all Typer option/argument definitions in `cli/main.py` — ensure every flag has a `help=` string (AC: 1, 2)
  - [ ] Add `rich_markup_mode="markdown"` to `typer.Typer()` for formatted help output
  - [ ] Add `epilog=` with a usage example block to the `scan` command
- [ ] Implement global exception handler in `cli/main.py` (AC: 3)
  - [ ] Wrap `app()` call in try/except; on unexpected exception:
    - [ ] If `--verbose`: `import traceback; traceback.print_exc()`
    - [ ] Else: `typer.echo(f"Error: {e}", err=True); typer.echo("Run with --verbose for details.", err=True)`
  - [ ] `DocklensError` is caught earlier and already has a user-friendly message
- [ ] Add NVD API key notice in `core/scanner.py` — log once per session at INFO level (AC: 4)
  - [ ] Use a module-level `_nvd_key_warned: bool = False` flag to ensure single warning

## Dev Notes

- **Typer `help=`**: Typer uses the Python docstring of the command function as the main help text. Add a docstring to `scan()` with a short description and example.
- **`epilog`**: Typer supports `epilog` on commands for additional help text. Use it for a "Examples:" block.
- **Exception handler**: wrap at the `if __name__ == "__main__": app()` level, not inside individual commands — this catches unhandled exceptions from anywhere in the call stack.
- **`--verbose` and logging**: `--verbose` flag should also set `logging.basicConfig(level=logging.DEBUG)` at startup to enable debug logs throughout the stack.
- **NVD notice**: `logging.getLogger("docklens.cve.nvd").info("NVD API key not set — rate-limited. Set DOCKLENS_NVD_API_KEY for better performance.")` — only runs once.

### Project Structure Notes

- All changes are in `docklens/cli/main.py` and `docklens/cve/nvd.py`.
- No new files required.

### References

- [Source: _bmad-output/planning-artifacts/prd.md#4.1 CLI Entry Point — FR-1, FR-2]
- [Source: _bmad-output/planning-artifacts/architecture.md#15. Error Handling Conventions]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
