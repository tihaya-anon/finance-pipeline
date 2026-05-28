from __future__ import annotations

try:
    from common import run_cli
except ModuleNotFoundError:  # pragma: no cover - import path differs for test/module usage
    from scripts.python.common import run_cli
from finance_pipeline.sources.replay import parse_args, run


if __name__ == "__main__":
    raise SystemExit(run_cli(parse_args, run))
