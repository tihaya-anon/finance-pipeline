from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from finance_pipeline.storage.market_fixture import load_ticks
from finance_pipeline.core.schemas import MarketTick, format_utc_timestamp
from finance_pipeline.config.settings import SETTINGS


DEFAULT_WINDOW_SECONDS = 5
DEFAULT_HORIZON_SECONDS = 30


@dataclass(frozen=True)
class VolatilityLabel:
    symbol: str
    venue: str
    instrument_type: str
    base_asset: str
    quote_asset: str
    window_start: str
    window_end: str
    horizon_seconds: int
    observation_count: int
    future_realized_vol: float
    future_log_return: float


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate future realized volatility labels from tick CSV data.")
    parser.add_argument("--csv", default=str(SETTINGS.replay_fixture_csv), help="Path to tick CSV data.")
    parser.add_argument(
        "--output",
        default=str(SETTINGS.artifacts_dir / "future_vol_labels.csv"),
        help="Path to output CSV labels.",
    )
    parser.add_argument("--window-seconds", type=int, default=DEFAULT_WINDOW_SECONDS)
    parser.add_argument("--horizon-seconds", type=int, default=DEFAULT_HORIZON_SECONDS)
    return parser.parse_args(argv)


def instrument_group_key(tick: MarketTick) -> tuple[str, str, str, str, str]:
    return (tick.symbol, tick.venue, tick.instrument_type, tick.base_asset, tick.quote_asset)


def population_stddev(values: list[float]) -> float:
    if not values:
        return 0.0
    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def generate_future_volatility_labels(
    ticks: list[MarketTick],
    *,
    window_seconds: int,
    horizon_seconds: int,
) -> list[VolatilityLabel]:
    grouped_ticks: dict[tuple[str, str, str, str, str], list[MarketTick]] = defaultdict(list)
    for tick in ticks:
        grouped_ticks[instrument_group_key(tick)].append(tick)

    labels: list[VolatilityLabel] = []
    window_delta = timedelta(seconds=window_seconds)
    horizon_delta = timedelta(seconds=horizon_seconds)

    for instrument_key, instrument_ticks in grouped_ticks.items():
        sorted_ticks = sorted(instrument_ticks, key=lambda tick: tick.event_time)
        cursor = 0

        while cursor < len(sorted_ticks):
            window_start = sorted_ticks[cursor].event_time
            window_end = window_start + window_delta
            horizon_end = window_end + horizon_delta

            while cursor < len(sorted_ticks) and sorted_ticks[cursor].event_time < window_start:
                cursor += 1

            future_ticks = [
                tick for tick in sorted_ticks
                if window_end <= tick.event_time < horizon_end
            ]
            future_prices = [tick.price for tick in future_ticks]

            log_returns = [
                math.log(current_price / previous_price)
                for previous_price, current_price in zip(future_prices, future_prices[1:])
                if previous_price > 0 and current_price > 0
            ]

            future_realized_vol = population_stddev(log_returns)
            future_log_return = 0.0
            if future_prices and future_prices[0] > 0 and future_prices[-1] > 0:
                future_log_return = math.log(future_prices[-1] / future_prices[0])

            symbol, venue, instrument_type, base_asset, quote_asset = instrument_key
            labels.append(
                VolatilityLabel(
                    symbol=symbol,
                    venue=venue,
                    instrument_type=instrument_type,
                    base_asset=base_asset,
                    quote_asset=quote_asset,
                    window_start=format_utc_timestamp(window_start),
                    window_end=format_utc_timestamp(window_end),
                    horizon_seconds=horizon_seconds,
                    observation_count=len(log_returns),
                    future_realized_vol=round(future_realized_vol, 8),
                    future_log_return=round(future_log_return, 8),
                )
            )

            cursor += 1
            while cursor < len(sorted_ticks) and sorted_ticks[cursor].event_time < window_end:
                cursor += 1

    return labels


def write_volatility_labels(output_path: Path, labels: list[VolatilityLabel]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "symbol",
                "venue",
                "instrument_type",
                "base_asset",
                "quote_asset",
                "window_start",
                "window_end",
                "horizon_seconds",
                "observation_count",
                "future_realized_vol",
                "future_log_return",
            ],
        )
        writer.writeheader()
        for label in labels:
            writer.writerow(label.__dict__)


def run(args: argparse.Namespace) -> None:
    ticks = load_ticks(Path(args.csv))
    labels = generate_future_volatility_labels(
        ticks,
        window_seconds=args.window_seconds,
        horizon_seconds=args.horizon_seconds,
    )
    write_volatility_labels(Path(args.output), labels)
    print(f"wrote {len(labels)} volatility labels to {args.output}")


def main() -> None:
    run(parse_args())
