from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from websockets.asyncio.client import connect

from finance_pipeline.storage.market_fixture import write_ticks
from finance_pipeline.sources.onchain_source import (
    BlockTimestampResolver,
    UNISWAP_V2_SWAP_TOPIC,
    normalize_hex_address,
    sort_evm_logs,
    tick_from_swap_log,
    validate_args,
)
from finance_pipeline.config.settings import SETTINGS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture EVM AMM swap logs into a local CSV fixture.")
    parser.add_argument("--ws-url", default=SETTINGS.evm_ws_url)
    parser.add_argument("--http-url", default=SETTINGS.evm_http_url)
    parser.add_argument("--pair-address", default=SETTINGS.evm_pair_address)
    parser.add_argument("--base-symbol", default=SETTINGS.evm_base_symbol)
    parser.add_argument("--quote-symbol", default=SETTINGS.evm_quote_symbol)
    parser.add_argument("--base-decimals", type=int, default=SETTINGS.evm_base_decimals)
    parser.add_argument("--quote-decimals", type=int, default=SETTINGS.evm_quote_decimals)
    parser.add_argument("--output", default=str(SETTINGS.onchain_capture_output))
    parser.add_argument("--max-events", type=int, default=SETTINGS.onchain_capture_max_events)
    parser.add_argument("--lookback-blocks", type=int, default=SETTINGS.onchain_capture_lookback_blocks)
    return parser.parse_args()


def capture_recent_ticks(args: argparse.Namespace, timestamp_resolver: BlockTimestampResolver) -> list:
    latest_block = timestamp_resolver.latest_block_number()
    from_block = max(latest_block - args.lookback_blocks, 0)
    recent_logs = timestamp_resolver.fetch_logs_in_chunks(
        address=args.pair_address,
        topics=[UNISWAP_V2_SWAP_TOPIC],
        from_block=from_block,
        to_block=latest_block,
        block_step=10,
    )
    pair = validate_args(args)
    ticks = []
    for index, log in enumerate(sort_evm_logs(recent_logs)[-args.max_events :], start=1):
        block_timestamp = timestamp_resolver.resolve(log["blockHash"])
        ticks.append(tick_from_swap_log(log, pair, block_timestamp))
        print(f"captured recent onchain tick {index}/{args.max_events}")
    return ticks


async def capture_ticks(args: argparse.Namespace) -> None:
    pair = validate_args(args)
    subscription_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_subscribe",
        "params": [
            "logs",
            {
                "address": normalize_hex_address(pair.pair_address),
                "topics": [UNISWAP_V2_SWAP_TOPIC],
            },
        ],
    }
    timestamp_resolver = BlockTimestampResolver(args.http_url)
    ticks = capture_recent_ticks(args, timestamp_resolver)

    if len(ticks) >= args.max_events:
        write_ticks(Path(args.output), ticks[: args.max_events])
        print(f"wrote {len(ticks[: args.max_events])} captured ticks to {args.output}")
        return

    async with connect(args.ws_url) as websocket:
        await websocket.send(json.dumps(subscription_request))
        while len(ticks) < args.max_events:
            message = json.loads(await websocket.recv())
            log = message.get("params", {}).get("result")
            if not log:
                continue

            block_timestamp = timestamp_resolver.resolve(log["blockHash"])
            ticks.append(tick_from_swap_log(log, pair, block_timestamp))
            print(f"captured live onchain tick {len(ticks)}/{args.max_events}")

    write_ticks(Path(args.output), ticks)
    print(f"wrote {len(ticks)} captured ticks to {args.output}")


def run(args: argparse.Namespace) -> None:
    asyncio.run(capture_ticks(args))


def main() -> None:
    run(parse_args())
