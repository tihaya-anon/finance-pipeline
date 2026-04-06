from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

from finance_pipeline.kafka_utils import build_producer
from finance_pipeline.schemas import MarketTick
from finance_pipeline.settings import SETTINGS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay market ticks into Kafka.")
    parser.add_argument(
        "--csv",
        default=str(SETTINGS.sample_ticks_csv),
        help="Path to tick CSV data.",
    )
    parser.add_argument("--speedup", type=float, default=50.0, help="Replay speed multiplier.")
    parser.add_argument(
        "--bootstrap-servers",
        default=SETTINGS.bootstrap_servers,
        help="Kafka bootstrap servers.",
    )
    parser.add_argument("--topic", default=SETTINGS.ticks_topic, help="Target topic for tick events.")
    return parser.parse_args()


def load_ticks(csv_path: Path) -> list[MarketTick]:
    """Load the replay fixture into memory so timing stays deterministic."""
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        return [MarketTick.from_csv_row(row) for row in csv.DictReader(handle)]


def main() -> None:
    args = parse_args()
    ticks = load_ticks(Path(args.csv))
    producer = build_producer(args.bootstrap_servers)

    previous_tick: MarketTick | None = None
    sent_count = 0

    try:
        for tick in ticks:
            if previous_tick is not None:
                # Preserve event-time gaps, but accelerate them for local iteration.
                event_gap = (tick.event_time - previous_tick.event_time).total_seconds()
                sleep_seconds = max(event_gap / args.speedup, 0.0)
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)

            producer.send(args.topic, key=tick.symbol, value=tick.to_payload()).get(timeout=10)
            previous_tick = tick
            sent_count += 1
            print(f"sent tick {sent_count}: {tick.symbol} {tick.price:.2f} @ {tick.event_time.isoformat()}")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
