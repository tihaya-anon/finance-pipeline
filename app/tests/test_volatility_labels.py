from __future__ import annotations

import csv
import math
from datetime import datetime, timedelta, timezone

from finance_pipeline.schemas import MarketTick
from finance_pipeline.volatility_labels import generate_future_volatility_labels, write_volatility_labels


def build_tick(second_offset: int, price: float) -> MarketTick:
    return MarketTick(
        symbol="BTCUSDT",
        event_time=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=second_offset),
        price=price,
        quantity=0.1,
        side="buy",
        venue="replay",
        instrument_type="spot",
        base_asset="BTC",
        quote_asset="USDT",
    )


def test_generate_future_volatility_labels_uses_forward_horizon_returns() -> None:
    ticks = [
        build_tick(0, 100.0),
        build_tick(1, 101.0),
        build_tick(5, 100.0),
        build_tick(6, 102.0),
        build_tick(7, 101.0),
        build_tick(10, 104.0),
    ]

    labels = generate_future_volatility_labels(ticks, window_seconds=5, horizon_seconds=5)

    assert len(labels) == 3
    first_label = labels[0]
    expected_returns = [math.log(102.0 / 100.0), math.log(101.0 / 102.0)]
    expected_mean = sum(expected_returns) / len(expected_returns)
    expected_stddev = math.sqrt(sum((value - expected_mean) ** 2 for value in expected_returns) / len(expected_returns))

    assert first_label.window_start == "2026-01-01T00:00:00.000Z"
    assert first_label.window_end == "2026-01-01T00:00:05.000Z"
    assert first_label.horizon_seconds == 5
    assert first_label.observation_count == 2
    assert first_label.future_realized_vol == round(expected_stddev, 8)
    assert first_label.future_log_return == round(math.log(101.0 / 100.0), 8)


def test_write_volatility_labels_persists_csv(tmp_path) -> None:
    ticks = [
        build_tick(0, 100.0),
        build_tick(5, 100.0),
        build_tick(6, 101.0),
    ]
    labels = generate_future_volatility_labels(ticks, window_seconds=5, horizon_seconds=5)

    output_path = tmp_path / "future_vol_labels.csv"
    write_volatility_labels(output_path, labels)

    with output_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == len(labels)
    assert rows[0]["symbol"] == "BTCUSDT"
    assert rows[0]["horizon_seconds"] == "5"
