# Data Sources

## Default Choice

开发默认选 Binance Spot 的公共行情：

- 实时流：`<symbol>@aggTrade`
- 历史补数：`GET /api/v3/aggTrades`

理由：

- 公开、免费、无需鉴权
- 文档成熟，社区样例多
- `aggTrade` 天然适合当前 MVP 的 tick/成交流 schema
- 后续如果想做 order book，也可以直接接 Binance depth stream

## Why Binance First

Binance 官方文档说明：

- Spot WebSocket 基础地址是 `wss://stream.binance.com:9443` 或 `:443`
- 也可使用只提供市场数据的 `wss://data-stream.binance.vision`
- `aggTrade` 是实时推送
- 历史 `GET /api/v3/aggTrades` 支持按时间或 `fromId` 回补

官方文档：

- WebSocket Streams: https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams
- Market Data Endpoints: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints

## Recommended Runtime Split

- 本地开发 / dashboard 演示：优先使用本地 fixture 和 synthetic data
- 回放测试：仓库自带 CSV 样例或 `make generate-synthetic` 产出的 fixture
- 真实链上采样：`make capture-onchain` 抓一小段样本再本地回放
- 后续扩展到衍生品：优先接 Bybit public trade / orderbook，再考虑 Binance Futures

## Alternative

如果后面更偏衍生品，Bybit 也很适合：

- 公共成交 topic：`publicTrade.{symbol}`
- 公共 WebSocket 主网现货地址：`wss://stream.bybit.com/v5/public/spot`

官方文档：

- Connect: https://bybit-exchange.github.io/docs/v5/ws/connect
- Public Trade: https://bybit-exchange.github.io/docs/v5/websocket/public/trade

## On-Chain Next Step

仓库现在也支持直接接 EVM AMM `Swap` 日志：

- 入口：`make onchain`
- 采样入口：`make capture-onchain`
- 当前解码模型：Uniswap V2 风格 pair `Swap` 事件
- 输出方式：把链上 swap 统一映射成现有 `market_ticks` schema，后续 Flink / strategy / QuestDB / Grafana 复用原链路
- 推荐工作流：先抓样本落到 `data/fixtures/onchain/`，开发时再用 `make replay` 或专门 replay 命令重放

最小配置：

```bash
make onchain \
  EVM_WS_URL=wss://your-node.example/ws \
  EVM_HTTP_URL=https://your-node.example/http \
  EVM_PAIR_ADDRESS=0xYourPairAddress \
  EVM_BASE_SYMBOL=ETH \
  EVM_QUOTE_SYMBOL=USDC \
  EVM_BASE_DECIMALS=18 \
  EVM_QUOTE_DECIMALS=6
```

当前限制：

- 只支持单个 pair
- 只支持 Uniswap V2 风格 `Swap(address,uint256,uint256,uint256,uint256,address)`
- 价格默认按 `token0/token1` 中的 `base/quote` 方向计算

## Config Management

所有 source 默认参数现在统一放在 `config/development.yaml`：

- `sources.replay`: 默认回放 fixture 与速度
- `sources.synthetic`: synthetic fixture 输出路径与生成参数
- `sources.binance`: Binance 公共流地址
- `sources.onchain`: 链上 WS/HTTP endpoint、pair、symbol、decimals、capture 输出路径
