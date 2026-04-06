# Repository Guidelines

## Project Structure & Module Organization
`app/` contains the Python project managed by `uv`. Core runtime code lives in `app/finance_pipeline/`, and tests live in `app/tests/`. Stream definitions are in `sql/market_features.sql`, operational scripts are in `scripts/`, and Docker assets are under `docker/`. Use `data/sample/` for replay inputs and treat `artifacts/` as generated output.

## Build, Test, and Development Commands
Run `make install` to sync Python dependencies with `uv`. Run `make test` to execute the full `pytest` suite from `app/tests/`. Use `make mvp` for the bounded end-to-end flow, `make dev` to start the long-running stack, and `make stop` or `make reset` to tear it down. For data flows, `make replay`, `make replay-fast`, and `make binance` cover sample replay, faster replay, and live Binance ingestion.

## Coding Style & Naming Conventions
Target Python 3.10+ and follow the existing code style: 4-space indentation, type hints on public functions, and concise docstrings where behavior is not obvious. Use `snake_case` for modules, functions, and variables, `PascalCase` for classes, and descriptive script names such as `start_dev_stack.sh`. No formatter or linter is configured today, so keep imports tidy and match the surrounding file style before introducing broader refactors.

## Testing Guidelines
Tests use `pytest` and follow the `test_*.py` naming pattern under `app/tests/`. Prefer small, deterministic unit tests around strategy, schema, and sink behavior; mirror the current style of explicit fixture builders and behavior-focused test names such as `test_generate_signal_goes_long_when_return_crosses_threshold`. Run `make test` before opening a PR.

## Commit & Pull Request Guidelines
Recent commits use short imperative subjects like `Add Makefile shortcuts` and `Fix Grafana dashboard and QuestDB sink startup`. Keep commits focused and readable, and prefer branch names like `feat/<topic>` or `fix/<topic>` as described in `README.md`. PRs should explain the behavioral change, list the commands you ran, and attach screenshots only when Grafana or other UI-visible output changes.

## Agent-Specific Instructions
Contributors working through Codex or similar agents should use Chinese for user-facing conversation unless the user explicitly requests another language. Keep responses concise, technical, and tied to concrete repo actions.

## Configuration Tips
Host ports are configurable through `Makefile` variables such as `HOST_GRAFANA_PORT` and `HOST_QUESTDB_HTTP_PORT`; override them inline, for example `make dev HOST_GRAFANA_PORT=13000`. Startup scripts persist the last successful port set in `artifacts/ports.env`, reuse it on the next run, and scan upward when a preferred port is occupied. Do not commit runtime artifacts, secrets, or environment-specific port overrides.
