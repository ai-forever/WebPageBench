#!/usr/bin/env bash
# Regenerate envs/runs/<harness>/<model>.env from _common + models + harnesses fragments.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENVS="$ROOT/envs"
RUNS="$ENVS/runs"

HARNESSes=(
  browser-use
  deepagents
  openhands
  openmanus
  ouroboros-cut
  ouroboros-full-isolated
  ouroboros-full-evolving
)
MODELS=(
  gemini-2.5-flash
  gemini-3.8-flash
  deepseek-v4-flash
  deepseek-v4.1-flash
  gpt-5.5
  gpt-5.6-luna
  claude-opus-4-7
  glm-5.1
  glm-5.2
  minimax-m2.7
  gigachat-3-ultra
  openrouter-ouroboros
)

for harness in "${HARNESSes[@]}"; do
  for model in "${MODELS[@]}"; do
    out="$RUNS/$harness/$model.env"
    mkdir -p "$(dirname "$out")"
    cat >"$out" <<EOF
# Composed eval env: $harness + $model
# Usage: ./scripts/run_eval.sh $harness/$model

_ENVS_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck disable=SC1091
source "\$_ENVS_DIR/_common.env"
source "\$_ENVS_DIR/models/${model}.env"
source "\$_ENVS_DIR/_load_keys.sh"
load_openrouter_api_key "\$_ENVS_DIR"
load_gigachat_secrets "\$_ENVS_DIR"
source "\$_ENVS_DIR/harnesses/${harness}.env"
EOF
  done
done

# GUI-модели (скриншот → координаты) не комбинируются со всеми LLM: у каждой
# семьи свой чекпоинт и свой vLLM. Поэтому пары задаются явно.
GUI_PAIRS=(
  "qwen3-vl:qwen3-vl-8b"
  "uitars:uitars-1.5-7b"
  "jedi:jedi-7b"
  "opencua:opencua-7b"
  "evocua:evocua-s2"
)

for pair in "${GUI_PAIRS[@]}"; do
  harness="${pair%%:*}"
  model="${pair##*:}"
  out="$RUNS/$harness/$model.env"
  mkdir -p "$(dirname "$out")"
  cat >"$out" <<EOF
# Composed eval env: $harness + $model (self-hosted vLLM)
# Usage:
#   python -m bench_eval.agents.cli.serve $model     # в отдельном терминале
#   ./scripts/run_eval.sh $harness/$model

_ENVS_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck disable=SC1091
source "\$_ENVS_DIR/_common.env"
source "\$_ENVS_DIR/models/${model}.env"
source "\$_ENVS_DIR/harnesses/${harness}.env"
EOF
done

# Модели, уже развёрнутые на платформе GigaHF: своего vLLM нет, нужен только
# токен, поэтому секрет грузится ДО фрагмента модели (тот разворачивает $GIGAHF_TOKEN).
GIGAHF_PAIRS=(
  "qwen3-vl:gigahf-qwen3.8-27b"
  "qwen3-vl:gigahf-qwen3.6-27b"
)

for pair in "${GIGAHF_PAIRS[@]}"; do
  harness="${pair%%:*}"
  model="${pair##*:}"
  out="$RUNS/$harness/$model.env"
  mkdir -p "$(dirname "$out")"
  cat >"$out" <<EOF
# Composed eval env: $harness + $model (GigaHF, модель уже развёрнута на платформе)
# Usage:
#   cp envs/_gigahf.env.example envs/_gigahf.env   # и вписать GIGAHF_TOKEN
#   ./scripts/run_eval.sh $harness/$model

_ENVS_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck disable=SC1091
source "\$_ENVS_DIR/_common.env"
source "\$_ENVS_DIR/_load_keys.sh"
load_gigahf_token "\$_ENVS_DIR"
source "\$_ENVS_DIR/models/${model}.env"
source "\$_ENVS_DIR/harnesses/${harness}.env"
EOF
done

count="$(find "$RUNS" -name '*.env' | wc -l)"
echo "Generated ${count} run env files under envs/runs/"
