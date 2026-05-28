from finance_pipeline.schemas import MarketFeature


def test_market_feature_from_payload_remains_backward_compatible() -> None:
    payload = {
        "symbol": "BTCUSDT",
        "window_start": "2026-01-01T00:00:00.000Z",
        "window_end": "2026-01-01T00:00:05.000Z",
        "trade_count": 4,
        "avg_price": 43110.0,
        "open_price": 43100.0,
        "close_price": 43120.0,
        "total_quantity": 0.95,
        "price_return": 0.000464,
    }

    feature = MarketFeature.from_payload(payload)

    assert feature.symbol == "BTCUSDT"
    assert feature.vwap == 43110.0
    assert feature.high_price == 43120.0
    assert feature.low_price == 43120.0
    assert feature.high_low_range == 0.0
    assert feature.notional_volume == 40954.5
    assert feature.buy_quantity == 0.0
    assert feature.sell_quantity == 0.0
    assert feature.volume_imbalance == 0.0
    assert feature.price_volatility == 0.0
    assert feature.instrument_type == "spot"
    assert feature.base_asset == "BTC"
    assert feature.quote_asset == "USDT"
