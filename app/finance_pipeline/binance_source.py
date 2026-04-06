from __future__ import annotations

import argparse
import asyncio
import json

from websockets.asyncio.client import connect

from finance_pipeline.kafka_utils import build_producer
from finance_pipeline.schemas import MarketTick
from finance_pipeline.settings import SETTINGS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stream Binance public aggTrade data into Kafka.")
    parser.add_argument("--stream-url", default=SETTINGS.binance_stream_url)
    parser.add_argument("--bootstrap-servers", default=SETTINGS.bootstrap_servers)
    parser.add_argument("--topic", default=SETTINGS.ticks_topic)
    return parser.parse_args()


async def stream_binance(args: argparse.Namespace) -> None:
    producer = build_producer(args.bootstrap_servers)
    try:
        async with connect(args.stream_url) as websocket:
            async for raw_message in websocket:
                payload = json.loads(raw_message)
                tick = MarketTick.from_binance_agg_trade(payload)
                producer.send(args.topic, key=tick.symbol, value=tick.to_payload()).get(timeout=10)
                print(f"streamed tick: {tick.symbol} {tick.price:.2f} @ {tick.event_time.isoformat()}")
    finally:
        producer.flush()
        producer.close()


def main() -> None:
    args = parse_args()
    asyncio.run(stream_binance(args))


if __name__ == "__main__":
    main()
