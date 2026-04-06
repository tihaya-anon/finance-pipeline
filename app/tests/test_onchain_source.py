from datetime import datetime, timezone

from finance_pipeline.onchain_source import PairConfig, tick_from_swap_log


def build_swap_log(data_hex: str) -> dict[str, str]:
    return {
        "data": data_hex,
        "blockHash": "0xabc",
    }


def test_tick_from_swap_log_maps_buy_of_base_token() -> None:
    pair = PairConfig(
        pair_address="0xpair",
        base_symbol="ETH",
        quote_symbol="USDC",
        base_decimals=18,
        quote_decimals=6,
    )
    block_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    amount0_in = 0
    amount1_in = 3200 * 10**6
    amount0_out = 10**18
    amount1_out = 0
    data_hex = "0x" + "".join(f"{value:064x}" for value in [amount0_in, amount1_in, amount0_out, amount1_out])

    tick = tick_from_swap_log(build_swap_log(data_hex), pair, block_time)

    assert tick.symbol == "ETHUSDC"
    assert tick.side == "buy"
    assert tick.quantity == 1.0
    assert tick.price == 3200.0
    assert tick.event_time == block_time


def test_tick_from_swap_log_maps_sell_of_base_token() -> None:
    pair = PairConfig(
        pair_address="0xpair",
        base_symbol="ETH",
        quote_symbol="USDC",
        base_decimals=18,
        quote_decimals=6,
    )
    block_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    amount0_in = 2 * 10**18
    amount1_in = 0
    amount0_out = 0
    amount1_out = 6400 * 10**6
    data_hex = "0x" + "".join(f"{value:064x}" for value in [amount0_in, amount1_in, amount0_out, amount1_out])

    tick = tick_from_swap_log(build_swap_log(data_hex), pair, block_time)

    assert tick.symbol == "ETHUSDC"
    assert tick.side == "sell"
    assert tick.quantity == 2.0
    assert tick.price == 3200.0
