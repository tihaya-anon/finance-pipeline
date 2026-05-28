from __future__ import annotations

from collections.abc import Callable


def run_cli(parse_args: Callable[[], object], run: Callable[[object], None]) -> int:
    try:
        run(parse_args())
    except KeyboardInterrupt:
        print("Interrupted; exiting cleanly.")
        return 0
    return 0
