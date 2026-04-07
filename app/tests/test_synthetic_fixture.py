from finance_pipeline.synthetic_fixture import build_synthetic_ticks, parse_args


def test_synthetic_fixture_builds_deterministic_tick_series() -> None:
    args = parse_args([])
    args.tick_count = 3
    args.seed = 11
    args.symbol = "BTCUSDT"

    ticks = build_synthetic_ticks(args)

    assert len(ticks) == 3
    assert ticks[0].symbol == "BTCUSDT"
    assert ticks[0].event_time < ticks[1].event_time
    assert ticks[0].price > 0
    assert ticks[0].side in {"buy", "sell"}
