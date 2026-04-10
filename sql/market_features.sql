SET 'execution.runtime-mode' = 'streaming';

CREATE TABLE market_ticks (
  symbol STRING,
  venue STRING,
  instrument_type STRING,
  base_asset STRING,
  quote_asset STRING,
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
  venue STRING,
  instrument_type STRING,
  base_asset STRING,
  quote_asset STRING,
  window_start TIMESTAMP_LTZ(3),
  window_end TIMESTAMP_LTZ(3),
  trade_count BIGINT,
  avg_price DOUBLE,
  vwap DOUBLE,
  open_price DOUBLE,
  close_price DOUBLE,
  total_quantity DOUBLE,
  buy_quantity DOUBLE,
  sell_quantity DOUBLE,
  volume_imbalance DOUBLE,
  price_volatility DOUBLE,
  price_return DOUBLE
) WITH (
  'connector' = 'kafka',
  'topic' = 'market_features',
  'properties.bootstrap.servers' = 'redpanda:9092',
  'format' = 'json',
  'json.timestamp-format.standard' = 'ISO-8601'
);

CREATE TEMPORARY VIEW base_windowed_ticks AS
SELECT
  symbol,
  venue,
  instrument_type,
  base_asset,
  quote_asset,
  window_start,
  window_end,
  event_time,
  price,
  quantity,
  side
FROM TABLE(
  TUMBLE(TABLE market_ticks, DESCRIPTOR(event_time), INTERVAL '5' SECONDS)
);

CREATE TEMPORARY VIEW open_ticks AS
SELECT
  symbol,
  venue,
  instrument_type,
  base_asset,
  quote_asset,
  window_start,
  window_end,
  price AS open_price
FROM (
  SELECT
    symbol,
    venue,
    instrument_type,
    base_asset,
    quote_asset,
    window_start,
    window_end,
    price,
    ROW_NUMBER() OVER (
      PARTITION BY venue, instrument_type, symbol, base_asset, quote_asset, window_start, window_end
      ORDER BY event_time ASC, price ASC
    ) AS row_num
  FROM base_windowed_ticks
)
WHERE row_num = 1;

CREATE TEMPORARY VIEW close_ticks AS
SELECT
  symbol,
  venue,
  instrument_type,
  base_asset,
  quote_asset,
  window_start,
  window_end,
  price AS close_price
FROM (
  SELECT
    symbol,
    venue,
    instrument_type,
    base_asset,
    quote_asset,
    window_start,
    window_end,
    price,
    ROW_NUMBER() OVER (
      PARTITION BY venue, instrument_type, symbol, base_asset, quote_asset, window_start, window_end
      ORDER BY event_time DESC, price DESC
    ) AS row_num
  FROM base_windowed_ticks
)
WHERE row_num = 1;

CREATE TEMPORARY VIEW feature_aggregates AS
SELECT
  symbol,
  venue,
  instrument_type,
  base_asset,
  quote_asset,
  window_start,
  window_end,
  COUNT(*) AS trade_count,
  ROUND(AVG(price), 6) AS avg_price,
  ROUND(SUM(price * quantity) / NULLIF(SUM(quantity), 0), 6) AS vwap,
  ROUND(SUM(quantity), 6) AS total_quantity,
  ROUND(SUM(CASE WHEN side = 'buy' THEN quantity ELSE 0.0 END), 6) AS buy_quantity,
  ROUND(SUM(CASE WHEN side = 'sell' THEN quantity ELSE 0.0 END), 6) AS sell_quantity,
  ROUND(
    (
      SUM(CASE WHEN side = 'buy' THEN quantity ELSE 0.0 END) -
      SUM(CASE WHEN side = 'sell' THEN quantity ELSE 0.0 END)
    ) / NULLIF(SUM(quantity), 0),
    6
  ) AS volume_imbalance,
  ROUND(
    STDDEV_POP(price) / NULLIF(AVG(price), 0),
    6
  ) AS price_volatility
FROM base_windowed_ticks
GROUP BY
  symbol,
  venue,
  instrument_type,
  base_asset,
  quote_asset,
  window_start,
  window_end;

INSERT INTO market_features
SELECT
  stats.symbol,
  stats.venue,
  stats.instrument_type,
  stats.base_asset,
  stats.quote_asset,
  stats.window_start,
  stats.window_end,
  stats.trade_count,
  stats.avg_price,
  stats.vwap,
  open_ticks.open_price,
  close_ticks.close_price,
  stats.total_quantity,
  stats.buy_quantity,
  stats.sell_quantity,
  stats.volume_imbalance,
  stats.price_volatility,
  ROUND(
    (
      close_ticks.close_price - open_ticks.open_price
    ) / NULLIF(open_ticks.open_price, 0),
    6
  ) AS price_return
FROM feature_aggregates AS stats
JOIN open_ticks
  ON stats.symbol = open_ticks.symbol
 AND stats.venue = open_ticks.venue
 AND stats.instrument_type = open_ticks.instrument_type
 AND stats.base_asset = open_ticks.base_asset
 AND stats.quote_asset = open_ticks.quote_asset
 AND stats.window_start = open_ticks.window_start
 AND stats.window_end = open_ticks.window_end
JOIN close_ticks
  ON stats.symbol = close_ticks.symbol
 AND stats.venue = close_ticks.venue
 AND stats.instrument_type = close_ticks.instrument_type
 AND stats.base_asset = close_ticks.base_asset
 AND stats.quote_asset = close_ticks.quote_asset
 AND stats.window_start = close_ticks.window_start
 AND stats.window_end = close_ticks.window_end;
