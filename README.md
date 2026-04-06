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
app/                    Python 子工程根目录
app/finance_pipeline/   Python package
app/tests/              Python 单测
data/sample/            示例行情
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
uv --directory app sync --group dev
uv --directory app run pytest
```

启动完整 MVP：

```bash
./scripts/run_mvp.sh
```

启动常驻开发栈和可视化：

```bash
./scripts/start_dev_stack.sh
```

常用入口：

- Redpanda Console: `http://127.0.0.1:8080`
- Grafana: `http://127.0.0.1:3000`
- QuestDB Web Console: `http://127.0.0.1:9000`

查看结果：

```bash
cat artifacts/signals.jsonl
cat artifacts/portfolio.jsonl
```

接 Binance 实时公开数据：

```bash
uv --directory app run stream-binance
```

停止基础设施：

```bash
docker compose down
```

## 运行说明

- Kafka 对宿主机默认暴露为 `localhost:39092`
- 如果端口冲突，启动前设置 `HOST_KAFKA_PORT=49092` 这类环境变量即可
- Flink Web UI 为 `http://localhost:8081`
- Flink SQL 作业定义在 `sql/market_features.sql`
- 示例数据覆盖 6 个 5 秒窗口，脚本默认消费 6 条特征和 6 条信号
- Python 依赖和锁文件都位于 `app/`
- 组合快照会额外写入 Kafka topic `portfolio_snapshots`
- Grafana 默认会自动加载 `Finance Pipeline` dashboard

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
