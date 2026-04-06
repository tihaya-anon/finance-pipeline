from finance_pipeline.schemas import MarketTick


def test_market_tick_can_be_built_from_binance_agg_trade() -> None:
    payload = {
        "s": "BTCUSDT",
        "T": 1775487361000,
        "p": "43123.45",
        "q": "0.1500",
        "m": False,
    }

    tick = MarketTick.from_binance_agg_trade(payload)

    assert tick.symbol == "BTCUSDT"
    assert tick.price == 43123.45
    assert tick.quantity == 0.15
    assert tick.side == "buy"
