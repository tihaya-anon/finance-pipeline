from __future__ import annotations

from dataclasses import dataclass, field

from finance_pipeline.core.schemas import PortfolioSnapshot, TradingSignal


@dataclass
class PositionState:
    current_position_size: float = 0.0
    last_price: float = 0.0


@dataclass
class SimplePortfolio:
    cash: float = 0.0
    positions: dict[str, PositionState] = field(default_factory=dict)

    @staticmethod
    def _direction_from_size(position_size: float) -> int:
        if position_size > 0:
            return 1
        if position_size < 0:
            return -1
        return 0

    def apply_signal(self, signal: TradingSignal) -> PortfolioSnapshot:
        """Rebalance to the requested target position at the signal reference price."""
        state = self.positions.setdefault(signal.instrument_key, PositionState())
        delta = signal.target_position_size - state.current_position_size

        if delta > 0:
            action = "buy"
        elif delta < 0:
            action = "sell"
        else:
            action = "hold"

        self.cash -= delta * signal.reference_price
        state.current_position_size = signal.target_position_size
        state.last_price = signal.reference_price

        equity = self.cash + sum(
            position.current_position_size * position.last_price for position in self.positions.values()
        )

        return PortfolioSnapshot(
            symbol=signal.symbol,
            timestamp=signal.generated_at,
            action=action,
            fill_price=signal.reference_price,
            target_position=signal.target_position,
            current_position=self._direction_from_size(state.current_position_size),
            target_position_size=round(signal.target_position_size, 6),
            current_position_size=round(state.current_position_size, 6),
            cash=round(self.cash, 6),
            equity=round(equity, 6),
            venue=signal.venue,
            instrument_type=signal.instrument_type,
            base_asset=signal.base_asset,
            quote_asset=signal.quote_asset,
        )
