# Finance Pipeline MVP

这是一个按 `PROPOSAL.md` 落地的最小可行项目：用 crypto 模拟数据先把量化数据链路跑通，再把复杂度留给后续扩展。

当前闭环：

1. CSV replay 把 `BTCUSDT` tick 数据回放到 Kafka
2. Flink SQL 做 5 秒窗口聚合，产出实时市场特征
3. Python 策略服务消费特征，生成简单动量信号
4. Python 组合服务消费信号，记录仓位、现金和权益快照
5. QuestDB 持久化结果流，Grafana 实时展示大盘，Redpanda Console 用于 topic 观测

## 技术栈

- Infra: Docker Compose, Redpanda, Apache Flink
- Python: `uv`, `kafka-python`, `pytest`
- Stream job: Flink SQL

## 目录结构

```text
config/                 YAML 运行配置
app/                    Python 子工程根目录
app/finance_pipeline/   Python package
app/tests/              Python 单测
data/sample/            示例行情
data/fixtures/          本地 fixture 与合成数据
docs/                   设计与运行文档
docker/flink/           Flink 自定义镜像
sql/                    Flink SQL 作业
scripts/                启动与验证脚本
artifacts/              运行结果输出
```

## Git 策略

- 默认分支：`main`
- 开发分支：`feat/<topic>`、`fix/<topic>`
- MVP 阶段建议保持小步提交，避免一开始做 trunk 之外的复杂分支模型

## 快速开始

前提：

- 本机安装 `uv`
- 本机安装 Docker 和 Docker Compose

先同步依赖并跑测试：

```bash
make install
make test
```

运行参数默认来自 `config/development.yaml`。需要切换配置文件时使用：

```bash
make dev CONFIG_FILE=config/development.yaml
```

启动完整 MVP：

```bash
make mvp
```

启动常驻开发栈和可视化：

```bash
make dev
```

启动脚本会自动探测宿主机端口冲突，向上寻找空闲端口，并把本次成功端口保存到 `artifacts/ports.env` 以便下次复用。
开发模式默认只保留短期数据：Kafka topics 默认保留 `1` 小时，QuestDB 分析表按小时分区并默认保留 `6` 小时。

常用入口：

- `make ports`
- Redpanda Console: `http://127.0.0.1:<HOST_CONSOLE_PORT>`
- Grafana: `http://127.0.0.1:<HOST_GRAFANA_PORT>`
- QuestDB Web Console: `http://127.0.0.1:<HOST_QUESTDB_HTTP_PORT>`
- Flink Web UI: `http://127.0.0.1:<HOST_FLINK_PORT>`

查看结果：

```bash
cat artifacts/signals.jsonl
cat artifacts/portfolio.jsonl
```

生成本地 synthetic fixture：

```bash
make generate-synthetic
```

回放 synthetic fixture：

```bash
make replay-synthetic
```

抓取链上样本到本地 fixture：

```bash
make capture-onchain
```

接 Binance 实时公开数据：

```bash
make binance
```

接 EVM 链上 swap 数据：

```bash
make onchain
```

停止基础设施：

```bash
make stop
```

彻底重置栈和本地运行产物：

```bash
make reset
```

## 运行说明

- 运行参数默认从 `config/development.yaml` 读取，Python source 和 shell 脚本共用同一份配置
- Kafka 对宿主机默认暴露为 `localhost:39092`
- 启动时会优先复用 `artifacts/ports.env` 中上次成功的端口；如果端口被占用，会自动向上扫描空闲端口
- 需要查看当前映射时运行 `make ports`
- 需要查看当前 YAML 配置映射时运行 `make config-show`
- Flink Web UI 地址由 `make ports` 输出中的 `HOST_FLINK_PORT` 决定
- 开发环境默认会在 `make dev` 时重建 QuestDB 分析表，并用 YAML 中的 retention 配置自动清理数据
- Flink SQL 作业定义在 `sql/market_features.sql`
- 示例数据覆盖 6 个 5 秒窗口，脚本默认消费 6 条特征和 6 条信号
- Python 依赖和锁文件都位于 `app/`
- 组合快照会额外写入 Kafka topic `portfolio_snapshots`
- Grafana 默认会自动加载 `Finance Pipeline` dashboard
- QuestDB 表结构会在启动时自动初始化；如果还没回放或接入实时数据，Grafana 会显示空图而不是报表不存在
- 推荐开发 workflow 是 `generate-synthetic` / `replay` / `replay-synthetic` / `capture-onchain`，真实 `make onchain` 只在需要时启用
- `make onchain` 与 `make capture-onchain` 当前按 Uniswap V2 风格 `Swap` 事件把链上成交映射为 `market_ticks`
- 常用入口都收在 `Makefile`

## 文档

- 设计说明见 `docs/architecture.md`
- 运行说明见 `docs/runbook.md`
- 数据源说明见 `docs/data-sources.md`
- Binance 接入手册见 `docs/binance-manual.md`

## 后续扩展方向

- 从现货 tick 扩展到 perp / options schema
- 在 Flink 中加入 order book imbalance、VWAP、rolling volatility
- 把 portfolio service 换成更接近真实的 execution + risk engine
- 增加 batch replay 和研究层，补 Spark / DuckDB / Ray
