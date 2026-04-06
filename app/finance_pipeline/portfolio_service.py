from __future__ import annotations

import argparse
import json
from pathlib import Path

from finance_pipeline.kafka_utils import build_consumer, build_producer
from finance_pipeline.portfolio import SimplePortfolio
from finance_pipeline.schemas import TradingSignal
from finance_pipeline.settings import SETTINGS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Consume trading signals and update a simple portfolio.")
    parser.add_argument("--bootstrap-servers", default=SETTINGS.bootstrap_servers)
    parser.add_argument("--source-topic", default=SETTINGS.signals_topic)
    parser.add_argument("--target-topic", default=SETTINGS.portfolio_topic)
    parser.add_argument("--group-id", default="portfolio-service")
    parser.add_argument("--max-messages", type=int, default=6)
    parser.add_argument("--output", default=str(SETTINGS.artifacts_dir / "portfolio.jsonl"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    consumer = build_consumer(
        args.source_topic,
        bootstrap_servers=args.bootstrap_servers,
        group_id=args.group_id,
        consumer_timeout_ms=SETTINGS.consumer_timeout_ms,
    )
    producer = build_producer(args.bootstrap_servers)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    portfolio = SimplePortfolio()
    processed = 0

    try:
        with output_path.open("w", encoding="utf-8") as handle:
            while args.max_messages <= 0 or processed < args.max_messages:
                records = consumer.poll(timeout_ms=SETTINGS.consumer_timeout_ms)
                if not records:
                    continue

                for topic_partition_records in records.values():
                    for record in topic_partition_records:
                        # This service is intentionally simple: one signal updates one
                        # in-memory portfolio state and appends one snapshot.
                        signal = TradingSignal.from_payload(record.value)
                        snapshot = portfolio.apply_signal(signal)
                        producer.send(args.target_topic, key=snapshot.symbol, value=snapshot.to_payload()).get(timeout=10)
                        handle.write(json.dumps(snapshot.to_payload(), separators=(",", ":")) + "\n")
                        handle.flush()
                        processed += 1
                        print(
                            f"portfolio {processed}: {snapshot.symbol} position={snapshot.current_position} "
                            f"cash={snapshot.cash:.2f} equity={snapshot.equity:.2f}"
                        )
                        if args.max_messages > 0 and processed >= args.max_messages:
                            break
                    if args.max_messages > 0 and processed >= args.max_messages:
                        break
    finally:
        producer.flush()
        producer.close()
        consumer.close()


if __name__ == "__main__":
    main()
