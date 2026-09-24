# Resolve npm/npx paths when Node is installed outside default PATH (conda/nvm).
# shellcheck shell=bash

_resolve_npm() {
  if [[ -n "${NPM_BIN:-}" && -x "${NPM_BIN}" ]]; then
    printf '%s\n' "$NPM_BIN"
    return 0
  fi
  if command -v npm >/dev/null 2>&1; then
    command -v npm
    return 0
  fi
  if [[ -n "${NODE_BIN_DIR:-}" && -x "${NODE_BIN_DIR}/npm" ]]; then
    printf '%s\n' "${NODE_BIN_DIR}/npm"
    return 0
  fi
  if [[ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]]; then
    # shellcheck disable=SC1091
    source "${NVM_DIR:-$HOME/.nvm}/nvm.sh"
    if command -v npm >/dev/null 2>&1; then
      command -v npm
      return 0
    fi
  fi
  if [[ -n "${CONDA_PREFIX:-}" && -x "${CONDA_PREFIX}/bin/npm" ]]; then
    printf '%s\n' "${CONDA_PREFIX}/bin/npm"
    return 0
  fi
  return 1
}

_resolve_npx() {
  local candidate=""

  if [[ -n "${PLAYWRIGHT_MCP_COMMAND:-}" ]]; then
    if [[ -x "${PLAYWRIGHT_MCP_COMMAND}" ]]; then
      printf '%s\n' "$PLAYWRIGHT_MCP_COMMAND"
      return 0
    fi
    if command -v "${PLAYWRIGHT_MCP_COMMAND}" >/dev/null 2>&1; then
      command -v "${PLAYWRIGHT_MCP_COMMAND}"
      return 0
    fi
  fi

  if [[ -n "${NPX_BIN:-}" && -x "${NPX_BIN}" ]]; then
    printf '%s\n' "$NPX_BIN"
    return 0
  fi

  if command -v npx >/dev/null 2>&1; then
    command -v npx
    return 0
  fi

  if [[ -n "${NODE_BIN_DIR:-}" && -x "${NODE_BIN_DIR}/npx" ]]; then
    printf '%s\n' "${NODE_BIN_DIR}/npx"
    return 0
  fi

  if [[ -n "${NPM_BIN:-}" && -x "${NPM_BIN}" ]]; then
    candidate="$(dirname "${NPM_BIN}")/npx"
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  fi

  if candidate="$(_resolve_npm 2>/dev/null)"; then
    candidate="$(dirname "$candidate")/npx"
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  fi

  if [[ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]]; then
    # shellcheck disable=SC1091
    source "${NVM_DIR:-$HOME/.nvm}/nvm.sh"
    if command -v npx >/dev/null 2>&1; then
      command -v npx
      return 0
    fi
  fi

  if [[ -n "${CONDA_PREFIX:-}" && -x "${CONDA_PREFIX}/bin/npx" ]]; then
    printf '%s\n' "${CONDA_PREFIX}/bin/npx"
    return 0
  fi

  local root="${AGENT_BENCH_ROOT:-}"
  local node_prefix="${NODE_CONDA_PREFIX:-}"
  if [[ -z "$node_prefix" && -n "$root" ]]; then
    node_prefix="${root}/.conda-node"
  fi
  if [[ -n "$node_prefix" && -x "${node_prefix}/bin/npx" ]]; then
    printf '%s\n' "${node_prefix}/bin/npx"
    return 0
  fi

  return 1
}
