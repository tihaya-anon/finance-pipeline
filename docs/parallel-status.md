# Parallel Status

## Usage

这个文件用于本地并行开发时同步状态。规则：

- 每个 feature branch / worktree 占一行
- 状态只用：`planned`、`in_progress`、`blocked`、`ready_to_merge`、`merged`
- worker 开始前先更新状态
- worker 提交前再更新一次
- integrator merge 完成后把状态改成 `merged`

## Active Streams

| Stream | Branch | Worktree | Owner | Status | Scope | Notes |
|---|---|---|---|---|---|---|
| Schema | `feat/multi-asset-schema` | `../finance-pipeline-schema` | unassigned | planned | `schemas.py`, topic design, docs |  |
| Features | `feat/flink-feature-engine` | `../finance-pipeline-features` | unassigned | planned | `sql/market_features.sql`, feature docs |  |
| Strategy | `feat/strategy-risk-layer` | `../finance-pipeline-strategy` | unassigned | planned | strategy, portfolio, risk |  |
| Simulation | `feat/simulation-scenarios` | `../finance-pipeline-sim` | unassigned | planned | simulate, fixture, dashboard |  |

## Merge Queue

| Order | Branch | Preconditions | Integrator Check |
|---|---|---|---|
| 1 | `feat/multi-asset-schema` | schema reviewed, tests pass | merge + `make test` |
| 2 | `feat/flink-feature-engine` | depends on latest schema | merge + `make replay` |
| 3 | `feat/strategy-risk-layer` | depends on latest schema/features | merge + `make test` |
| 4 | `feat/simulation-scenarios` | no blocking shared files | merge + `make simulate` |

## Shared Files Requiring Integrator Coordination

- `config/development.yaml`
- `app/finance_pipeline/settings.py`
- `app/pyproject.toml`
- `app/uv.lock`
- `README.md`
- `docker/grafana/dashboards/finance-pipeline.json`

## Current Integration Baseline

- Branch: `main`
- Stack owner: integrator terminal only
- Long-running commands:
  - `make dev`
  - `make simulate`
- Quick validation:
  - `make test`
  - `make replay`
  - `make net`
