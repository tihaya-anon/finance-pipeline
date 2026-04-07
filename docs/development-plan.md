# Development Plan

## Objective

当前目标不是继续堆单点功能，而是把项目改造成适合并行开发的量化研究骨架：

1. 多标的 underlying 能力
2. 更真实的 strategy / portfolio / risk 分层
3. 后续可平滑扩展到 perps / options
4. 本地 fixture / simulate-first 工作流

## Recommended Workstreams

建议把并行开发拆成 4 条主线，尽量减少文件冲突：

### Stream A: Data Model & Topics

- 扩展 `schemas.py`
- 为 multi-asset / derivatives 设计新 schema
- 规划新 Kafka topics
- 保持向后兼容或明确迁移路径

建议负责文件：

- `app/finance_pipeline/schemas.py`
- `docs/architecture.md`
- `docs/data-sources.md`

### Stream B: Feature Engine

- 扩展 Flink SQL 特征
- 从单标的窗口特征扩展到 multi-asset / cross-sectional 特征
- 第一批优先做：rolling volatility、VWAP、imbalance、correlation-ready outputs

建议负责文件：

- `sql/market_features.sql`
- `docker/flink/`
- `docs/architecture.md`

### Stream C: Strategy / Portfolio / Risk

- 把当前单阈值动量扩展为多策略框架
- 增加 position sizing、gross/net exposure、资金分配
- 为后续 options/perps 预留 risk hooks

建议负责文件：

- `app/finance_pipeline/strategy.py`
- `app/finance_pipeline/strategy_service.py`
- `app/finance_pipeline/portfolio.py`
- `app/finance_pipeline/portfolio_service.py`

### Stream D: Source / Fixture / Simulation / Observability

- 强化 `simulate`、fixture capture、replay profiles
- 增加可切换 market regimes
- 完善 Grafana dashboard 和 runbook

建议负责文件：

- `app/finance_pipeline/simulated_source.py`
- `app/finance_pipeline/capture_onchain.py`
- `config/development.yaml`
- `docker/grafana/`
- `docs/runbook.md`

## Priority Order

建议按下面顺序推进：

1. Multi-asset schema and feature pipeline
2. Strategy and portfolio sizing/risk
3. Simulation and replay scenario library
4. Perps extensions
5. Options schema, Greeks, IV surface, skew/term structure

不要一开始就直接冲 options。先把多标的 underlying 骨架打稳，后面再往 options 升维。

## Local Branch Strategy

没有远端仓库时，最适合你的不是多个 branch 共用一个目录，而是：

`git worktree + feature branch`

原因：

- 每条功能线有独立目录，不会互相覆盖文件
- 每个 terminal / Codex 可以绑定一个 worktree
- 避免频繁 `git checkout` 打断别人的工作
- 更接近真实团队开发流程

推荐分支命名：

- `feat/multi-asset-schema`
- `feat/flink-feature-engine`
- `feat/strategy-risk-layer`
- `feat/simulation-scenarios`
- `fix/<topic>`
- `docs/<topic>`

## Recommended Worktree Layout

保留一个集成主目录，再为每条功能线开独立 worktree：

```bash
git worktree add ../finance-pipeline-schema -b feat/multi-asset-schema main
git worktree add ../finance-pipeline-features -b feat/flink-feature-engine main
git worktree add ../finance-pipeline-strategy -b feat/strategy-risk-layer main
git worktree add ../finance-pipeline-sim -b feat/simulation-scenarios main
```

建议约定：

- 当前目录 `/finance-pipeline` 作为 integration worktree
- 只有 integration worktree 负责最终 merge
- 只有一个 worktree 长期开 `make dev`

## Merge Workflow

推荐本地流程：

1. 每条功能线在自己的 worktree 开发
2. 每条功能线自己 `make test`
3. 完成后在该分支小步提交
4. 切回 integration worktree 的 `main`
5. 顺序执行 `git merge --no-ff feat/<topic>`
6. 每合一条线就跑一次：

```bash
make test
make replay
make net
```

如果合并内容影响 dashboard 或数据链路，再额外跑：

```bash
make dev
make simulate
```

## Conflict Avoidance Rules

并行开发时要明确文件所有权。优先避免多人同时改这些高冲突文件：

- `config/development.yaml`
- `app/finance_pipeline/settings.py`
- `app/pyproject.toml`
- `app/uv.lock`
- `README.md`

建议规则：

- 配置/锁文件由 integration owner 统一收口
- 公共 schema 变更先约定字段，再分别开发
- Grafana dashboard 只给一个人改
- 每条分支尽量聚焦单一 write set

## Codex Workflow

你的设想是对的：多开 terminal 可以显著提效，但前提是每个 terminal 对应独立 worktree。

推荐角色分工：

### Terminal 1: Integrator

- 绑定主 worktree
- 负责 merge、回归验证、最终修冲突
- 负责唯一的 `make dev`

### Terminal 2+: Workers

- 每个 terminal 绑定一个 feature worktree
- 每个 worker 只负责一条主线
- worker 默认只跑本分支需要的测试，不启动全套 stack

## Integrator Operation Flow

目标是：你只需要盯住一个 integrate terminal，其他 worker terminal 只负责各自功能线。

### Step 1: 创建 worktree

在主目录执行一次：

