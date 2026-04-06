from __future__ import annotations

import argparse
import json
from pathlib import Path

from finance_pipeline.kafka_utils import build_consumer, build_producer
from finance_pipeline.schemas import MarketFeature
from finance_pipeline.settings import SETTINGS
from finance_pipeline.strategy import generate_signal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Consume market features and publish trading signals.")
    parser.add_argument("--bootstrap-servers", default=SETTINGS.bootstrap_servers)
    parser.add_argument("--source-topic", default=SETTINGS.features_topic)
    parser.add_argument("--target-topic", default=SETTINGS.signals_topic)
    parser.add_argument("--group-id", default="strategy-service")
    parser.add_argument("--threshold", type=float, default=0.001)
    parser.add_argument("--max-messages", type=int, default=6)
    parser.add_argument("--output", default=str(SETTINGS.artifacts_dir / "signals.jsonl"))
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

    processed = 0

    try:
        with output_path.open("w", encoding="utf-8") as handle:
            while processed < args.max_messages:
                records = consumer.poll(timeout_ms=SETTINGS.consumer_timeout_ms)
                if not records:
                    continue

                for topic_partition_records in records.values():
                    for record in topic_partition_records:
                        # Persist every derived signal so the replay has a durable audit trail.
                        feature = MarketFeature.from_payload(record.value)
                        signal = generate_signal(feature, threshold=args.threshold)
                        producer.send(args.target_topic, key=signal.symbol, value=signal.to_payload()).get(timeout=10)
                        handle.write(json.dumps(signal.to_payload(), separators=(",", ":")) + "\n")
                        handle.flush()
                        processed += 1
                        print(
                            f"signal {processed}: {signal.symbol} target={signal.target_position} "
                            f"return={signal.price_return:.5f}"
                        )
                        if processed >= args.max_messages:
                            break
                    if processed >= args.max_messages:
                        break
    finally:
        producer.flush()
        producer.close()
        consumer.close()


if __name__ == "__main__":
    main()
