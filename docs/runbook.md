# Runbook

## Install

```bash
make install
```

或直接：

```bash
uv --directory app sync --group dev
```

## Unit Tests

```bash
uv --directory app run pytest
```

## Run MVP

```bash
./scripts/run_mvp.sh
```

## Start Long-Running Dev Mode

```bash
make dev
```

这个模式会：

- 启动 Redpanda 和 Flink
- 启动 Redpanda Console、QuestDB、Grafana
- 从 `config/development.yaml` 加载运行参数
- 自动选择可用宿主机端口并保存到 `artifacts/ports.env`
- 初始化 QuestDB dashboard 依赖表结构，并在开发模式下重建分析表
- 提交 Flink SQL 作业
- 常驻启动 strategy / portfolio / questdb-sink 服务

可视化地址：

- 运行 `make net`
- Redpanda Console: `http://127.0.0.1:<HOST_CONSOLE_PORT>`
- Grafana: `http://127.0.0.1:<HOST_GRAFANA_PORT>`
- QuestDB: `http://127.0.0.1:<HOST_QUESTDB_HTTP_PORT>`
- Flink UI: `http://127.0.0.1:<HOST_FLINK_PORT>`

推样例数据：

```bash
make replay
```

`make replay` 会把 fixture 时间平移到当前时间附近，所以 Grafana 默认 `now-15m` 视图能直接看到新数据。

生成 synthetic fixture：

```bash
make generate-synthetic
```

回放 synthetic fixture：

```bash
make replay-synthetic
```

抓取链上 fixture：

```bash
make capture-onchain
```

推 Binance 实时数据：

```bash
make binance
```

推 EVM 链上实时 swap：

```bash
make onchain
```

默认候选端口：

- Kafka: `localhost:39092`
- Flink UI: `http://localhost:${HOST_FLINK_PORT:-8081}`
- Redpanda Console: `localhost:${HOST_CONSOLE_PORT:-8080}`
- QuestDB HTTP: `localhost:${HOST_QUESTDB_HTTP_PORT:-9000}`
- QuestDB ILP: `localhost:${HOST_QUESTDB_ILP_PORT:-9009}`
- QuestDB PGWire: `localhost:${HOST_QUESTDB_PG_PORT:-8812}`
- Grafana: `localhost:${HOST_GRAFANA_PORT:-3000}`

不修改命令行参数时，脚本会直接读取 `config/development.yaml`；成功启动后可用 `make config-show` 与 `make net` 查看最终配置和实际网络接口。
开发环境还会自动清理数据：

- Redpanda topics 默认保留 `1` 小时，由 YAML 中 `retention.topic_retention_ms` 控制
- QuestDB 分析表按 `HOUR` 分区，默认保留 `6` 小时，由 YAML 中 `retention.questdb_ttl` 控制
- 每次 `make dev` 会重建 QuestDB 分析表，避免开发过程无限积累旧数据

## Outputs

运行完成后检查：

- `artifacts/flink-submit.log`
- `artifacts/signals.jsonl`
- `artifacts/portfolio.jsonl`

## Shutdown

```bash
make stop
```

## Full Reset

```bash
make reset
```

如果还启动了本地后台 Python 服务：

```bash
pkill -f "uv --directory app run strategy-service"
pkill -f "uv --directory app run portfolio-service"
pkill -f "uv --directory app run questdb-sink"
```

## Data Retention

Kafka/Redpanda 原生支持 retention，不需要额外写应用层清理器。

开发环境里可直接调 topic 保留时间：

```bash
./scripts/apply_topic_retention.sh 3600000
```

上面示例表示保留 1 小时。

如果要彻底清空开发数据：

```bash
./scripts/reset_dev_data.sh
```

## Known Tradeoffs

- 当前策略阈值较高，样例数据默认多为 `flat`
- 最后一个窗口是否输出取决于事件时间与 watermark 推进
- Flink 特征目前只使用简单聚合，不包含盘口或波动率细节
- 当前推荐开发流是 fixture-first：优先用本地样本和 synthetic 数据复现问题，再按需接真实实时源
