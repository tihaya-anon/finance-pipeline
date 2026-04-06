# Runbook

## Install

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
./scripts/start_dev_stack.sh
```

这个模式会：

- 启动 Redpanda 和 Flink
- 启动 Redpanda Console、QuestDB、Grafana
- 自动选择可用宿主机端口并保存到 `artifacts/ports.env`
- 初始化 QuestDB dashboard 依赖表结构，并在开发模式下重建分析表
- 提交 Flink SQL 作业
- 常驻启动 strategy / portfolio / questdb-sink 服务

可视化地址：

- 运行 `make ports`
- Redpanda Console: `http://127.0.0.1:<HOST_CONSOLE_PORT>`
- Grafana: `http://127.0.0.1:<HOST_GRAFANA_PORT>`
- QuestDB: `http://127.0.0.1:<HOST_QUESTDB_HTTP_PORT>`
- Flink UI: `http://127.0.0.1:<HOST_FLINK_PORT>`

推样例数据：

```bash
uv --directory app run replay-market --speedup 50
```

推 Binance 实时数据：

```bash
uv --directory app run stream-binance
```

默认候选端口：

- Kafka: `localhost:39092`
- Flink UI: `http://localhost:${HOST_FLINK_PORT:-8081}`
- Redpanda Console: `localhost:${HOST_CONSOLE_PORT:-8080}`
- QuestDB HTTP: `localhost:${HOST_QUESTDB_HTTP_PORT:-9000}`
- QuestDB ILP: `localhost:${HOST_QUESTDB_ILP_PORT:-9009}`
- QuestDB PGWire: `localhost:${HOST_QUESTDB_PG_PORT:-8812}`
- Grafana: `localhost:${HOST_GRAFANA_PORT:-3000}`

如果端口冲突：

```bash
HOST_KAFKA_PORT=49092 \
HOST_CONSOLE_PORT=18080 \
HOST_QUESTDB_HTTP_PORT=19000 \
HOST_QUESTDB_ILP_PORT=19009 \
HOST_QUESTDB_PG_PORT=18812 \
HOST_GRAFANA_PORT=13000 \
HOST_FLINK_PORT=18081 \
./scripts/start_dev_stack.sh
```

不传环境变量时，脚本会自动向上扫描空闲端口；成功启动后可用 `make ports` 查看最终映射。
开发环境还会自动清理数据：

- Redpanda topics 默认保留 `1` 小时，由 `DEV_TOPIC_RETENTION_MS` 控制
- QuestDB 分析表按 `HOUR` 分区，默认保留 `6` 小时，由 `DEV_QUESTDB_TTL` 控制
- 每次 `make dev` 会重建 QuestDB 分析表，避免开发过程无限积累旧数据

## Outputs

运行完成后检查：

- `artifacts/flink-submit.log`
- `artifacts/signals.jsonl`
- `artifacts/portfolio.jsonl`

## Shutdown

```bash
./scripts/stop_stack.sh
```

## Full Reset

```bash
./scripts/reset_stack.sh
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
