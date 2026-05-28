from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import itertools
from typing import Any
from urllib import request

from websockets.asyncio.client import connect

from finance_pipeline.core.kafka_utils import build_producer
from finance_pipeline.core.schemas import MarketTick
from finance_pipeline.config.settings import SETTINGS


UNISWAP_V2_SWAP_TOPIC = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"


@dataclass(frozen=True)
class PairConfig:
    pair_address: str
    base_symbol: str
    quote_symbol: str
    base_decimals: int
    quote_decimals: int

    @property
    def market_symbol(self) -> str:
        return f"{self.base_symbol}{self.quote_symbol}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stream EVM AMM swap logs into Kafka as market ticks.")
    parser.add_argument("--ws-url", default=SETTINGS.evm_ws_url)
    parser.add_argument("--http-url", default=SETTINGS.evm_http_url)
    parser.add_argument("--pair-address", default=SETTINGS.evm_pair_address)
    parser.add_argument("--base-symbol", default=SETTINGS.evm_base_symbol)
    parser.add_argument("--quote-symbol", default=SETTINGS.evm_quote_symbol)
    parser.add_argument("--base-decimals", type=int, default=SETTINGS.evm_base_decimals)
    parser.add_argument("--quote-decimals", type=int, default=SETTINGS.evm_quote_decimals)
    parser.add_argument("--bootstrap-servers", default=SETTINGS.bootstrap_servers)
    parser.add_argument("--topic", default=SETTINGS.ticks_topic)
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> PairConfig:
    required_fields = {
        "ws-url": args.ws_url,
        "http-url": args.http_url,
        "pair-address": args.pair_address,
        "base-symbol": args.base_symbol,
        "quote-symbol": args.quote_symbol,
    }
    missing_fields = [name for name, value in required_fields.items() if not value]
    if missing_fields:
        joined = ", ".join(missing_fields)
        raise SystemExit(f"Missing required chain source settings: {joined}")

    return PairConfig(
        pair_address=args.pair_address.lower(),
        base_symbol=args.base_symbol.upper(),
        quote_symbol=args.quote_symbol.upper(),
        base_decimals=args.base_decimals,
        quote_decimals=args.quote_decimals,
    )


def normalize_hex_address(address: str) -> str:
    address = address.lower()
    return address if address.startswith("0x") else f"0x{address}"


def parse_hex_int(raw_value: str) -> int:
    return int(raw_value, 16)


def decode_uint256_words(data_hex: str) -> list[int]:
    payload = data_hex.removeprefix("0x")
    if len(payload) % 64 != 0:
        raise ValueError(f"Unexpected EVM log payload length: {len(payload)}")

    return [int(payload[index : index + 64], 16) for index in range(0, len(payload), 64)]


def scale_amount(raw_amount: int, decimals: int) -> Decimal:
    return Decimal(raw_amount) / (Decimal(10) ** decimals)


def tick_from_swap_log(log: dict[str, Any], pair: PairConfig, block_timestamp: datetime) -> MarketTick:
    amounts = decode_uint256_words(log["data"])
    if len(amounts) != 4:
        raise ValueError(f"Unexpected Swap payload word count: {len(amounts)}")

    amount0_in, amount1_in, amount0_out, amount1_out = amounts

    if amount0_out > 0 and amount1_in > 0:
        quantity = scale_amount(amount0_out, pair.base_decimals)
        notional = scale_amount(amount1_in, pair.quote_decimals)
        side = "buy"
    elif amount0_in > 0 and amount1_out > 0:
        quantity = scale_amount(amount0_in, pair.base_decimals)
        notional = scale_amount(amount1_out, pair.quote_decimals)
        side = "sell"
    else:
        raise ValueError(
            "Swap log does not match a simple token0/token1 trade "
            f"(amount0_in={amount0_in}, amount1_in={amount1_in}, amount0_out={amount0_out}, amount1_out={amount1_out})"
        )

    if quantity <= 0:
        raise ValueError("Swap quantity must be positive")

    price = notional / quantity
    return MarketTick(
        symbol=pair.market_symbol,
        event_time=block_timestamp,
        price=float(price),
        quantity=float(quantity),
        side=side,
        venue="evm",
        instrument_type="spot",
        base_asset=pair.base_symbol,
        quote_asset=pair.quote_symbol,
    )


