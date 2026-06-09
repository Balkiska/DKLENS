# Story 7.1: FastAPI REST API Server

Status: ready-for-dev

## Story

As a tool integrator,
I want a local REST API server that exposes Docklens scan functionality,
so that I can trigger scans and consume results from other tools without using the CLI directly.

## Acceptance Criteria

1. `docklens serve --port 8080` starts the server; `GET /health` returns HTTP 200 `{"status": "ok"}`.
2. `POST /scan` with `{"image": "ubuntu:22.04"}` → HTTP 200 with same JSON payload as `--output json`.
3. Image not found locally → HTTP 404 `{"error": "Image not found"}`.
4. Missing `image` key in request body → HTTP 422 with validation error.
5. All responses have `Content-Type: application/json`.

## Tasks / Subtasks

- [ ] Add `fastapi` and `uvicorn` to optional dependency group in `pyproject.toml` (AC: 1)
- [ ] Implement `docklens/api/server.py` — FastAPI app (AC: 1–5)
  - [ ] `GET /health` → `{"status": "ok"}`
  - [ ] `POST /scan` — request body: `class ScanRequest(BaseModel): image: str`
  - [ ] Call `Scanner.scan(image_ref=body.image)` — reuse existing scan pipeline
  - [ ] On `DocklensError` (image not found) → `HTTPException(status_code=404, detail={"error": str(e)})`
  - [ ] Return `result.model_dump()` as JSON response
- [ ] Add `serve` command to `docklens/cli/main.py` (AC: 1)
  - [ ] `docklens serve --port 8080` → `uvicorn.run("docklens.api.server:app", host="127.0.0.1", port=port)`
- [ ] Write integration tests `tests/integration/test_api.py` using `httpx.AsyncClient` with `app` (AC: 1–5)

## Dev Notes

- **FastAPI optional**: add to `pyproject.toml` as `[tool.poetry.extras]`: `api = ["fastapi", "uvicorn[standard]"]`. Install with `poetry install --extras api`. The CLI works without it; the `serve` command fails gracefully with "Install docklens[api] to use the API server" if FastAPI is not installed.
- **Localhost only**: bind to `127.0.0.1` not `0.0.0.0` — the API is explicitly local-only for v1 (no auth).
- **Reuse Scanner**: instantiate `Scanner` with `Settings()` and `CacheRepository()` inside the FastAPI app startup event (`lifespan` context manager in FastAPI 0.95+).
- **422 validation**: FastAPI handles this automatically via Pydantic model validation — no manual code needed.
- **Response model**: use `response_model=ScanResultResponse` (a stripped-down Pydantic model for the API) or just return `result.model_dump()` directly. For v1, `model_dump()` is fine.

### Project Structure Notes

- `docklens/api/server.py` — the FastAPI `app` instance.
- `docklens/api/__init__.py` — empty init.
- `serve` command is a new Typer subcommand in `cli/main.py`.

### References

- [Source: _bmad-output/planning-artifacts/prd.md#4.10 REST API — FR-28, FR-29]
- [Source: _bmad-output/planning-artifacts/architecture.md#2. Repository Layout]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
