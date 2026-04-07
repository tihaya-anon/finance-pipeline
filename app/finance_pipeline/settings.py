from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from finance_pipeline.repo_config import get_config_value, load_repo_config, resolve_repo_path

PACKAGE_ROOT = Path(__file__).resolve().parent
APP_ROOT = PACKAGE_ROOT.parent
REPO_ROOT = APP_ROOT.parent
CONFIG = load_repo_config()


@dataclass(frozen=True)
class PipelineSettings:
    # Host-side bootstrap address. Docker-side SQL jobs still use the internal
    # broker address defined in the Flink SQL file.
    bootstrap_servers: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        f"localhost:{get_config_value(CONFIG, 'ports.kafka', 39092)}",
    )
    ticks_topic: str = os.getenv("TICKS_TOPIC", "market_ticks")
    features_topic: str = os.getenv("FEATURES_TOPIC", "market_features")
    signals_topic: str = os.getenv("SIGNALS_TOPIC", "trade_signals")
    portfolio_topic: str = os.getenv("PORTFOLIO_TOPIC", "portfolio_snapshots")
    consumer_timeout_ms: int = int(os.getenv("CONSUMER_TIMEOUT_MS", "2000"))
    replay_fixture_csv: Path = resolve_repo_path(get_config_value(CONFIG, "sources.replay.fixture_csv", "data/sample/btcusdt_ticks.csv"))
    replay_speedup: float = float(os.getenv("REPLAY_SPEEDUP", str(get_config_value(CONFIG, "sources.replay.speedup", 50.0))))
    replay_fast_speedup: float = float(
        os.getenv("REPLAY_FAST_SPEEDUP", str(get_config_value(CONFIG, "sources.replay.fast_speedup", 200.0)))
    )
    artifacts_dir: Path = REPO_ROOT / "artifacts"
    binance_stream_url: str = os.getenv(
        "BINANCE_STREAM_URL",
        str(get_config_value(CONFIG, "sources.binance.stream_url", "wss://data-stream.binance.vision/ws/btcusdt@aggTrade")),
    )
    evm_ws_url: str = os.getenv("EVM_WS_URL", str(get_config_value(CONFIG, "sources.onchain.ws_url", "")))
    evm_http_url: str = os.getenv("EVM_HTTP_URL", str(get_config_value(CONFIG, "sources.onchain.http_url", "")))
    evm_pair_address: str = os.getenv(
        "EVM_PAIR_ADDRESS", str(get_config_value(CONFIG, "sources.onchain.pair_address", ""))
    )
    evm_base_symbol: str = os.getenv("EVM_BASE_SYMBOL", str(get_config_value(CONFIG, "sources.onchain.base_symbol", "")))
    evm_quote_symbol: str = os.getenv(
        "EVM_QUOTE_SYMBOL", str(get_config_value(CONFIG, "sources.onchain.quote_symbol", ""))
    )
    evm_base_decimals: int = int(os.getenv("EVM_BASE_DECIMALS", str(get_config_value(CONFIG, "sources.onchain.base_decimals", 18))))
    evm_quote_decimals: int = int(
        os.getenv("EVM_QUOTE_DECIMALS", str(get_config_value(CONFIG, "sources.onchain.quote_decimals", 6)))
    )
    onchain_capture_output: Path = resolve_repo_path(
        os.getenv(
            "ONCHAIN_CAPTURE_OUTPUT",
            str(get_config_value(CONFIG, "sources.onchain.capture_output", "data/fixtures/onchain/uniswap_v2_eth_usdc_ticks.csv")),
        )
    )
    onchain_capture_max_events: int = int(
        os.getenv("ONCHAIN_CAPTURE_MAX_EVENTS", str(get_config_value(CONFIG, "sources.onchain.capture_max_events", 200)))
    )
    synthetic_output_csv: Path = resolve_repo_path(
        os.getenv(
            "SYNTHETIC_OUTPUT_CSV",
            str(get_config_value(CONFIG, "sources.synthetic.output_csv", "data/fixtures/generated/synthetic_ticks.csv")),
        )
    )
    synthetic_symbol: str = os.getenv(
        "SYNTHETIC_SYMBOL", str(get_config_value(CONFIG, "sources.synthetic.symbol", "BTCUSDT"))
    )
    synthetic_start_time: str = os.getenv(
        "SYNTHETIC_START_TIME", str(get_config_value(CONFIG, "sources.synthetic.start_time", "2026-01-01T00:00:00Z"))
    )
    synthetic_start_price: float = float(
        os.getenv("SYNTHETIC_START_PRICE", str(get_config_value(CONFIG, "sources.synthetic.start_price", 43100.0)))
    )
    synthetic_tick_count: int = int(
        os.getenv("SYNTHETIC_TICK_COUNT", str(get_config_value(CONFIG, "sources.synthetic.tick_count", 240)))
    )
    synthetic_interval_ms: int = int(
        os.getenv("SYNTHETIC_INTERVAL_MS", str(get_config_value(CONFIG, "sources.synthetic.interval_ms", 250)))
    )
    synthetic_quantity_min: float = float(
        os.getenv("SYNTHETIC_QUANTITY_MIN", str(get_config_value(CONFIG, "sources.synthetic.quantity_min", 0.05)))
    )
    synthetic_quantity_max: float = float(
        os.getenv("SYNTHETIC_QUANTITY_MAX", str(get_config_value(CONFIG, "sources.synthetic.quantity_max", 0.25)))
    )
    synthetic_volatility_bps: float = float(
        os.getenv("SYNTHETIC_VOLATILITY_BPS", str(get_config_value(CONFIG, "sources.synthetic.volatility_bps", 8.0)))
    )
    synthetic_drift_bps: float = float(
        os.getenv("SYNTHETIC_DRIFT_BPS", str(get_config_value(CONFIG, "sources.synthetic.drift_bps", 0.0)))
    )
    synthetic_seed: int = int(os.getenv("SYNTHETIC_SEED", str(get_config_value(CONFIG, "sources.synthetic.seed", 7))))


SETTINGS = PipelineSettings()
