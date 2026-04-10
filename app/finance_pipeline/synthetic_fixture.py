from __future__ import annotations

import argparse
from datetime import timedelta
from pathlib import Path
import random

from finance_pipeline.market_fixture import write_ticks
from finance_pipeline.schemas import MarketTick, infer_spot_asset_pair, parse_utc_timestamp
from finance_pipeline.settings import SETTINGS


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a local synthetic tick fixture.")
    parser.add_argument("--output", default=str(SETTINGS.synthetic_output_csv))
    parser.add_argument("--symbol", default=SETTINGS.synthetic_symbol)
    parser.add_argument("--start-time", default=SETTINGS.synthetic_start_time)
    parser.add_argument("--start-price", type=float, default=SETTINGS.synthetic_start_price)
    parser.add_argument("--tick-count", type=int, default=SETTINGS.synthetic_tick_count)
    parser.add_argument("--interval-ms", type=int, default=SETTINGS.synthetic_interval_ms)
    parser.add_argument("--quantity-min", type=float, default=SETTINGS.synthetic_quantity_min)
    parser.add_argument("--quantity-max", type=float, default=SETTINGS.synthetic_quantity_max)
    parser.add_argument("--volatility-bps", type=float, default=SETTINGS.synthetic_volatility_bps)
    parser.add_argument("--drift-bps", type=float, default=SETTINGS.synthetic_drift_bps)
    parser.add_argument("--seed", type=int, default=SETTINGS.synthetic_seed)
    parser.add_argument("--venue", default="synthetic")
    parser.add_argument("--instrument-type", default="spot")
    parser.add_argument("--base-asset", default="")
    parser.add_argument("--quote-asset", default="")
    return parser.parse_args(argv)


def build_synthetic_ticks(args: argparse.Namespace) -> list[MarketTick]:
    rng = random.Random(args.seed)
    event_time = parse_utc_timestamp(args.start_time)
    price = args.start_price
    ticks: list[MarketTick] = []
    base_asset = args.base_asset
    quote_asset = args.quote_asset
    if args.instrument_type == "spot" and (not base_asset or not quote_asset):
        inferred_base_asset, inferred_quote_asset = infer_spot_asset_pair(args.symbol)
        base_asset = base_asset or inferred_base_asset
        quote_asset = quote_asset or inferred_quote_asset

    for _ in range(args.tick_count):
        move_bps = rng.gauss(args.drift_bps, args.volatility_bps)
        price = max(price * (1 + move_bps / 10_000), 0.01)
        quantity = rng.uniform(args.quantity_min, args.quantity_max)
        side = "buy" if move_bps >= 0 else "sell"
        ticks.append(
            MarketTick(
                symbol=args.symbol,
                event_time=event_time,
                price=round(price, 6),
                quantity=round(quantity, 6),
                side=side,
                venue=args.venue,
                instrument_type=args.instrument_type,
                base_asset=base_asset,
                quote_asset=quote_asset,
            )
        )
        event_time += timedelta(milliseconds=args.interval_ms)

    return ticks


def main() -> None:
    args = parse_args()
    ticks = build_synthetic_ticks(args)
    write_ticks(Path(args.output), ticks)
    print(f"wrote {len(ticks)} synthetic ticks to {args.output}")


if __name__ == "__main__":
    main()
