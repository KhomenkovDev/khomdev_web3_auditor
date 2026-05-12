# Web3 Auditor

AI-powered code reviewer for Solidity smart contracts and Python projects.
Uses Google Gemini for security audits and refactoring suggestions.

## Features

- Scan local files or GitHub repositories for Solidity (`.sol`), Python (`.py`), and JavaScript (`.js`) sources
- Generate structured security audits via Gemini (overview, vulnerabilities, improvements, code upgrades)
- Interactive follow-up chat session after initial review
- Two interfaces: desktop GUI (PyQt6) and web UI (FastAPI)
- Dependency graph analysis for `.sol` and `.py` files
- Optional static analyzer integration (Slither, Bandit)
- Live SSE telemetry feed during scans

## Quick Start

1. Copy `.env.example` to `.env` and set `GEMINI_API_KEY`.
2. Install: `pip install -e ".[web]"` (web UI) or `pip install -e ".[gui]"` (desktop GUI)
3. Run:
   - Desktop GUI: `web3-auditor`
   - Web UI: `uvicorn web.app:app`

### Docker

```bash
docker compose up --build
```

Open http://localhost:8080.

## Project Structure

```
web3_auditor/       Core library
├── scanner.py      Source file discovery
├── github.py       Git clone / cleanup with URL validation
├── llm_chat.py     Gemini chat with JSON structured output
├── deps.py         Dependency graph builder
├── analyzers/      Static analyzer runners
│   ├── slither_runner.py
│   └── bandit_runner.py
├── gui.py          PyQt6 desktop GUI
└── cli.py          Entry point

web/                FastAPI web application
├── app.py          Application factory with config validation
├── routes.py       API endpoints with SSE telemetry
├── session.py      TTL-based session store
├── templates/      Jinja2 templates
└── static/         Frontend assets

tests/              pytest test suite
```

## Configuration

| Variable       | Default              | Description       |
|----------------|----------------------|-------------------|
| `GEMINI_API_KEY` | —                    | Google Gemini API key |
| `GEMINI_MODEL`   | `gemini-2.5-flash`   | Model name        |
| `APP_NAME`       | `Code Reviewer`      | Window / page title |
