from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import random
import time

from finance_pipeline.kafka_utils import build_producer
from finance_pipeline.repo_config import get_config_value, load_repo_config
from finance_pipeline.schemas import MarketTick
from finance_pipeline.settings import SETTINGS


CONFIG = load_repo_config()


@dataclass(frozen=True)
class SyntheticScenario:
    name: str
    drift_bps: float
    volatility_bps: float
    quantity_min: float
    quantity_max: float
    jump_probability: float
    jump_bps: float
    burst_probability: float
    burst_multiplier: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Continuously stream synthetic market ticks into Kafka.")
    parser.add_argument("--scenario", default=SETTINGS.simulation_scenario)
    parser.add_argument("--symbol", default=SETTINGS.simulation_symbol)
    parser.add_argument("--start-price", type=float, default=SETTINGS.simulation_start_price)
    parser.add_argument("--interval-ms", type=int, default=SETTINGS.simulation_interval_ms)
    parser.add_argument("--seed", type=int, default=SETTINGS.simulation_seed)
    parser.add_argument("--bootstrap-servers", default=SETTINGS.bootstrap_servers)
    parser.add_argument("--topic", default=SETTINGS.ticks_topic)
    parser.add_argument("--max-ticks", type=int, default=0, help="Stop after N ticks; 0 means run forever.")
    return parser.parse_args()


def available_scenarios() -> dict[str, SyntheticScenario]:
    raw_scenarios = get_config_value(CONFIG, "sources.synthetic_stream.scenarios", {})
    scenarios: dict[str, SyntheticScenario] = {}
    for name, raw_config in raw_scenarios.items():
        scenarios[name] = SyntheticScenario(
            name=name,
            drift_bps=float(raw_config["drift_bps"]),
            volatility_bps=float(raw_config["volatility_bps"]),
            quantity_min=float(raw_config["quantity_min"]),
            quantity_max=float(raw_config["quantity_max"]),
            jump_probability=float(raw_config["jump_probability"]),
            jump_bps=float(raw_config["jump_bps"]),
            burst_probability=float(raw_config["burst_probability"]),
            burst_multiplier=float(raw_config["burst_multiplier"]),
        )
    return scenarios


def resolve_scenario(name: str) -> SyntheticScenario:
    scenarios = available_scenarios()
    scenario = scenarios.get(name)
    if scenario is not None:
        return scenario

    available = ", ".join(sorted(scenarios))
    raise SystemExit(f"Unknown simulation scenario '{name}'. Available scenarios: {available}")


def generate_next_tick(
    *,
    symbol: str,
    current_price: float,
    rng: random.Random,
    scenario: SyntheticScenario,
) -> MarketTick:
    move_bps = rng.gauss(scenario.drift_bps, scenario.volatility_bps)
    if rng.random() < scenario.jump_probability:
        jump_direction = 1 if rng.random() >= 0.5 else -1
        move_bps += jump_direction * scenario.jump_bps

    next_price = max(current_price * (1 + move_bps / 10_000), 0.01)
    quantity = rng.uniform(scenario.quantity_min, scenario.quantity_max)
    if rng.random() < scenario.burst_probability:
        quantity *= scenario.burst_multiplier

    side = "buy" if move_bps >= 0 else "sell"
    return MarketTick(
        symbol=symbol,
        event_time=datetime.now(timezone.utc),
        price=round(next_price, 6),
        quantity=round(quantity, 6),
        side=side,
    )


def main() -> None:
    args = parse_args()
    scenario = resolve_scenario(args.scenario)
    rng = random.Random(args.seed)
    producer = build_producer(args.bootstrap_servers)
    current_price = args.start_price
    sent_count = 0

    try:
        while args.max_ticks <= 0 or sent_count < args.max_ticks:
            tick = generate_next_tick(
                symbol=args.symbol,
                current_price=current_price,
                rng=rng,
                scenario=scenario,
            )
            producer.send(args.topic, key=tick.symbol, value=tick.to_payload()).get(timeout=10)
            current_price = tick.price
            sent_count += 1
            print(
                f"simulated tick {sent_count}: {scenario.name} "
                f"{tick.symbol} {tick.side} {tick.price:.2f} qty={tick.quantity:.4f}"
            )
            time.sleep(args.interval_ms / 1000)
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
