from finance_pipeline.simulated_source import available_scenarios, generate_next_tick, resolve_scenario

import random


def test_resolve_scenario_returns_yaml_defined_scenario() -> None:
    scenario = resolve_scenario("trend_up")

    assert scenario.name == "trend_up"
    assert scenario.drift_bps > 0


def test_generate_next_tick_produces_positive_price_and_quantity() -> None:
    scenario = available_scenarios()["calm_range"]
    tick = generate_next_tick(
        symbol="BTCUSDT",
        current_price=43100.0,
        rng=random.Random(7),
        scenario=scenario,
    )

    assert tick.symbol == "BTCUSDT"
    assert tick.venue == "synthetic"
    assert tick.instrument_type == "spot"
    assert tick.base_asset == "BTC"
    assert tick.quote_asset == "USDT"
    assert tick.price > 0
    assert tick.quantity > 0
    assert tick.side in {"buy", "sell"}
