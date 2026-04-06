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
- 提交 Flink SQL 作业
- 常驻启动 strategy / portfolio / questdb-sink 服务

可视化地址：

- Redpanda Console: `http://127.0.0.1:8080`
- Grafana: `http://127.0.0.1:3000`
- QuestDB: `http://127.0.0.1:9000`

推样例数据：

```bash
uv --directory app run replay-market --speedup 50
```

推 Binance 实时数据：

```bash
uv --directory app run stream-binance
```

默认暴露：

- Kafka: `localhost:39092`
- Flink UI: `http://localhost:8081`

如果 `39092` 冲突：

```bash
HOST_KAFKA_PORT=49092 ./scripts/run_mvp.sh
```

## Outputs

运行完成后检查：

- `artifacts/flink-submit.log`
- `artifacts/signals.jsonl`
- `artifacts/portfolio.jsonl`

## Shutdown

```bash
docker compose down
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
