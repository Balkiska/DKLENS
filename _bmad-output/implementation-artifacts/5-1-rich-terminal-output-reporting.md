# Story 5.1: Rich Terminal Output & Reporting

Status: ready-for-dev

## Story

As a developer,
I want Docklens to display scan results as a Rich summary panel and sortable CVE table,
so that I can immediately understand the security posture of my image.

## Acceptance Criteria

1. Completed scan with CVEs → summary panel shows: image name, Risk Score, CVE totals (C/H/M/L), scan duration, timestamp.
2. CVE table columns: CVE ID, Package, Installed Version, Fixed Version, CVSS, Severity, Link — severity colour-coded.
3. No line wrapping on an 80-column terminal.
4. Zero CVEs → summary panel shows Risk Score = 0 and a "" message; no empty table rendered.
5. `--output json` → valid JSON to stdout matching `ScanResult` schema.
6. `--output json --output-file results.json` → JSON written to file; nothing printed to stdout.
7. `--sbom` → CycloneDX v1.4 JSON written to `sbom.json` (or `--output-file` path).

## Tasks / Subtasks

- [ ] Implement `render_summary_panel(result: ScanResult) -> Panel` in `docklens/cli/output.py` (AC: 1, 4)
  - [ ] Rich `Panel` with title = image name
  - [ ] Grid showing Risk Score, C/H/M/L counts, timestamp, duration
  - [ ] If zero CVEs: add "" row
- [ ] Implement `render_cve_table(result: ScanResult) -> Table` in `docklens/cli/output.py` (AC: 2, 3)
  - [ ] Columns (in order): CVE ID, Package, Installed Ver, Fixed Ver, CVSS, Severity, Link
  - [ ] Severity colour: `[red]CRITICAL[/]`, `[orange3]HIGH[/]`, `[yellow]MEDIUM[/]`, default LOW
  - [ ] Use `format_link()` from Story 4.4 for Link column
  - [ ] Table `show_header=True`, `box=rich.box.SIMPLE` — fits 80 cols
- [ ] Implement `print_results(result: ScanResult, console: Console)` (AC: 1–4)
  - [ ] `console.print(render_summary_panel(result))`
  - [ ] If `result.vulnerabilities`: `console.print(render_cve_table(result))`
- [ ] Implement `export_json(result: ScanResult, output_file: Path | None)` (AC: 5, 6)
  - [ ] `json_str = result.model_dump_json(indent=2)`
  - [ ] If `output_file`: write to file silently; else `typer.echo(json_str)`
- [ ] Implement `export_sbom(result: ScanResult, output_file: Path)` (AC: 7)
  - [ ] Build CycloneDX v1.4 JSON dict manually (no heavy library); write to file
  - [ ] Minimum fields: `bomFormat`, `specVersion`, `version`, `metadata.timestamp`, `components[]`
- [ ] Wire `print_results` / `export_json` / `export_sbom` into `cli/main.py` based on `--output` and `--sbom` flags
- [ ] Write unit tests `tests/unit/test_output.py` — verify panel/table structure with mock `ScanResult`

## Dev Notes

- **Column widths**: CVE ID (~20), Package (~20), Installed Ver (~15), Fixed Ver (~15), CVSS (~6), Severity (~10), Link (~15) = ~101 total. Use `Table(expand=False)` and set `max_width` on the Link column to keep it within 80 cols.
- **Rich box**: `rich.box.SIMPLE` uses minimal borders and fits narrow terminals. Avoid `HEAVY` or `DOUBLE`.
- **CycloneDX minimal schema**:
  ```json
  {
    "bomFormat": "CycloneDX",
    "specVersion": "1.4",
    "version": 1,
    "metadata": {"timestamp": "...", "tools": [{"name": "docklens"}]},
    "components": [{"type": "library", "name": "...", "version": "...", "purl": "pkg:{ecosystem}/{name}@{version}"}]
  }
  ```
- **Duration**: `ScanResult.duration_seconds` — format as `f"{duration:.1f}s"`.
- **Warnings display**: if `result.warnings` is non-empty, print them after the table as yellow `[WARNING]` lines.

### Project Structure Notes

- All rendering functions live in `docklens/cli/output.py`.
- `cli/main.py` imports `output` and calls render functions; no Rich imports in `main.py` directly.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#12. Output Layer]
- [Source: _bmad-output/planning-artifacts/prd.md#4.7 Terminal Output & Reporting — FR-20, FR-21, FR-22, FR-23]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
