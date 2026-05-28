from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


KNOWN_QUOTE_ASSETS = (
    "USDT",
    "USDC",
    "FDUSD",
    "BUSD",
    "BTC",
    "ETH",
    "USD",
    "EUR",
)


def parse_utc_timestamp(raw_value: str) -> datetime:
    return datetime.fromisoformat(raw_value.replace("Z", "+00:00")).astimezone(timezone.utc)


def format_utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def infer_spot_asset_pair(symbol: str) -> tuple[str, str]:
    normalized_symbol = symbol.upper()
    for quote_asset in sorted(KNOWN_QUOTE_ASSETS, key=len, reverse=True):
        if normalized_symbol.endswith(quote_asset) and len(normalized_symbol) > len(quote_asset):
            return normalized_symbol[: -len(quote_asset)], quote_asset
    return "", ""


def parse_instrument_fields(
    payload: dict[str, Any],
    *,
    symbol: str,
    default_venue: str = "",
    default_instrument_type: str = "spot",
) -> dict[str, str]:
    instrument_type = str(payload.get("instrument_type") or default_instrument_type)
    base_asset = str(payload.get("base_asset") or "")
    quote_asset = str(payload.get("quote_asset") or "")

    if instrument_type == "spot" and (not base_asset or not quote_asset):
        inferred_base_asset, inferred_quote_asset = infer_spot_asset_pair(symbol)
        base_asset = base_asset or inferred_base_asset
        quote_asset = quote_asset or inferred_quote_asset

    return {
        "venue": str(payload.get("venue") or default_venue),
        "instrument_type": instrument_type,
        "base_asset": base_asset,
        "quote_asset": quote_asset,
    }


@dataclass(frozen=True)
class MarketTick:
    symbol: str
    event_time: datetime
    price: float
    quantity: float
    side: str
    venue: str = ""
    instrument_type: str = "spot"
    base_asset: str = ""
    quote_asset: str = ""

    @property
    def instrument_key(self) -> str:
        return "|".join(part for part in (self.venue, self.instrument_type, self.symbol) if part)

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> "MarketTick":
        instrument_fields = parse_instrument_fields(row, symbol=row["symbol"], default_venue="replay")
        return cls(
            symbol=row["symbol"],
            event_time=parse_utc_timestamp(row["event_time"]),
            price=float(row["price"]),
            quantity=float(row["quantity"]),
            side=row["side"],
            **instrument_fields,
        )

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["event_time"] = format_utc_timestamp(self.event_time)
        return payload

    @classmethod
    def from_binance_agg_trade(cls, payload: dict[str, Any]) -> "MarketTick":
        """Map Binance aggTrade payloads into the internal normalized tick schema."""
        event_time = datetime.fromtimestamp(int(payload["T"]) / 1000, tz=timezone.utc)
        side = "sell" if payload["m"] else "buy"
        instrument_fields = parse_instrument_fields(
            {},
            symbol=payload["s"],
            default_venue="binance",
            default_instrument_type="spot",
        )
        return cls(
            symbol=payload["s"],
            event_time=event_time,
            price=float(payload["p"]),
            quantity=float(payload["q"]),
            side=side,
            **instrument_fields,
        )


@dataclass(frozen=True)
class MarketFeature:
    symbol: str
    window_start: datetime
    window_end: datetime
    trade_count: int
    avg_price: float
    vwap: float
    open_price: float
    close_price: float
    total_quantity: float
    buy_quantity: float
    sell_quantity: float
    volume_imbalance: float
    price_volatility: float
    price_return: float
    venue: str = ""
    instrument_type: str = "spot"
    base_asset: str = ""
    quote_asset: str = ""
    high_price: float = 0.0
    low_price: float = 0.0
    high_low_range: float = 0.0
    notional_volume: float = 0.0

    @property
    def instrument_key(self) -> str:
        return "|".join(part for part in (self.venue, self.instrument_type, self.symbol) if part)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "MarketFeature":
        instrument_fields = parse_instrument_fields(payload, symbol=payload["symbol"])
        return cls(
            symbol=payload["symbol"],
            window_start=parse_utc_timestamp(payload["window_start"]),
            window_end=parse_utc_timestamp(payload["window_end"]),
            trade_count=int(payload["trade_count"]),
            avg_price=float(payload["avg_price"]),
            vwap=float(payload.get("vwap", payload["avg_price"])),
            open_price=float(payload["open_price"]),
            close_price=float(payload["close_price"]),
            high_price=float(payload.get("high_price", payload["close_price"])),
            low_price=float(payload.get("low_price", payload["close_price"])),
            high_low_range=float(payload.get("high_low_range", 0.0)),
            total_quantity=float(payload["total_quantity"]),
            notional_volume=float(
                payload.get(
                    "notional_volume",
                    float(payload.get("vwap", payload["avg_price"])) * float(payload["total_quantity"]),
                )
            ),
            buy_quantity=float(payload.get("buy_quantity", 0.0)),
            sell_quantity=float(payload.get("sell_quantity", 0.0)),
            volume_imbalance=float(payload.get("volume_imbalance", 0.0)),
            price_volatility=float(payload.get("price_volatility", 0.0)),
            price_return=float(payload["price_return"]),
            **instrument_fields,
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
    target_position_size: float
    reference_price: float
    price_return: float
    reason: str
    venue: str = ""
    instrument_type: str = "spot"
    base_asset: str = ""
    quote_asset: str = ""

    @property
    def instrument_key(self) -> str:
        return "|".join(part for part in (self.venue, self.instrument_type, self.symbol) if part)

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["generated_at"] = format_utc_timestamp(self.generated_at)
        payload["window_end"] = format_utc_timestamp(self.window_end)
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "TradingSignal":
        instrument_fields = parse_instrument_fields(payload, symbol=payload["symbol"])
        return cls(
            symbol=payload["symbol"],
            generated_at=parse_utc_timestamp(payload["generated_at"]),
            window_end=parse_utc_timestamp(payload["window_end"]),
            target_position=int(payload["target_position"]),
            target_position_size=float(payload.get("target_position_size", payload["target_position"])),
            reference_price=float(payload["reference_price"]),
            price_return=float(payload["price_return"]),
            reason=payload["reason"],
            **instrument_fields,
        )


@dataclass(frozen=True)
class PortfolioSnapshot:
    symbol: str
    timestamp: datetime
    action: str
    fill_price: float
    target_position: int
    current_position: int
    target_position_size: float
    current_position_size: float
    cash: float
    equity: float
    venue: str = ""
    instrument_type: str = "spot"
    base_asset: str = ""
    quote_asset: str = ""

    @property
    def instrument_key(self) -> str:
        return "|".join(part for part in (self.venue, self.instrument_type, self.symbol) if part)

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = format_utc_timestamp(self.timestamp)
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PortfolioSnapshot":
        instrument_fields = parse_instrument_fields(payload, symbol=payload["symbol"])
        return cls(
            symbol=payload["symbol"],
            timestamp=parse_utc_timestamp(payload["timestamp"]),
            action=payload["action"],
            fill_price=float(payload["fill_price"]),
            target_position=int(payload["target_position"]),
            current_position=int(payload["current_position"]),
            target_position_size=float(payload.get("target_position_size", payload["target_position"])),
            current_position_size=float(payload.get("current_position_size", payload["current_position"])),
            cash=float(payload["cash"]),
            equity=float(payload["equity"]),
            **instrument_fields,
        )
