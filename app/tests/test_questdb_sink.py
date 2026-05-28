from finance_pipeline.services.questdb_sink import build_feature_line
from finance_pipeline.core.schemas import MarketFeature
from datetime import datetime, timezone


def test_build_feature_line_contains_expected_measurement_and_fields() -> None:
    feature = MarketFeature(
        symbol="BTCUSDT",
        window_start=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        window_end=datetime(2026, 1, 1, 0, 0, 5, tzinfo=timezone.utc),
        trade_count=4,
        avg_price=43110.0,
        vwap=43112.5,
        high_price=43125.0,
        low_price=43095.0,
        open_price=43100.0,
        close_price=43120.0,
        high_low_range=0.000696,
        total_quantity=0.95,
        notional_volume=40956.875,
        buy_quantity=0.6,
        sell_quantity=0.35,
        volume_imbalance=0.263158,
        price_volatility=0.000441,
        price_return=0.000464,
        venue="binance",
        instrument_type="spot",
        base_asset="BTC",
        quote_asset="USDT",
    )

    line = build_feature_line(feature)

    assert line.startswith(
        "market_features,symbol=BTCUSDT,venue=binance,instrument_type=spot,base_asset=BTC,quote_asset=USDT "
    )
    assert 'window_end="2026-01-01T00:00:05.000Z"' in line
    assert "trade_count=4i" in line
    assert "vwap=43112.5" in line
    assert "high_price=43125.0" in line
    assert "low_price=43095.0" in line
    assert "high_low_range=0.000696" in line
    assert "notional_volume=40956.875" in line
    assert "volume_imbalance=0.263158" in line
