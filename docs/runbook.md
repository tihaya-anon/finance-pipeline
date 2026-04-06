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

## Known Tradeoffs

- 当前策略阈值较高，样例数据默认多为 `flat`
- 最后一个窗口是否输出取决于事件时间与 watermark 推进
- Flink 特征目前只使用简单聚合，不包含盘口或波动率细节
