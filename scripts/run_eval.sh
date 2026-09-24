#!/usr/bin/env bash
# Прогон LLM-агента на обезличенном бенчмарке tests/bench через DeepEval.
# Сервисы WebPageBench (backend + frontend) должны быть уже запущены.
#
#   ./scripts/start_dab.sh          # в отдельном терминале
#   cp .env.eval.example .env     # LLM-ключи
#   ./scripts/run_eval.sh
#   ./scripts/run_eval.sh browser-use/gemini-2.5-flash
#   ./scripts/run_eval.sh ouroboros-cut/deepseek-v4-flash
#   ./scripts/run_eval.sh envs/runs/browser-use/gigachat-3-ultra.env
#
# Готовые конфиги: envs/runs/<harness>/<model>.env (см. scripts/gen_eval_envs.sh)
#
# Примеры:
#   EVAL_MAX_TASKS=3 ./scripts/run_eval.sh
#   EVAL_TASK_FILTER=ecommerce_basket ./scripts/run_eval.sh
#   DEEPEVAL_IDENTIFIER=bench-v2 DEEPEVAL_EXTRA_ARGS="--num-processes 2" ./scripts/run_eval.sh
#   EVAL_DRY_RUN=true ./scripts/run_eval.sh   # только create_track, без браузера

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=_eval_env.sh
source "$ROOT/scripts/_eval_env.sh"

if [[ $# -gt 0 && "$1" != -* ]]; then
  _eval_resolve_env_file "$1"
  shift
fi

_eval_load_dotenv
_eval_check_services

if [[ "${EVAL_REBUILD_DATASET}" == "true" ]]; then
  _eval_build_dataset
fi

_eval_run_deepeval "$@"
