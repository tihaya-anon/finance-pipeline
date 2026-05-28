from pathlib import Path

from finance_pipeline.config.repo_config import build_config_env, load_repo_config, redact_sensitive_env


def test_repo_config_loads_yaml_defaults() -> None:
    config = load_repo_config()

    assert config["ports"]["kafka"] == 39092
    assert config["sources"]["synthetic"]["symbol"] == "BTCUSDT"


def test_repo_config_can_render_shell_environment_values() -> None:
    env_values = build_config_env()

    assert env_values["HOST_KAFKA_PORT"] == "39092"
    assert env_values["REPLAY_SPEEDUP"] == "50.0"
    assert env_values["SYNTHETIC_SYMBOL"] == "BTCUSDT"


def test_repo_config_merges_optional_secrets_file(tmp_path: Path) -> None:
    config_path = tmp_path / "development.yaml"
    secrets_path = tmp_path / "development.secrets.yaml"
    config_path.write_text("sources:\n  onchain:\n    base_symbol: ETH\n", encoding="utf-8")
    secrets_path.write_text("sources:\n  onchain:\n    http_url: https://example.test/key\n", encoding="utf-8")

    config = load_repo_config(str(config_path), str(secrets_path))

    assert config["sources"]["onchain"]["base_symbol"] == "ETH"
    assert config["sources"]["onchain"]["http_url"] == "https://example.test/key"


def test_repo_config_redacts_sensitive_values_for_display() -> None:
    redacted = redact_sensitive_env(
        {
            "EVM_HTTP_URL": "https://example.test/secret",
            "EVM_WS_URL": "wss://example.test/secret",
            "HOST_KAFKA_PORT": "39092",
        }
    )

    assert redacted["EVM_HTTP_URL"] == "<redacted>"
    assert redacted["EVM_WS_URL"] == "<redacted>"
    assert redacted["HOST_KAFKA_PORT"] == "39092"
