from __future__ import annotations

from finance_pipeline.schemas import MarketFeature, TradingSignal


LONG_SIGNAL = 1
FLAT_SIGNAL = 0
SHORT_SIGNAL = -1


def _compute_position_size(
    price_return: float,
    max_position_size: float,
    max_return_for_full_size: float,
) -> float:
    if max_position_size <= 0:
        raise ValueError("max_position_size must be positive")
    if max_return_for_full_size <= 0:
        raise ValueError("max_return_for_full_size must be positive")
    strength = abs(price_return) / max_return_for_full_size
    return min(strength, 1.0) * max_position_size


def generate_signal(
    feature: MarketFeature,
    threshold: float = 0.001,
    max_position_size: float = 1.0,
    max_return_for_full_size: float = 0.005,
) -> TradingSignal:
    """Map a windowed return into a coarse long/flat/short target position."""
    if threshold <= 0:
        raise ValueError("threshold must be positive")

    if feature.price_return >= threshold:
        target_position = LONG_SIGNAL
        reason = "long_momentum"
    elif feature.price_return <= -threshold:
        target_position = SHORT_SIGNAL
        reason = "short_momentum"
    else:
        target_position = FLAT_SIGNAL
        reason = "flat"

    target_position_size = 0.0
    if target_position != FLAT_SIGNAL:
        target_position_size = target_position * _compute_position_size(
            feature.price_return,
            max_position_size=max_position_size,
            max_return_for_full_size=max_return_for_full_size,
        )

    return TradingSignal(
        symbol=feature.symbol,
        generated_at=feature.window_end,
        window_end=feature.window_end,
        target_position=target_position,
        target_position_size=round(target_position_size, 6),
        reference_price=feature.close_price,
        price_return=feature.price_return,
        reason=reason,
        venue=feature.venue,
        instrument_type=feature.instrument_type,
        base_asset=feature.base_asset,
        quote_asset=feature.quote_asset,
    )
