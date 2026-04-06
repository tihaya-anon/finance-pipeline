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

- 本地开发 / dashboard 演示：Binance Spot `aggTrade`
- 回放测试：仓库自带 CSV 样例，保证环境稳定
- 后续扩展到衍生品：优先接 Bybit public trade / orderbook，再考虑 Binance Futures

## Alternative

如果后面更偏衍生品，Bybit 也很适合：

- 公共成交 topic：`publicTrade.{symbol}`
- 公共 WebSocket 主网现货地址：`wss://stream.bybit.com/v5/public/spot`

官方文档：

- Connect: https://bybit-exchange.github.io/docs/v5/ws/connect
- Public Trade: https://bybit-exchange.github.io/docs/v5/websocket/public/trade
