# Secret loading for composed envs/runs/*.env (source after model fragment).
# shellcheck shell=bash

load_openrouter_api_key() {
  local envs_dir="${1:?}"
  local secrets="$envs_dir/_openrouter.env"
  if [[ ! -f "$secrets" ]]; then
    return 0
  fi
  # Always source: LLM_BASE_URL (proxy) lives here. Keep a pre-set key.
  local keep_key="${OPENROUTER_API_KEY:-}"
  # shellcheck disable=SC1091
  source "$secrets"
  if [[ -n "$keep_key" ]]; then
    OPENROUTER_API_KEY="$keep_key"
  fi
}

load_gigachat_secrets() {
  local envs_dir="${1:?}"
  if [[ -n "${GIGACHAT_TOKEN:-}" || -n "${GIGACHAT_CREDENTIALS:-}" ]]; then
    return 0
  fi
  local secrets="$envs_dir/_gigachat.env"
  if [[ -f "$secrets" ]]; then
    # shellcheck disable=SC1091
    source "$secrets"
  fi
}

load_gigahf_token() {
  local envs_dir="${1:?}"
  if [[ -n "${GIGAHF_TOKEN:-}" ]]; then
    return 0
  fi
  local secrets="$envs_dir/_gigahf.env"
  if [[ -f "$secrets" ]]; then
    # shellcheck disable=SC1091
    source "$secrets"
  fi
}
