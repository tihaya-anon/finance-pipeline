from finance_pipeline.repo_config import build_config_env, load_repo_config


def test_repo_config_loads_yaml_defaults() -> None:
    config = load_repo_config()

    assert config["ports"]["kafka"] == 39092
    assert config["sources"]["synthetic"]["symbol"] == "BTCUSDT"


def test_repo_config_can_render_shell_environment_values() -> None:
    env_values = build_config_env()

    assert env_values["HOST_KAFKA_PORT"] == "39092"
    assert env_values["REPLAY_SPEEDUP"] == "50.0"
    assert env_values["SYNTHETIC_SYMBOL"] == "BTCUSDT"
