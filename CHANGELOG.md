# Changelog

## 0.1.0 — 2026-05-12

- Initial refactor: cleaned junk files, added project scaffolding.
- Restructured web3_auditor modules with service layer, logging, and env-var configuration.
- Restructured FastAPI web app with modular route handlers.
- Replaced print/logging with proper logging module.
- Added test suite with 35 tests (scanner, github, llm_chat, web routes).
- Added pyproject.toml with ruff, mypy, and pytest configuration.
- Added docker-compose.yml for local development.
- Added .env.example with documented environment variables.
- Removed hardcoded branding in favour of APP_NAME env var.
- Bumped Docker image from Python 3.11 to 3.12.
- Rewrote README with plain technical description.
