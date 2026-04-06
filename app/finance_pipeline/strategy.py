from __future__ import annotations

from finance_pipeline.schemas import MarketFeature, TradingSignal


LONG_SIGNAL = 1
FLAT_SIGNAL = 0
SHORT_SIGNAL = -1


def generate_signal(feature: MarketFeature, threshold: float = 0.001) -> TradingSignal:
    """Map a windowed return into a coarse long/flat/short target position."""
    if feature.price_return >= threshold:
        target_position = LONG_SIGNAL
        reason = "long_momentum"
    elif feature.price_return <= -threshold:
        target_position = SHORT_SIGNAL
        reason = "short_momentum"
    else:
        target_position = FLAT_SIGNAL
        reason = "flat"

    return TradingSignal(
        symbol=feature.symbol,
        generated_at=feature.window_end,
        window_end=feature.window_end,
        target_position=target_position,
        reference_price=feature.close_price,
        price_return=feature.price_return,
        reason=reason,
    )
