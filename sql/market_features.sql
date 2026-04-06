SET 'execution.runtime-mode' = 'streaming';

CREATE TABLE market_ticks (
  symbol STRING,
  event_time TIMESTAMP_LTZ(3),
  price DOUBLE,
  quantity DOUBLE,
  side STRING,
  WATERMARK FOR event_time AS event_time - INTERVAL '1' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'market_ticks',
  'properties.bootstrap.servers' = 'redpanda:9092',
  'properties.group.id' = 'flink-market-features',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'json',
  'json.timestamp-format.standard' = 'ISO-8601'
);

CREATE TABLE market_features (
  symbol STRING,
  window_start TIMESTAMP_LTZ(3),
  window_end TIMESTAMP_LTZ(3),
  trade_count BIGINT,
  avg_price DOUBLE,
  open_price DOUBLE,
  close_price DOUBLE,
  total_quantity DOUBLE,
  price_return DOUBLE
) WITH (
  'connector' = 'kafka',
  'topic' = 'market_features',
  'properties.bootstrap.servers' = 'redpanda:9092',
  'format' = 'json',
  'json.timestamp-format.standard' = 'ISO-8601'
);

INSERT INTO market_features
SELECT
  symbol,
  window_start,
  window_end,
  COUNT(*) AS trade_count,
  ROUND(AVG(price), 6) AS avg_price,
  MIN(price) AS open_price,
  MAX(price) AS close_price,
  ROUND(SUM(quantity), 6) AS total_quantity,
  ROUND(
    (MAX(price) - MIN(price)) / NULLIF(MIN(price), 0),
    6
  ) AS price_return
FROM TABLE(
  TUMBLE(TABLE market_ticks, DESCRIPTOR(event_time), INTERVAL '5' SECONDS)
)
GROUP BY symbol, window_start, window_end;
