from __future__ import annotations

from dataclasses import dataclass, field

from finance_pipeline.schemas import PortfolioSnapshot, TradingSignal


@dataclass
class PositionState:
    current_position: int = 0
    last_price: float = 0.0


@dataclass
class SimplePortfolio:
    cash: float = 0.0
    positions: dict[str, PositionState] = field(default_factory=dict)

    def apply_signal(self, signal: TradingSignal) -> PortfolioSnapshot:
        """Rebalance to the requested target position at the signal reference price."""
        state = self.positions.setdefault(signal.symbol, PositionState())
        delta = signal.target_position - state.current_position

        if delta > 0:
            action = "buy"
        elif delta < 0:
            action = "sell"
        else:
            action = "hold"

        self.cash -= delta * signal.reference_price
        state.current_position = signal.target_position
        state.last_price = signal.reference_price

        equity = self.cash + sum(
            position.current_position * position.last_price for position in self.positions.values()
        )

        return PortfolioSnapshot(
            symbol=signal.symbol,
            timestamp=signal.generated_at,
            action=action,
            fill_price=signal.reference_price,
            target_position=signal.target_position,
            current_position=state.current_position,
            cash=round(self.cash, 6),
            equity=round(equity, 6),
        )
