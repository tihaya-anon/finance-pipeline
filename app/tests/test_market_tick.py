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
    assert tick.venue == "binance"
    assert tick.instrument_type == "spot"
    assert tick.base_asset == "BTC"
    assert tick.quote_asset == "USDT"
    assert tick.price == 43123.45
    assert tick.quantity == 0.15
    assert tick.side == "buy"


def test_market_tick_from_legacy_csv_defaults_venue_to_replay() -> None:
    tick = MarketTick.from_csv_row(
        {
            "symbol": "BTCUSDT",
            "event_time": "2026-01-01T00:00:00.000Z",
            "price": "43100.0",
            "quantity": "0.25",
            "side": "buy",
        }
    )

    assert tick.venue == "replay"
    assert tick.instrument_type == "spot"
    assert tick.base_asset == "BTC"
    assert tick.quote_asset == "USDT"