class BlockTimestampResolver:
    def __init__(self, rpc_http_url: str) -> None:
        self.rpc_http_url = rpc_http_url
        self._block_cache: dict[str, datetime] = {}
        self._request_ids = itertools.count(1)

    def _call(self, method: str, params: list[Any]) -> Any:
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": next(self._request_ids),
                "method": method,
                "params": params,
            }
        ).encode("utf-8")
        req = request.Request(
            self.rpc_http_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=10) as response:
            result = json.load(response)

        if result.get("error"):
            raise RuntimeError(f"RPC error for {method}: {result['error']}")
        return result.get("result")

    def latest_block_number(self) -> int:
        latest = self._call("eth_blockNumber", [])
        if latest is None:
            raise RuntimeError("RPC returned no block number")
        return parse_hex_int(latest)

    def resolve(self, block_hash: str) -> datetime:
        normalized_hash = block_hash.lower()
        cached = self._block_cache.get(normalized_hash)
        if cached is not None:
            return cached

        block = self._call("eth_getBlockByHash", [normalized_hash, False])
        if not block or "timestamp" not in block:
            raise RuntimeError(f"Block not found for hash {block_hash}")

        block_timestamp = datetime.fromtimestamp(int(block["timestamp"], 16), tz=timezone.utc)
        self._block_cache[normalized_hash] = block_timestamp
        return block_timestamp

    def fetch_logs(self, *, address: str, topics: list[str], from_block: int, to_block: int | str = "latest") -> list[dict[str, Any]]:
        filter_params = {
            "address": normalize_hex_address(address),
            "topics": topics,
            "fromBlock": hex(from_block),
            "toBlock": hex(to_block) if isinstance(to_block, int) else to_block,
        }
        result = self._call("eth_getLogs", [filter_params])
        if not isinstance(result, list):
            raise RuntimeError(f"Unexpected eth_getLogs result type: {type(result)!r}")
        return result

    def fetch_logs_in_chunks(
        self,
        *,
        address: str,
        topics: list[str],
        from_block: int,
        to_block: int,
        block_step: int,
    ) -> list[dict[str, Any]]:
        if block_step <= 0:
            raise ValueError("block_step must be positive")

        logs: list[dict[str, Any]] = []
        current_from = from_block
        while current_from <= to_block:
            current_to = min(current_from + block_step - 1, to_block)
            logs.extend(
                self.fetch_logs(
                    address=address,
                    topics=topics,
                    from_block=current_from,
                    to_block=current_to,
                )
            )
            current_from = current_to + 1
        return logs


def sort_evm_logs(logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        logs,
        key=lambda log: (
            parse_hex_int(log.get("blockNumber", "0x0")),
            parse_hex_int(log.get("transactionIndex", "0x0")),
            parse_hex_int(log.get("logIndex", "0x0")),
        ),
    )


async def stream_onchain_swaps(args: argparse.Namespace) -> None:
    pair = validate_args(args)
    producer = build_producer(args.bootstrap_servers)
    timestamp_resolver = BlockTimestampResolver(args.http_url)
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

    try:
        async with connect(args.ws_url) as websocket:
            await websocket.send(json.dumps(subscription_request))

            async for raw_message in websocket:
                message = json.loads(raw_message)
                if "params" not in message:
                    continue

                log = message["params"].get("result")
                if not log:
                    continue

                block_timestamp = timestamp_resolver.resolve(log["blockHash"])
                tick = tick_from_swap_log(log, pair, block_timestamp)
                producer.send(args.topic, key=tick.instrument_key, value=tick.to_payload()).get(timeout=10)
                print(
                    f"streamed onchain tick: {tick.symbol} {tick.side} "
                    f"{tick.quantity:.6f} @ {tick.price:.6f} {pair.quote_symbol}"
                )
    finally:
        producer.flush()
        producer.close()


def main() -> None:
    args = parse_args()
    asyncio.run(stream_onchain_swaps(args))


if __name__ == "__main__":
    main()
