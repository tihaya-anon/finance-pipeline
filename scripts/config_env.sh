#!/usr/bin/env bash

CONFIG_ENV_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

load_config_env() {
  local config_file="${FINANCE_PIPELINE_CONFIG:-$CONFIG_ENV_ROOT/config/development.yaml}"
  local shell_exports=""

  shell_exports="$(
    FINANCE_PIPELINE_CONFIG="$config_file" \
      uv --directory "$CONFIG_ENV_ROOT/app" run config-export --config "$config_file"
  )"
  eval "$shell_exports"
  export FINANCE_PIPELINE_CONFIG="$config_file"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  load_config_env
fi
