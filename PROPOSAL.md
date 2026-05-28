# Finance Pipeline Proposal

## Objective

本项目的目标不是做一个泛化的“量化什么都能装”的 demo，而是沿着一条明确主线推进：

1. 先构建面向标的行情的流式研究骨架
2. 重点研究未来实现波动率 `realized volatility` 的预测
3. 再把标的波动率预测和期权隐含波动率 `implied volatility` 连接起来
4. 最终形成可用于波动率交易、相对价值分析和期权定价辅助的研究平台

核心问题可以概括为：

> 能否利用标的行情、成交、微观结构与跨窗口特征，稳定预测未来波动率，并与期权市场当前定价出来的隐含波动率形成可交易偏差？

## Why This Direction

相比直接做传统股票 alpha，这条路线更适合当前仓库，也更容易自然扩展到期权。

原因有三点：

1. 当前系统已经具备流处理骨架，天然适合做高频和分钟级波动率特征
2. 波动率研究同时连接标的市场和期权市场，主线比“纯股票因子”更统一
3. 后续扩展到 IV surface、skew、term structure 时，不需要推翻已有架构

需要明确的是：

- 标的因子不能“直接算出” IV
- IV 是期权市场价格隐含出来的未来波动率定价结果
- 标的因子更适合预测未来实现波动率 `future realized vol`
- 真正可交易的是 `IV` 和模型预测波动率之间的偏差，而不是把两者混为一谈

## Research Thesis

研究假设如下：

1. 标的的短中期未来实现波动率不是完全随机的
2. 成交量、收益率路径、波动聚集、盘口失衡、跳跃代理变量等特征，对未来波动率有解释力
3. 期权市场的 IV 提供了市场定价视角，但其中包含风险溢价、供需和尾部风险补偿
4. 因此，`IV - expected future realized vol` 可以作为一个有研究价值的 spread

这个 spread 后续可以支持：

- 买入或卖出波动率
- IV vs RV 相对价值策略
- 不同期限之间的 term structure 策略
- 不同 moneyness 之间的 skew 策略

## System Scope

系统按两层资产对象推进。

### Layer 1: Underlying Volatility Engine

先围绕标的现货或永续合约建立研究能力：

- ticks / trades / bars ingestion
- stream feature computation
- future realized volatility label generation
- factor evaluation and replay

这一层先不依赖期权链，也能单独形成完整研究闭环。

### Layer 2: Option Volatility Analytics

在标的波动率预测稳定之后，再接入期权市场：

- option quote / trade ingestion
- per-strike / per-expiry IV calculation
- ATM IV extraction
- skew / term structure / surface snapshots
- IV vs forecast RV comparison

这一层的目标不是一开始就做完整做市或复杂 Greeks 风控，而是先把波动率定价和相对价值链路打通。

## Data Strategy

考虑到真实期权实时数据获取成本较高，数据策略按可获得性分层：

### Phase A: Replay-First

优先使用本地样本和合成数据：

- 历史 tick replay
- synthetic volatility regimes
- 可复现的事件驱动测试

### Phase B: Live Underlying Streams

接入开放程度更高的实时标的数据流：

- crypto spot / perp
- 后续可替换为股票或 ETF 行情

### Phase C: Option Data

在底层稳定后引入期权数据：

- 历史 option chain
- 延迟或 replay 的 option quote/trade
- 条件允许时接实时期权行情

## Core Metrics

这个项目的核心不是先追逐收益率，而是先验证研究对象和系统能力。

优先指标包括：

- future realized vol prediction error
- correlation / rank IC of volatility factors
- regime stability across replay windows
- IV minus forecast RV spread behavior
- signal persistence after fees and slippage assumptions

后续策略层再看：

- Sharpe
- drawdown
- turnover
- vega exposure
- tail risk under jump scenarios

## Architecture Principles

### 1. Stream-First, But Not Stream-Only

Flink 负责实时特征和在线聚合，batch 侧负责离线研究和评估。项目不把所有问题硬塞进流计算。

### 2. Unified Instrument Schema

底层 schema 必须从一开始支持：

- venue
- instrument_type
- base_asset
- quote_asset
- symbol

这样才能平滑扩展到现货、perp、股票、ETF、期权。

### 3. Replay Is a First-Class Capability

replay 不是辅助脚本，而是验证研究和模拟生产行为的核心能力。

### 4. Separate Underlying and Option Layers

标的行情特征、未来波动率标签、期权 IV 计算、期权策略信号需要逻辑分层，避免过早耦合。

## Proposed Roadmap

### Phase 1: Multi-Asset Underlying Schema

打稳底层数据模型：

- multi-asset schema
- feature topic normalization
- instrument-aware keys and storage

### Phase 2: Volatility Feature Engine

围绕未来波动率预测完善特征：

- rolling realized vol
- return dispersion
- jump proxies
- buy/sell imbalance
- volume and liquidity features
- correlation-ready outputs

### Phase 3: Vol Forecasting and Evaluation

引入更明确的研究闭环：

- define forward vol horizons
- generate labels
- evaluate factors
- compare replay regimes

### Phase 4: Strategy / Portfolio / Risk

在预测能力形成后，再做策略层：

- volatility signal abstraction
- position sizing
- exposure controls
- scenario-based risk hooks

### Phase 5: Option IV Integration

接入期权链并形成波动率相对价值能力：

- IV calculation
- ATM IV time series
- term structure
- skew features
- IV vs forecast RV spread analytics

### Phase 6: Volatility Trading Research

最终研究策略包括：

- long/short vol
- calendar spread
- skew spread
- event-driven volatility dislocations

## Near-Term Build Order

当前最合理的近程顺序是：

1. 先把标的流式特征做扎实
2. 明确定义 future realized vol 的预测 horizon
3. 做一批基础波动率因子
4. 先验证这些因子在 replay 和 synthetic regimes 下是否稳定
5. 再接期权 IV，不要一开始就直接冲 surface 和 Greeks

## Non-Goals For Now

当前阶段不优先做：

- 超高频撮合或 execution engine
- 完整做市系统
- 全量 Greeks 风控平台
- 一上来就覆盖完整股票和期权生产数据接入
- 没有标的预测能力前就直接做复杂期权组合策略

## Summary

本项目的核心主线是：

> 用标的因子预测未来波动率，再和期权市场隐含波动率连接起来，研究可交易的波动率偏差。

这条路线兼顾了：

- 当前仓库已有的流处理能力
- 后续扩展到期权和波动率曲面的空间
- replay-first 的现实开发方式
- 从 underlying 到 derivative 的自然升级路径
