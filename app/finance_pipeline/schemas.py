from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


def parse_utc_timestamp(raw_value: str) -> datetime:
    return datetime.fromisoformat(raw_value.replace("Z", "+00:00")).astimezone(timezone.utc)


def format_utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class MarketTick:
    symbol: str
    event_time: datetime
    price: float
    quantity: float
    side: str

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> "MarketTick":
        return cls(
            symbol=row["symbol"],
            event_time=parse_utc_timestamp(row["event_time"]),
            price=float(row["price"]),
            quantity=float(row["quantity"]),
            side=row["side"],
        )

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["event_time"] = format_utc_timestamp(self.event_time)
        return payload


@dataclass(frozen=True)
class MarketFeature:
    symbol: str
    window_start: datetime
    window_end: datetime
    trade_count: int
    avg_price: float
    open_price: float
    close_price: float
    total_quantity: float
    price_return: float

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "MarketFeature":
        return cls(
            symbol=payload["symbol"],
            window_start=parse_utc_timestamp(payload["window_start"]),
            window_end=parse_utc_timestamp(payload["window_end"]),
            trade_count=int(payload["trade_count"]),
            avg_price=float(payload["avg_price"]),
            open_price=float(payload["open_price"]),
            close_price=float(payload["close_price"]),
            total_quantity=float(payload["total_quantity"]),
            price_return=float(payload["price_return"]),
        )

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["window_start"] = format_utc_timestamp(self.window_start)
        payload["window_end"] = format_utc_timestamp(self.window_end)
        return payload


@dataclass(frozen=True)
class TradingSignal:
    symbol: str
    generated_at: datetime
    window_end: datetime
    target_position: int
    reference_price: float
    price_return: float
    reason: str

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["generated_at"] = format_utc_timestamp(self.generated_at)
        payload["window_end"] = format_utc_timestamp(self.window_end)
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "TradingSignal":
        return cls(
            symbol=payload["symbol"],
            generated_at=parse_utc_timestamp(payload["generated_at"]),
            window_end=parse_utc_timestamp(payload["window_end"]),
            target_position=int(payload["target_position"]),
            reference_price=float(payload["reference_price"]),
            price_return=float(payload["price_return"]),
            reason=payload["reason"],
        )


@dataclass(frozen=True)
class PortfolioSnapshot:
    symbol: str
    timestamp: datetime
    action: str
    fill_price: float
    target_position: int
    current_position: int
    cash: float
    equity: float

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = format_utc_timestamp(self.timestamp)
        return payload
