# Development Plan

## Objective

当前目标不是继续堆单点功能，而是把项目从单标的 MVP 推到可扩展的波动率研究骨架：

1. 多标的 underlying 能力
2. 面向 future realized vol 的特征与标签
3. 更真实的 strategy / portfolio / risk 分层
4. 后续可平滑扩展到 options / IV analytics
5. 本地 fixture / simulate-first 工作流

当前开发方式改为串行推进，不再维护并行 worktree 或 `docs/parallel-status.md`。

## Priority Order

建议严格按下面顺序推进：

1. Multi-asset schema and feature pipeline
2. Volatility feature engine and forward-vol labels
3. Strategy and portfolio sizing/risk
4. Simulation and replay scenario library
5. Options schema, IV analytics, skew/term structure

不要一开始就直接冲 options。先把多标的 underlying 骨架和波动率预测闭环打稳，后面再往 IV 和 options 升维。

## Current Stage

当前已经完成的收口：

- 核心四类消息 schema 统一增加了 `venue`、`instrument_type`、`base_asset`、`quote_asset`
- source / strategy / portfolio / QuestDB sink 已经开始透传这些字段
- Kafka key 从单纯 `symbol` 升级为 instrument 维度，避免同名 symbol 跨 venue 冲突
- Flink 第一批窗口特征已经覆盖 VWAP、价格波动率、买卖量不平衡，并修正了 open/close 的时间语义

这一步的目标不是直接把系统做成完整 multi-asset 平台，而是先把主键和消息格式打稳。

## Next Milestones

### Milestone 1: Volatility Feature Engine

优先改 `sql/market_features.sql`，把现在的基础窗口聚合升级为真正可交易的特征：

- VWAP
- rolling volatility
- buy/sell volume imbalance
- forward-vol label ready outputs
- correlation-ready outputs

当前这一批里，VWAP / price volatility / volume imbalance 与时间语义正确的 open/close 已经补上。下一步还缺的是更明确的 forward-vol label outputs、correlation-ready outputs，以及跨窗口 rolling state。

### Milestone 2: Vol Forecasting / Strategy / Portfolio / Risk

在特征层稳定之后，再改 Python 侧：

- 先定义 future realized vol 的预测 horizon
- 从单阈值动量扩展到 volatility-oriented signal interface
- 增加 position sizing
- 增加 gross / net exposure
- 增加资金分配和风险钩子

建议重点文件：

- `app/finance_pipeline/strategy.py`
- `app/finance_pipeline/strategy_service.py`
- `app/finance_pipeline/portfolio.py`
- `app/finance_pipeline/portfolio_service.py`

### Milestone 3: Source / Simulation / Observability

等前两层稳定后，再做开发效率增强：

- 更多 synthetic regimes
- 更细的 replay presets
- 更明确的 dashboard 过滤维度
- runbook 补充多 source / 多 venue 说明
- 为后续 IV 接入预留 option chain replay 入口

## Serial Workflow

推荐串行开发节奏：

1. 先改一条最小闭环
2. 本地跑 `make test`
3. 需要数据链路验证时跑 `make replay`
4. 需要整链路验证时跑 `make dev`、`make simulate`、`make net`
5. 每完成一个里程碑就回到文档，更新当前阶段和下一步

## Conflict Rules

即使现在按串行开发，也要避免一次同时改太多共享文件。高风险文件仍然是：

- `config/development.yaml`
- `app/finance_pipeline/settings.py`
- `app/pyproject.toml`
- `app/uv.lock`
- `README.md`

修改这些文件时，优先把目标收窄到当前里程碑，不顺手做无关重构。
