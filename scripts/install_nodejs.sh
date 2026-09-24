#!/usr/bin/env bash
# Install Node.js (npx) into repo-local conda prefix for deepagents Playwright MCP.
#
# Usage (from repo root):
#   ./scripts/install_nodejs.sh
#
# Optional:
#   AGENT_BENCH_ROOT — repo root (default: parent of scripts/)
#   SKIP_NODE_INSTALL=1 — no-op when npx missing (exit 1)

set -euo pipefail

ROOT="${AGENT_BENCH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PREFIX="${NODE_CONDA_PREFIX:-$ROOT/.conda-node}"
NPX="$PREFIX/bin/npx"

if [[ -x "$NPX" ]]; then
  echo "Node.js already installed: $NPX"
  exit 0
fi

if [[ "${SKIP_NODE_INSTALL:-0}" == "1" ]]; then
  echo "SKIP_NODE_INSTALL=1 and npx missing: $NPX" >&2
  exit 1
fi

if ! command -v conda >/dev/null 2>&1; then
  cat >&2 <<EOF
conda not found; cannot install Node.js into $PREFIX.

Install Node.js with your system package manager, or set
NODE_BIN_DIR / NPX_BIN / PLAYWRIGHT_MCP_COMMAND.
EOF
  exit 1
fi

echo "==> Installing Node.js (conda-forge) into $PREFIX"
mkdir -p "$(dirname "$PREFIX")"
if [[ -d "$PREFIX/conda-meta" ]]; then
  conda install -y -p "$PREFIX" -c conda-forge nodejs=20
else
  conda create -y -p "$PREFIX" -c conda-forge nodejs=20
fi

if [[ ! -x "$NPX" ]]; then
  echo "Node install finished but npx missing: $NPX" >&2
  exit 1
fi

echo "Node.js ready: $NPX ($("$NPX" --version 2>/dev/null || true))"
