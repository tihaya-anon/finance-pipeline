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
        vwap=99.7,
        open_price=99.0,
        close_price=close_price,
        total_quantity=8.0,
        buy_quantity=4.5,
        sell_quantity=3.5,
        volume_imbalance=0.125,
        price_volatility=0.003,
        price_return=price_return,
    )


def test_generate_signal_goes_long_when_return_crosses_threshold() -> None:
    signal = generate_signal(build_feature(price_return=0.0015))
    assert signal.target_position == 1
    assert signal.target_position_size == 0.3
    assert signal.reason == "long_momentum"


def test_generate_signal_flattens_when_return_is_small() -> None:
    signal = generate_signal(build_feature(price_return=0.0002))
    assert signal.target_position == 0
    assert signal.target_position_size == 0.0
    assert signal.reason == "flat"


def test_generate_signal_caps_position_size() -> None:
    signal = generate_signal(build_feature(price_return=0.02), max_position_size=2.0, max_return_for_full_size=0.005)
    assert signal.target_position == 1
    assert signal.target_position_size == 2.0


def test_generate_signal_preserves_instrument_metadata() -> None:
    feature = build_feature(price_return=0.0015)
    feature = MarketFeature(
        symbol=feature.symbol,
        window_start=feature.window_start,
        window_end=feature.window_end,
        trade_count=feature.trade_count,
        avg_price=feature.avg_price,
        vwap=feature.vwap,
        open_price=feature.open_price,
        close_price=feature.close_price,
        total_quantity=feature.total_quantity,
        buy_quantity=feature.buy_quantity,
        sell_quantity=feature.sell_quantity,
        volume_imbalance=feature.volume_imbalance,
        price_volatility=feature.price_volatility,
        price_return=feature.price_return,
        venue="binance",
        instrument_type="spot",
        base_asset="BTC",
        quote_asset="USDT",
    )

    signal = generate_signal(feature)

    assert signal.venue == "binance"
    assert signal.base_asset == "BTC"
    assert signal.quote_asset == "USDT"


def test_portfolio_updates_cash_and_equity_after_signal() -> None:
    portfolio = SimplePortfolio()
    signal = generate_signal(build_feature(price_return=0.002, close_price=101.0))

    snapshot = portfolio.apply_signal(signal)

    assert snapshot.current_position == 1
    assert snapshot.current_position_size == 0.4
    assert snapshot.cash == -40.4
    assert snapshot.equity == 0.0


def test_portfolio_tracks_same_symbol_across_venues_separately() -> None:
    portfolio = SimplePortfolio()
    signal_a = generate_signal(
        MarketFeature(
            symbol="BTCUSDT",
            window_start=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 1, 1, 0, 0, 5, tzinfo=timezone.utc),
            trade_count=4,
            avg_price=100.0,
            vwap=100.2,
            open_price=99.0,
            close_price=101.0,
            total_quantity=8.0,
            buy_quantity=5.0,
            sell_quantity=3.0,
            volume_imbalance=0.25,
            price_volatility=0.004,
            price_return=0.002,
            venue="binance",
            instrument_type="spot",
            base_asset="BTC",
            quote_asset="USDT",
        )
    )
    signal_b = generate_signal(
        MarketFeature(
            symbol="BTCUSDT",
            window_start=datetime(2026, 1, 1, 0, 0, 5, tzinfo=timezone.utc),
            window_end=datetime(2026, 1, 1, 0, 0, 10, tzinfo=timezone.utc),
            trade_count=4,
            avg_price=100.0,
            vwap=100.2,
            open_price=99.0,
            close_price=101.0,
            total_quantity=8.0,
            buy_quantity=5.0,
            sell_quantity=3.0,
            volume_imbalance=0.25,
            price_volatility=0.004,
            price_return=0.002,
            venue="synthetic",
            instrument_type="spot",
            base_asset="BTC",
            quote_asset="USDT",
        )
    )

    portfolio.apply_signal(signal_a)
    portfolio.apply_signal(signal_b)

    assert len(portfolio.positions) == 2