```bash
git worktree add ../finance-pipeline-schema -b feat/multi-asset-schema main
git worktree add ../finance-pipeline-features -b feat/flink-feature-engine main
git worktree add ../finance-pipeline-strategy -b feat/strategy-risk-layer main
git worktree add ../finance-pipeline-sim -b feat/simulation-scenarios main
```

### Step 2: 创建 tmux session

推荐用一个统一 session，例如：

```bash
tmux new -s quant-dev
```

推荐布局：

- Window 1: `integrate`
- Window 2: `schema`
- Window 3: `features`
- Window 4: `strategy`
- Window 5: `sim`

每个 window 进入对应目录：

```bash
cd /home/labuser/code/quant/proj/finance-pipeline
cd /home/labuser/code/quant/finance-pipeline-schema
cd /home/labuser/code/quant/finance-pipeline-features
cd /home/labuser/code/quant/finance-pipeline-strategy
cd /home/labuser/code/quant/finance-pipeline-sim
```

### Step 3: 角色固定

Integrator window 只做：

- `make dev`
- `make simulate`
- `make net`
- merge
- 回归验证

Worker windows 只做：

- 本分支编码
- `make test`
- 必要的局部命令

不要在 worker window 起整套 stack。

### Step 4: 启动主栈

只在 integrate window 执行：

```bash
make dev
make simulate
```

需要时再执行：

```bash
make replay
make net
```

### Step 5: 启动各个 Codex

每个 tmux window 启一个 Codex，并告诉它自己的责任边界：

- schema window: 只动 schema / docs / topics
- feature window: 只动 Flink SQL / feature engine
- strategy window: 只动 strategy / portfolio / risk
- sim window: 只动 simulate / fixture / dashboard

### Step 6: Worker 完成后通知 Integrator

每条线完成后，在该 worker worktree：

```bash
make test
git status
git add ...
git commit -m "..."
```

然后由 integrator window 执行：

```bash
cd /home/labuser/code/quant/proj/finance-pipeline
git merge --no-ff feat/<topic>
make test
make replay
make net
```

如果 merge 影响整条链路，再加：

```bash
make simulate
```

### Step 7: 冲突处理规则

如果 merge 冲突发生在以下文件：

- `config/development.yaml`
- `app/finance_pipeline/settings.py`
- `app/pyproject.toml`
- `app/uv.lock`
- `README.md`

统一由 integrator 解决，worker 不直接在主线抢修。

## Agent Instructions

给每个 agent 的固定操作规则：

1. 只在自己的 worktree 工作
2. 不切换到别人的 branch
3. 不启动 `make dev`
4. 不改共享锁文件，除非 integrator 明确授权
5. 完成后先本地 `make test`
6. 提交前更新 `docs/parallel-status.md`

agent 在开始前应先确认：

- 当前负责的 stream
- 自己允许改动的文件集合
- 当前是否依赖 integration 分支上的最新变更

## tmux Tips

如果你准备长期这么用，推荐下面几个惯例：

### Window naming

```bash
tmux rename-window integrate
tmux new-window -n schema
tmux new-window -n features
tmux new-window -n strategy
tmux new-window -n sim
```

### Quick switching

- `Ctrl-b w` 看所有窗口
- `Ctrl-b 0..9` 直接切窗口
- `Ctrl-b ,` 重命名窗口

### Suggested statusline habit

始终让 window 名和 worktree 责任一致，不要混用。

## Recommended Daily Rhythm

每天建议按这个节奏：

1. integrator 拉起主栈
2. workers 各自开始独立功能线
3. 每完成一个小点就 commit
4. 半天内至少 merge 一次最小闭环
5. 当天结束前保证 integration `main` 是可测试、可运行的

## Efficiency Tips

### 1. One Stack Owner

不要多个 worktree 同时跑 `make dev`，容易造成：

- 端口竞争
- 多套 Docker Compose 栈
- 日志和状态难以判断

规则：

- 只有 integrator terminal 长期开 stack
- 其他 worker 默认跑 `make test`、局部命令、静态检查

### 2. Simulate First

开发联调优先用：

```bash
make simulate
```

它比反复抓链上数据或手动 replay 更稳定。

### 3. Small Merge Batches

不要等 4 条线都完成再一次性合并。建议：

- 每完成一个小 milestone 就 merge 一次
- 每次 merge 只引入一条主线的最小闭环

### 4. Lockfile Ownership

如果某个 worker 改了 `app/pyproject.toml`，应由 integrator 统一处理 `uv lock`，避免多分支同时改 `uv.lock`。

### 5. Shared Planning File

如果并行工作持续时间较长，建议在仓库内维护一个简单状态文件，例如：

- `docs/development-plan.md` 记录长期计划
- `docs/parallel-status.md` 记录当前谁在做哪条线、是否已 merge

## Immediate Next Iteration

建议下一轮并行开发就按下面切：

1. `feat/multi-asset-schema`
   目标：schema 和 topics 支持多标的

2. `feat/flink-feature-engine`
   目标：rolling vol、VWAP、volume imbalance

3. `feat/strategy-risk-layer`
   目标：position sizing、gross/net exposure、multi-symbol portfolio

4. `feat/simulation-scenarios`
   目标：更多 synthetic regimes、scenario presets、Grafana 演示增强

当这 4 条合完后，再开：

5. `feat/perps-basis`
6. `feat/options-schema`
7. `feat/options-greeks-surface`
