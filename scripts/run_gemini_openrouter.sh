#!/usr/bin/env bash
# Скоринг WebPageBench с google/gemini-2.5-flash через OpenRouter.
# Сервисы WebPageBench (backend + frontend) должны быть уже запущены.
#
#   1. ./scripts/start_dab.sh
#   2. Укажите OPENROUTER_API_KEY (см. ниже или в .env)
#   3. ./scripts/run_gemini_openrouter.sh
#
# Примеры:
#   export OPENROUTER_API_KEY=sk-or-v1-...
#   ./scripts/run_gemini_openrouter.sh
#   EVAL_MAX_TASKS=3 ./scripts/run_gemini_openrouter.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=_eval_env.sh
source "$ROOT/scripts/_eval_env.sh"

# Сначала .env — ключ можно задать там (OPENROUTER_API_KEY=...).
_eval_load_dotenv

# --- или вставьте ключ сюда ---
OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-sk-or-v1-...}"
# ------------------------------

if [[ -z "$OPENROUTER_API_KEY" || "$OPENROUTER_API_KEY" == "sk-or-v1-..." ]]; then
  echo "Укажите OPENROUTER_API_KEY одним из способов:" >&2
  echo "  export OPENROUTER_API_KEY=sk-or-v1-..." >&2
  echo "  echo 'OPENROUTER_API_KEY=sk-or-v1-...' >> .env" >&2
  echo "  отредактируйте переменную в scripts/run_gemini_openrouter.sh" >&2
  exit 1
fi

# После .env — OpenRouter-настройки имеют приоритет над OPENAI_API_KEY из .env.
export LLM_PROVIDER=openrouter
export LLM_MODEL="${LLM_MODEL:-google/gemini-2.5-flash}"
export LLM_BASE_URL="${LLM_BASE_URL:-https://openrouter.ai/api/v1}"
export OPENROUTER_API_KEY
export OPENAI_API_KEY="$OPENROUTER_API_KEY"

export EVAL_TASK_FILTER="${EVAL_TASK_FILTER:-ecommerce_basket_any_product}"
export EVAL_MAX_TASKS="${EVAL_MAX_TASKS:-1}"

_eval_check_services
_eval_build_dataset
_eval_run_deepeval "$@"
