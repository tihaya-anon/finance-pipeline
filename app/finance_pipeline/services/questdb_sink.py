from __future__ import annotations

import argparse
import socket
import time

from finance_pipeline.core.kafka_utils import build_consumer
from finance_pipeline.core.schemas import MarketFeature, PortfolioSnapshot, TradingSignal
from finance_pipeline.config.settings import SETTINGS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sink Kafka pipeline outputs into QuestDB over ILP/TCP.")
    parser.add_argument("--bootstrap-servers", default=SETTINGS.bootstrap_servers)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9009)
    parser.add_argument("--group-id", default="questdb-sink")
    parser.add_argument("--max-messages", type=int, default=0)
    parser.add_argument("--connect-retries", type=int, default=30)
    parser.add_argument("--connect-backoff-seconds", type=float, default=2.0)
    return parser.parse_args()


def escape_tag(value: str) -> str:
    return value.replace("\\", "\\\\").replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")


def escape_string_field(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def to_ilp_line(measurement: str, tags: dict[str, str], fields: dict[str, str]) -> str:
    tags_clause = ",".join(
        f"{key}={escape_tag(value)}"
        for key, value in tags.items()
        if value
    )
    fields_clause = ",".join(f"{key}={value}" for key, value in fields.items())
    ingestion_timestamp_ns = time.time_ns()
    return f"{measurement},{tags_clause} {fields_clause} {ingestion_timestamp_ns}\n"


def build_instrument_tags(symbol: str, venue: str, instrument_type: str, base_asset: str, quote_asset: str) -> dict[str, str]:
    return {
        "symbol": symbol,
        "venue": venue,
        "instrument_type": instrument_type,
        "base_asset": base_asset,
        "quote_asset": quote_asset,
    }


def build_feature_line(feature: MarketFeature) -> str:
    return to_ilp_line(
        "market_features",
        build_instrument_tags(
            feature.symbol,
            feature.venue,
            feature.instrument_type,
            feature.base_asset,
            feature.quote_asset,
        ),
        {
            "window_start": f'"{escape_string_field(feature.to_payload()["window_start"])}"',
            "window_end": f'"{escape_string_field(feature.to_payload()["window_end"])}"',
            "trade_count": f"{feature.trade_count}i",
            "avg_price": str(feature.avg_price),
            "vwap": str(feature.vwap),
            "high_price": str(feature.high_price),
            "low_price": str(feature.low_price),
            "open_price": str(feature.open_price),
            "close_price": str(feature.close_price),
            "high_low_range": str(feature.high_low_range),
            "total_quantity": str(feature.total_quantity),
            "notional_volume": str(feature.notional_volume),
            "buy_quantity": str(feature.buy_quantity),
            "sell_quantity": str(feature.sell_quantity),
            "volume_imbalance": str(feature.volume_imbalance),
            "price_volatility": str(feature.price_volatility),
            "price_return": str(feature.price_return),
        },
    )


def build_signal_line(signal: TradingSignal) -> str:
    payload = signal.to_payload()
    return to_ilp_line(
        "trade_signals",
        build_instrument_tags(
            signal.symbol,
            signal.venue,
            signal.instrument_type,
            signal.base_asset,
            signal.quote_asset,
        ),
        {
            "generated_at": f'"{escape_string_field(payload["generated_at"])}"',
            "window_end": f'"{escape_string_field(payload["window_end"])}"',
            "target_position": f"{signal.target_position}i",
            "target_position_size": str(signal.target_position_size),
            "reference_price": str(signal.reference_price),
            "price_return": str(signal.price_return),
            "reason": f'"{escape_string_field(signal.reason)}"',
        },
    )


def build_portfolio_line(snapshot: PortfolioSnapshot) -> str:
    payload = snapshot.to_payload()
    return to_ilp_line(
        "portfolio_snapshots",
        build_instrument_tags(
            snapshot.symbol,
            snapshot.venue,
            snapshot.instrument_type,
            snapshot.base_asset,
            snapshot.quote_asset,
        ),
        {
            "event_timestamp": f'"{escape_string_field(payload["timestamp"])}"',
            "action": f'"{escape_string_field(snapshot.action)}"',
            "fill_price": str(snapshot.fill_price),
            "target_position": f"{snapshot.target_position}i",
            "current_position": f"{snapshot.current_position}i",
            "target_position_size": str(snapshot.target_position_size),
            "current_position_size": str(snapshot.current_position_size),
            "cash": str(snapshot.cash),
            "equity": str(snapshot.equity),
        },
    )


def main() -> None:
    args = parse_args()
    consumer = build_consumer(
        [SETTINGS.features_topic, SETTINGS.signals_topic, SETTINGS.portfolio_topic],
        bootstrap_servers=args.bootstrap_servers,
        group_id=args.group_id,
        consumer_timeout_ms=SETTINGS.consumer_timeout_ms,
    )
    connection: socket.socket | None = None
    processed = 0

    try:
        for attempt in range(1, args.connect_retries + 1):
            try:
                connection = socket.create_connection((args.host, args.port), timeout=10)
                break
            except OSError as exc:
                if attempt == args.connect_retries:
                    raise
                print(
                    f"questdb sink connect retry {attempt}/{args.connect_retries}: "
                    f"{exc}; sleeping {args.connect_backoff_seconds:.1f}s"
                )
                time.sleep(args.connect_backoff_seconds)

        assert connection is not None

        while args.max_messages <= 0 or processed < args.max_messages:
            records = consumer.poll(timeout_ms=SETTINGS.consumer_timeout_ms)
            if not records:
                continue

            for topic_partition_records in records.values():
                for record in topic_partition_records:
                    if record.topic == SETTINGS.features_topic:
                        line = build_feature_line(MarketFeature.from_payload(record.value))
                    elif record.topic == SETTINGS.signals_topic:
                        line = build_signal_line(TradingSignal.from_payload(record.value))
                    elif record.topic == SETTINGS.portfolio_topic:
                        line = build_portfolio_line(PortfolioSnapshot.from_payload(record.value))
                    else:
                        continue

                    connection.sendall(line.encode("utf-8"))
                    processed += 1
                    print(f"questdb sink {processed}: wrote {record.topic}")
                    if args.max_messages > 0 and processed >= args.max_messages:
                        break
                if args.max_messages > 0 and processed >= args.max_messages:
                    break
    finally:
        if connection is not None:
            connection.close()
        consumer.close()


if __name__ == "__main__":
    main()
