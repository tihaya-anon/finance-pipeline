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

## Layout

- `app/`: Python 子工程，`uv` 在这里管理依赖、入口和测试
- `sql/`: Flink SQL 作业
- `docker/`: Flink 镜像定制
- `scripts/`: 一键运行与基础设施辅助脚本
- `data/`: 样例输入数据
- `artifacts/`: 运行结果

## Design Choices

### 为什么先做 crypto replay

- 数据结构简单，方便先把流式系统打通
- 不依赖外部收费行情源
- 后续迁移到 perp 或 options 时，可以复用绝大部分 pipeline

### 为什么 Flink SQL 只保留简单窗口特征

- MVP 的目标是验证实时处理层是否可用
- 先用稳定的窗口聚合替代复杂特征，降低调试成本
- 后续可继续加 rolling volatility、VWAP、order book imbalance

### 为什么策略和组合层仍然保留在 Python

- 便于快速试错
- 逻辑清晰，和流式计算层解耦
- 后面可替换为更真实的 execution/risk service

### 为什么现在改成 QuestDB + Grafana

- 数据大屏是成熟需求，不需要自己维护 UI 服务
- Grafana 更适合长期的开发观测和演示
- QuestDB 对时序场景天然合适，接金融特征流成本低
- Redpanda Console 补上了 Kafka 层面的原始消息可视化
