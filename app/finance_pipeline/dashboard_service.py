from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Event, Thread
import time

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from finance_pipeline.dashboard_state import DashboardState
from finance_pipeline.kafka_utils import build_consumer
from finance_pipeline.schemas import MarketFeature, PortfolioSnapshot, TradingSignal
from finance_pipeline.settings import SETTINGS


HTML_PATH = Path(__file__).resolve().parent / "web" / "dashboard.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve a local real-time dashboard for pipeline topics.")
    parser.add_argument("--host", default=SETTINGS.dashboard_host)
    parser.add_argument("--port", type=int, default=SETTINGS.dashboard_port)
    parser.add_argument("--bootstrap-servers", default=SETTINGS.bootstrap_servers)
    return parser.parse_args()


def run_consumer_loop(state: DashboardState, stop_event: Event, bootstrap_servers: str) -> None:
    consumer = build_consumer(
        [SETTINGS.features_topic, SETTINGS.signals_topic, SETTINGS.portfolio_topic],
        bootstrap_servers=bootstrap_servers,
        group_id="dashboard-service",
        consumer_timeout_ms=SETTINGS.consumer_timeout_ms,
    )

    try:
        while not stop_event.is_set():
            records = consumer.poll(timeout_ms=SETTINGS.consumer_timeout_ms)
            if not records:
                time.sleep(0.2)
                continue

            for topic_partition_records in records.values():
                for record in topic_partition_records:
                    if record.topic == SETTINGS.features_topic:
                        state.add_feature(MarketFeature.from_payload(record.value))
                    elif record.topic == SETTINGS.signals_topic:
                        state.add_signal(TradingSignal.from_payload(record.value))
                    elif record.topic == SETTINGS.portfolio_topic:
                        state.add_portfolio_snapshot(PortfolioSnapshot.from_payload(record.value))
    finally:
        consumer.close()


def build_app(bootstrap_servers: str) -> FastAPI:
    state = DashboardState(history_limit=SETTINGS.dashboard_history_limit)
    stop_event = Event()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        consumer_thread = Thread(
            target=run_consumer_loop,
            args=(state, stop_event, bootstrap_servers),
            daemon=True,
            name="dashboard-consumer",
        )
        consumer_thread.start()
        try:
            yield
        finally:
            stop_event.set()
            consumer_thread.join(timeout=3)

    app = FastAPI(title="Finance Pipeline Dashboard", lifespan=lifespan)

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return HTML_PATH.read_text(encoding="utf-8")

    @app.get("/api/state", response_class=JSONResponse)
    async def get_state() -> dict:
        return state.to_payload()

    return app


def main() -> None:
    args = parse_args()
    uvicorn.run(build_app(args.bootstrap_servers), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
