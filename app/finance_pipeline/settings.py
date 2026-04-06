from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


PACKAGE_ROOT = Path(__file__).resolve().parent
APP_ROOT = PACKAGE_ROOT.parent
REPO_ROOT = APP_ROOT.parent


@dataclass(frozen=True)
class PipelineSettings:
    # Host-side bootstrap address. Docker-side SQL jobs still use the internal
    # broker address defined in the Flink SQL file.
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:39092")
    ticks_topic: str = os.getenv("TICKS_TOPIC", "market_ticks")
    features_topic: str = os.getenv("FEATURES_TOPIC", "market_features")
    signals_topic: str = os.getenv("SIGNALS_TOPIC", "trade_signals")
    portfolio_topic: str = os.getenv("PORTFOLIO_TOPIC", "portfolio_snapshots")
    consumer_timeout_ms: int = int(os.getenv("CONSUMER_TIMEOUT_MS", "2000"))
    sample_ticks_csv: Path = REPO_ROOT / "data" / "sample" / "btcusdt_ticks.csv"
    artifacts_dir: Path = REPO_ROOT / "artifacts"
    dashboard_host: str = os.getenv("DASHBOARD_HOST", "127.0.0.1")
    dashboard_port: int = int(os.getenv("DASHBOARD_PORT", "8100"))
    dashboard_history_limit: int = int(os.getenv("DASHBOARD_HISTORY_LIMIT", "240"))
    binance_stream_url: str = os.getenv(
        "BINANCE_STREAM_URL",
        "wss://data-stream.binance.vision/ws/btcusdt@aggTrade",
    )


SETTINGS = PipelineSettings()
