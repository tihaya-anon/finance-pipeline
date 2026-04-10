# Architecture

## MVP Scope

这个项目只做一件事：把量化数据链路最小闭环跑通，而不是一开始就做复杂研究平台。

当前链路：

1. `replay-market` 把样例 tick 数据回放到 `market_ticks`
2. Flink SQL 对 `market_ticks` 做 5 秒窗口聚合，写入 `market_features`
3. `strategy-service` 消费特征并生成信号，写入 `trade_signals`
4. `portfolio-service` 消费信号并产出账户快照，写入 `portfolio_snapshots`
5. `questdb-sink` 消费三个结果 topic 并写入 QuestDB
6. Grafana 从 QuestDB 读取时序数据做大盘展示
7. Redpanda Console 用于直接查看 topic、消息和 consumer 状态

统一消息 schema 现在不仅保留 `symbol`，还携带以下 instrument metadata：

- `venue`
- `instrument_type`
- `base_asset`
- `quote_asset`

这样相同 `symbol` 来自不同 venue 或不同 instrument type 时，可以在 Kafka key、组合状态和 QuestDB tags 上保持隔离。

开发态额外约定：

- source 层优先使用本地 fixture 和 synthetic data，减少对外部 endpoint 的依赖
- 实时链上 source 主要用于抓一小段样本，再转回本地 fixture
- 运行参数统一收敛到 `config/development.yaml`

## Layout

- `app/`: Python 子工程，`uv` 在这里管理依赖、入口和测试
- `config/`: YAML 配置，驱动 source 默认值、端口和保留策略
- `sql/`: Flink SQL 作业
- `docker/`: Flink 镜像定制
- `scripts/`: 一键运行与基础设施辅助脚本
- `data/`: 样例输入数据、链上采样 fixture、synthetic fixture
- `artifacts/`: 运行结果

## Design Choices

### 为什么先做 crypto replay

- 数据结构简单，方便先把流式系统打通
- 不依赖外部收费行情源
- 后续迁移到 perp 或 options 时，可以复用绝大部分 pipeline

### 为什么先扩 instrument metadata 再做 risk

- 如果 Kafka 消息仍然只靠 `symbol` 标识，同名标的跨 venue 时会在状态和分区上碰撞
- 先把 instrument 维度补齐，后面的 sizing、exposure、risk limit 才有稳定主键
- QuestDB 和 Grafana 也能直接按 `venue` / `instrument_type` 切片，而不是后补迁移

### 为什么 Flink SQL 先做窗口级特征

- 先把 5 秒窗口内的 VWAP、波动率、成交量不平衡跑通，能覆盖一批最基础的盘中信号输入
- 这类特征足够轻量，适合在 MVP 阶段快速验证 Kafka -> Flink -> Python -> QuestDB 全链路
- 后续再继续往跨窗口、跨标的和 order book 特征扩展

### 为什么策略和组合层仍然保留在 Python

- 便于快速试错
- 逻辑清晰，和流式计算层解耦
- 后面可替换为更真实的 execution/risk service

### 为什么现在改成 QuestDB + Grafana

- 数据大屏是成熟需求，不需要自己维护 UI 服务
- Grafana 更适合长期的开发观测和演示
- QuestDB 对时序场景天然合适，接金融特征流成本低
- Redpanda Console 补上了 Kafka 层面的原始消息可视化
