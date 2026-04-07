from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from finance_pipeline.schemas import MarketTick


CSV_FIELDNAMES = ["symbol", "event_time", "price", "quantity", "side"]


def load_ticks(csv_path: Path) -> list[MarketTick]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        return [MarketTick.from_csv_row(row) for row in csv.DictReader(handle)]


def write_ticks(csv_path: Path, ticks: Iterable[MarketTick]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for tick in ticks:
            payload = tick.to_payload()
            writer.writerow(
                {
                    "symbol": payload["symbol"],
                    "event_time": payload["event_time"],
                    "price": payload["price"],
                    "quantity": payload["quantity"],
                    "side": payload["side"],
                }
            )
