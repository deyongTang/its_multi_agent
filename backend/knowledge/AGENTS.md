# Repository Guidelines

## Project Structure & Module Organization
This repository is a Python FastAPI backend under `backend/knowledge`.

- `api/`: API entrypoints and routers (`api/main.py`, `api/routers.py`, `api/auth_routes.py`)
- `business_logic/`, `services/`: orchestration and domain services (retrieval, ingestion, crawler, embeddings)
- `data_access/`, `repositories/`, `infrastructure/`: persistence, ES/MinIO/database clients, middleware, logging
- `config/`: runtime settings loaded from `.env`
- `scripts/`: operational scripts (DB init, migrations, ES index/template setup)
- `migrations/`: SQL schema migrations
- `test/` and root `test_*.py`: test and verification scripts
- `data/`, `logs/`: runtime data and logs (do not commit generated artifacts)

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create local virtualenv
- `pip install -r requirements.txt`: install dependencies
- `python api/main.py`: run API locally on `:8001`
- `pytest -q`: run tests
- `docker compose up -d --build`: start containerized service
- `docker compose logs -f knowledge-api`: stream API logs
- `bash deploy.sh`: one-command deployment wrapper used by this project

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation and UTF-8 source files.
- Use `snake_case` for functions/modules/variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants/env keys.
- Keep API schemas in `schemas/`, business orchestration in `business_logic/`, and external integrations in `infrastructure/` or `data_access/`.
- Prefer explicit type hints for new service interfaces and request/response models.

## Testing Guidelines
- Test framework: `pytest`.
- Name tests as `test_*.py`; keep unit-like tests in `test/` and integration checks near root only when necessary.
- For API/integration tests (for example auth/login), start the service first (`python api/main.py`) and use `.test-env`/`.env` values appropriate to the environment.
- Add tests for new business logic and edge cases around retrieval, ingestion, and auth paths.

## Commit & Pull Request Guidelines
- Current history is mixed (`init`, short notes, and some `feat:`). For new work, use clear Conventional Commit-style messages, e.g. `feat(api): add token refresh endpoint`.
- Keep commits focused and atomic; avoid bundling refactors with feature behavior changes.
- PRs should include: purpose, changed modules, config/migration impact, test evidence (`pytest` or manual API checks), and sample request/response when API behavior changes.

## Security & Configuration Tips
- Never commit real secrets in `.env`, `.test-env`, or logs.
- Validate required external dependencies (OpenAI-compatible API, Elasticsearch, MinIO, optional MySQL) before running ingestion/retrieval flows.
- When changing logging or middleware, preserve traceability (`TraceIdMiddleware`) and structured logs.
