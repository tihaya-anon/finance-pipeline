from datetime import datetime, timezone

from finance_pipeline.portfolio import SimplePortfolio
from finance_pipeline.schemas import MarketFeature
from finance_pipeline.strategy import generate_signal


def build_feature(price_return: float, close_price: float = 100.0) -> MarketFeature:
    """Create a compact feature fixture for signal and portfolio tests."""
    start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 1, 0, 0, 5, tzinfo=timezone.utc)
    return MarketFeature(
        symbol="BTCUSDT",
        window_start=start,
        window_end=end,
        trade_count=4,
        avg_price=99.5,
        open_price=99.0,
        close_price=close_price,
        total_quantity=8.0,
        price_return=price_return,
    )


def test_generate_signal_goes_long_when_return_crosses_threshold() -> None:
    signal = generate_signal(build_feature(price_return=0.0015))
    assert signal.target_position == 1
    assert signal.reason == "long_momentum"


def test_generate_signal_flattens_when_return_is_small() -> None:
    signal = generate_signal(build_feature(price_return=0.0002))
    assert signal.target_position == 0
    assert signal.reason == "flat"


def test_portfolio_updates_cash_and_equity_after_signal() -> None:
    portfolio = SimplePortfolio()
    signal = generate_signal(build_feature(price_return=0.002, close_price=101.0))

    snapshot = portfolio.apply_signal(signal)

    assert snapshot.current_position == 1
    assert snapshot.cash == -101.0
    assert snapshot.equity == 0.0
