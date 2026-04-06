from finance_pipeline.questdb_sink import build_feature_line
from finance_pipeline.schemas import MarketFeature
from datetime import datetime, timezone


def test_build_feature_line_contains_expected_measurement_and_fields() -> None:
    feature = MarketFeature(
        symbol="BTCUSDT",
        window_start=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        window_end=datetime(2026, 1, 1, 0, 0, 5, tzinfo=timezone.utc),
        trade_count=4,
        avg_price=43110.0,
        open_price=43100.0,
        close_price=43120.0,
        total_quantity=0.95,
        price_return=0.000464,
    )

    line = build_feature_line(feature)

    assert line.startswith("market_features,symbol=BTCUSDT ")
    assert 'window_end="2026-01-01T00:00:05.000Z"' in line
    assert "trade_count=4i" in line
