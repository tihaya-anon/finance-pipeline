#!/usr/bin/env bash

CONFIG_ENV_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

load_config_env() {
  local config_file="${FINANCE_PIPELINE_CONFIG:-$CONFIG_ENV_ROOT/config/development.yaml}"
  local secrets_file="${FINANCE_PIPELINE_SECRETS:-}"
  local shell_exports=""

  shell_exports="$(
    FINANCE_PIPELINE_CONFIG="$config_file" \
      FINANCE_PIPELINE_SECRETS="$secrets_file" \
      uv --directory "$CONFIG_ENV_ROOT/app" run python "$CONFIG_ENV_ROOT/scripts/python/config_export.py" --config "$config_file" --secrets "$secrets_file"
  )"
  eval "$shell_exports"
  export FINANCE_PIPELINE_CONFIG="$config_file"
  if [[ -n "$secrets_file" ]]; then
    export FINANCE_PIPELINE_SECRETS="$secrets_file"
  fi
  return 0
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  load_config_env
fi
