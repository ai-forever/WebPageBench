#!/usr/bin/env bash
# Shared vLLM launcher for GUI agent models.
#
# The launch flags live in the Python registry (bench_eval/agents/*/__init__.py),
# so these scripts stay thin: they resolve the model, print the command, and exec
# it. Overriding a flag never means editing a script — pass it through.
#
#   MODEL=qwen3-vl-8b PORT=8000 TP=1 ./serve_qwen3_vl.sh
#   MODEL_PATH=/data/ckpt ./serve_opencua.sh --enable-prefix-caching

set -euo pipefail

AGENTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$AGENTS_DIR/../.." && pwd)"

serve_model() {
  local default_model="$1"
  shift

  local model="${MODEL:-$default_model}"
  local host="${HOST:-0.0.0.0}"
  local port="${PORT:-8000}"

  local args=(--host "$host" --port "$port")
  [[ -n "${TP:-}" ]] && args+=(--tp "$TP")
  [[ -n "${MAX_MODEL_LEN:-}" ]] && args+=(--max-model-len "$MAX_MODEL_LEN")
  [[ -n "${GPU_MEMORY_UTILIZATION:-}" ]] && args+=(--gpu-memory-utilization "$GPU_MEMORY_UTILIZATION")
  [[ -n "${MODEL_PATH:-}" ]] && args+=(--model-path "$MODEL_PATH")

  if ! command -v vllm >/dev/null 2>&1; then
    echo "vllm not found in PATH. Install it first: pip install vllm" >&2
    exit 1
  fi

  echo "[serve] model=$model host=$host port=$port"
  cd "$ROOT"
  exec python -m bench_eval.agents.cli.serve "$model" "${args[@]}" "$@"
}
