from __future__ import annotations

from common import run_cli
from finance_pipeline.sources.replay import parse_args, run


if __name__ == "__main__":
    raise SystemExit(run_cli(parse_args, run))
