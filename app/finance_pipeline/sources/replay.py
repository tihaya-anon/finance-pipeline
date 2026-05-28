from __future__ import annotations

import argparse
from datetime import datetime, timezone
import time
from pathlib import Path

from finance_pipeline.core.kafka_utils import build_producer
from finance_pipeline.storage.market_fixture import load_ticks
from finance_pipeline.core.schemas import MarketTick
from finance_pipeline.config.settings import SETTINGS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay market ticks into Kafka.")
    parser.add_argument(
        "--csv",
        default=str(SETTINGS.replay_fixture_csv),
        help="Path to tick CSV data.",
    )
    parser.add_argument("--speedup", type=float, default=SETTINGS.replay_speedup, help="Replay speed multiplier.")
    parser.add_argument(
        "--shift-to-now",
        action="store_true",
        help="Shift fixture timestamps so the last tick lands near current UTC time.",
    )
    parser.add_argument(
        "--bootstrap-servers",
        default=SETTINGS.bootstrap_servers,
        help="Kafka bootstrap servers.",
    )
    parser.add_argument("--topic", default=SETTINGS.ticks_topic, help="Target topic for tick events.")
    return parser.parse_args()


def shift_ticks_to_now(ticks: list[MarketTick]) -> list[MarketTick]:
    if not ticks:
        return ticks

    offset = datetime.now(timezone.utc) - ticks[-1].event_time
    return [
        MarketTick(
            symbol=tick.symbol,
            event_time=tick.event_time + offset,
            price=tick.price,
            quantity=tick.quantity,
            side=tick.side,
            venue=tick.venue,
            instrument_type=tick.instrument_type,
            base_asset=tick.base_asset,
            quote_asset=tick.quote_asset,
        )
        for tick in ticks
    ]


def run(args: argparse.Namespace) -> None:
    ticks = load_ticks(Path(args.csv))
    if args.shift_to_now:
        ticks = shift_ticks_to_now(ticks)
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

            producer.send(args.topic, key=tick.instrument_key, value=tick.to_payload()).get(timeout=10)
            previous_tick = tick
            sent_count += 1
            print(f"sent tick {sent_count}: {tick.symbol} {tick.price:.2f} @ {tick.event_time.isoformat()}")
    finally:
        producer.flush()
        producer.close()


def main() -> None:
    run(parse_args())
