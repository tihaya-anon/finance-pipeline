from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from threading import Lock
from typing import Any

from finance_pipeline.schemas import MarketFeature, PortfolioSnapshot, TradingSignal


@dataclass
class DashboardSnapshot:
    feature_count: int
    signal_count: int
    snapshot_count: int
    latest_feature: dict[str, Any] | None
    latest_signal: dict[str, Any] | None
    latest_portfolio: dict[str, Any] | None
    recent_features: list[dict[str, Any]]
    recent_signals: list[dict[str, Any]]
    recent_portfolio: list[dict[str, Any]]


class DashboardState:
    """Thread-safe in-memory cache used by the local real-time dashboard."""

    def __init__(self, history_limit: int) -> None:
        self._features: deque[MarketFeature] = deque(maxlen=history_limit)
        self._signals: deque[TradingSignal] = deque(maxlen=history_limit)
        self._portfolio: deque[PortfolioSnapshot] = deque(maxlen=history_limit)
        self._lock = Lock()

    def add_feature(self, feature: MarketFeature) -> None:
        with self._lock:
            self._features.append(feature)

    def add_signal(self, signal: TradingSignal) -> None:
        with self._lock:
            self._signals.append(signal)

    def add_portfolio_snapshot(self, snapshot: PortfolioSnapshot) -> None:
        with self._lock:
            self._portfolio.append(snapshot)

    def to_payload(self) -> dict[str, Any]:
        with self._lock:
            features = list(self._features)
            signals = list(self._signals)
            portfolio = list(self._portfolio)

        return asdict(
            DashboardSnapshot(
                feature_count=len(features),
                signal_count=len(signals),
                snapshot_count=len(portfolio),
                latest_feature=features[-1].to_payload() if features else None,
                latest_signal=signals[-1].to_payload() if signals else None,
                latest_portfolio=portfolio[-1].to_payload() if portfolio else None,
                recent_features=[feature.to_payload() for feature in features],
                recent_signals=[signal.to_payload() for signal in signals],
                recent_portfolio=[snapshot.to_payload() for snapshot in portfolio],
            )
        )
