# Binance 接入手册

## 目标

把 Binance 公共实时成交流接入当前开发栈，并在：

- Redpanda Console 中看到原始消息
- Grafana 中看到特征、信号和组合变化

## 官方文档

- WebSocket Streams: https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams
- Market Data Endpoints: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints

当前项目默认使用：

- 实时源：`wss://data-stream.binance.vision/ws/btcusdt@aggTrade`

## 一次性启动开发栈

```bash
./scripts/dev/start_dev_stack.sh
```

启动后可打开：

- Redpanda Console: `http://127.0.0.1:8080`
- Grafana: `http://127.0.0.1:3000`
- QuestDB: `http://127.0.0.1:9000`

## 推送 Binance 实时数据

默认 `BTCUSDT`：

```bash
uv --directory app run stream-binance
```

自定义 stream URL：

```bash
uv --directory app run stream-binance \
  --stream-url wss://data-stream.binance.vision/ws/ethusdt@aggTrade
```

## 观测路径

### 1. 看原始数据是否进 Kafka

打开 Redpanda Console：

- 查看 topic `market_ticks`
- 新消息会持续进入

### 2. 看 Flink 是否在产出特征

打开：

- Flink UI: `http://127.0.0.1:8081`

确认 `market_features` 相关 job 处于 `RUNNING`。

### 3. 看 Grafana 大屏是否更新

打开 Grafana 默认 dashboard：

- `Finance Pipeline`

会看到：

- 平均价格
- 窗口收益率
- 成交量
- 权益曲线
- 最近信号表

## 常见问题

### 1. Grafana 没数据

先检查：

- `questdb-sink` 是否在运行
- `market_features` / `trade_signals` / `portfolio_snapshots` 是否有消息
- Grafana 时间范围是否是最近 15 分钟

### 2. Binance 连不上

常见原因：

- 网络限制
- WSL 或本机代理配置
- Binance 公共域名被运营商或本地网络限流

可先用样例 replay 验证系统本身：

```bash
uv --directory app run replay-market --speedup 50
```

### 3. 想切到别的交易对

直接换 stream URL 即可，例如：

```bash
wss://data-stream.binance.vision/ws/solusdt@aggTrade
```

## 建议

开发阶段建议并行使用两种数据：

- replay：保证可重复调试
- Binance live：观察实时视觉效果和系统稳定性
