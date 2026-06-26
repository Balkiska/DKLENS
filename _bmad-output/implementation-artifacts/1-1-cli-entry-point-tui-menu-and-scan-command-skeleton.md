# Story 1.1: CLI Entry Point, TUI Menu, and Scan Command Skeleton

Status: done

## Story

As a developer,
I want a working `docklens` CLI with an interactive TUI and a `scan` subcommand,
so that I have a solid, installable entry point to build all scanning features on top of.

## Acceptance Criteria

1. `docklens --help` exits 0 and lists the `scan` subcommand with all its flags.
2. `docklens scan --help` lists all scan flags with one-line descriptions and a usage example.
3. Running `docklens` (no args) opens an InquirerPy menu with options: Scan local image / Scan Kubernetes cluster / View cached results / Quit.
4. Selecting Quit exits with code 0.
5. `docklens scan ubuntu:22.04` prints a placeholder "Scan not yet implemented" message and exits 0.
6. `~/.config/docklens/config.toml` with `cache_ttl_hours = 48` is loaded; `Settings.cache_ttl_hours` equals 48.
7. Absent config file uses defaults (`cache_ttl_hours = 24`, `exit_on_critical = false`) without error.

## Tasks / Subtasks

- [x] Create CLI package with `__init__.py`, `main.py` entrypoint and Typer app (AC: 1, 5) — branch `feat/cli-structure`
- [x] Implement Typer app with `scan` command — now wired to real scanner pipeline (AC: 1, 5) — branch `feat/scanner`
  - [x] Calls `validate_and_pull_image()`, `extract_filesystem()`, `extract_packages()` in sequence
  - [ ] Define all scan flags: `--k8s`, `--pull`, `--exit-on-critical`, `--output`, `--output-file`, `--sbom`, `--no-cache`, `--namespace`, `--verbose` — only `image` and `--format` currently defined
- [ ] Implement `docklens/cli/tui.py` — InquirerPy main menu (AC: 3, 4) — not started
  - [ ] Four options: scan local / scan k8s / cached results / quit
  - [ ] Quit → `raise typer.Exit(0)`
- [ ] Implement `docklens/config/settings.py` — `pydantic-settings` + `tomli` (AC: 6, 7) — not started
  - [ ] `Settings` model with fields: `cache_ttl_hours`, `nvd_api_key`, `default_output_format`, `exit_on_critical`, `cache_db_path`, `log_level`
  - [ ] Read from `~/.config/docklens/config.toml`; env prefix `DOCKLENS_`
  - [ ] Missing file → use defaults silently
- [ ] Add `docklens/core/models.py` — `Package`, `Vulnerability`, `ScanResult` Pydantic v2 models — not started
- [ ] Write unit tests: `tests/unit/test_settings.py` (AC: 6, 7) — not started
- [ ] Verify `docklens --help` and `docklens scan ubuntu:22.04` work end-to-end after `poetry install`

## Dev Notes

- **Typer app**: use `typer.Typer(name="docklens")`. The `scan` command must accept `image` as an optional `Argument` (not `Option`) so it can be None when TUI is triggered.
- **TUI trigger**: in `scan()`, if `image is None` and `not k8s`, call `tui.run_menu()` to launch InquirerPy.
- **Settings singleton**: instantiate `Settings()` once at module level in `config/settings.py`; import it everywhere else. Do not re-instantiate per request.
- **tomli note**: `tomli` is stdlib as `tomllib` in Python 3.11+. Use `try: import tomllib except ImportError: import tomli as tomllib` for compatibility if needed, but since we target 3.11+ this is not required.
- **Models**: `ScanResult` must include a `warnings: list[str] = []` field for non-fatal API errors (used from Epic 3 onward).
- **No Docker SDK or K8s client imports here** — the CLI layer must not depend on adapters directly.

### Project Structure Notes

- Entrypoint defined in `pyproject.toml` under `[tool.poetry.scripts]`.
- Config reads from `Path.home() / ".config" / "docklens" / "config.toml"`.
- All models live in `docklens/core/models.py` — do not scatter them.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#2. Repository Layout]
- [Source: _bmad-output/planning-artifacts/architecture.md#11. CLI Structure]
- [Source: _bmad-output/planning-artifacts/architecture.md#9. Configuration]
- [Source: _bmad-output/planning-artifacts/prd.md#4.1 CLI Entry Point — FR-1, FR-2, FR-3, FR-27]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Typer app + `scan` command stub implemented on branch `feat/cli-structure`.
- Only `image` (required Argument) and `--format` (table/json) flags are defined — all other flags from the story still need to be added.
- `image` is currently a required positional argument, not optional. This means the TUI cannot be triggered without arguments yet — needs to be changed to `Optional[str] = typer.Argument(None)`.
- File layout is flat (`cli/menu.py`, `cli/output.py`) rather than the planned `docklens/cli/` package structure — will need to be reconciled when the project is properly packaged.
- ACs 3, 4 (TUI), 6, 7 (config) not started.

### File List

- `cli/__init__.py`
- `cli/menu.py` (Typer app + scan stub)
- `cli/output.py` (show_table, show_json helpers)
- `main.py` (entrypoint)
- `tests/test_output.py`
