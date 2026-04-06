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
    binance_stream_url: str = os.getenv(
        "BINANCE_STREAM_URL",
        "wss://data-stream.binance.vision/ws/btcusdt@aggTrade",
    )
    evm_ws_url: str = os.getenv("EVM_WS_URL", "")
    evm_http_url: str = os.getenv("EVM_HTTP_URL", "")
    evm_pair_address: str = os.getenv("EVM_PAIR_ADDRESS", "")
    evm_base_symbol: str = os.getenv("EVM_BASE_SYMBOL", "")
    evm_quote_symbol: str = os.getenv("EVM_QUOTE_SYMBOL", "")
    evm_base_decimals: int = int(os.getenv("EVM_BASE_DECIMALS", "18"))
    evm_quote_decimals: int = int(os.getenv("EVM_QUOTE_DECIMALS", "6"))


SETTINGS = PipelineSettings()
