# Shared environment for DeepEval WebPageBench runs (source from bash scripts).
# shellcheck shell=bash

: "${EVAL_ROOT:=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$EVAL_ROOT"

export PYTHONPATH="${EVAL_ROOT}/lib/src:${EVAL_ROOT}${PYTHONPATH:+:$PYTHONPATH}"
# pip install --user puts deepeval in ~/.local/bin
export PATH="${HOME}/.local/bin:${PATH}"

# Capture only values already present in the parent shell (exported on the CLI).
# Defaults below must not block .env from supplying EVAL_API_ADDRESS / ports.
declare -A _EVAL_SHELL_OVERRIDES=()
_EVAL_OVERRIDE_VARS=(
  EVAL_FRONTEND_HOST
  EVAL_API_ADDRESS
  DAB_API_PORT
  EVAL_REBUILD_DATASET
  EVAL_TASK_FILTER
  EVAL_MAX_TASKS
  DEEPEVAL_IDENTIFIER
  DEEPEVAL_CACHE_FOLDER
  DEEPEVAL_EXTRA_ARGS
  EVAL_OUTPUT_DIR
)
for _eval_var in "${_EVAL_OVERRIDE_VARS[@]}"; do
  if [[ -n "${!_eval_var+x}" ]]; then
    _EVAL_SHELL_OVERRIDES["$_eval_var"]="${!_eval_var}"
  fi
done
unset _eval_var

export EVAL_MOCK="${EVAL_MOCK:-bench}"
export EVAL_FRONTEND_HOST="${EVAL_FRONTEND_HOST:-127.0.0.1:5173}"
export EVAL_API_ADDRESS="${EVAL_API_ADDRESS:-localhost:9000}"
export EVAL_REBUILD_DATASET="${EVAL_REBUILD_DATASET:-true}"

export AGENT_MAX_STEPS="${AGENT_MAX_STEPS:-25}"
export AGENT_HEADLESS="${AGENT_HEADLESS:-true}"
export AGENT_HARNESS="${AGENT_HARNESS:-browser-use}"

export DEEPEVAL_EXTRA_ARGS="${DEEPEVAL_EXTRA_ARGS:---num-processes 2}"

_eval_prepare_output_dir() {
  if [[ -n "${EVAL_OUTPUT_DIR:-}" || -n "${EVAL_DATASET_PATH:-}" ]]; then
    _eval_ensure_deepeval_cache_folder
    return 0
  fi
  _eval_ensure_track_suffix
  EVAL_OUTPUT_DIR="$(
    python3 - <<'PY'
import os
from datetime import datetime
from bench_eval.results import default_run_directory

model = os.environ.get("LLM_MODEL", "gpt-4.1-mini")
harness = os.environ.get("AGENT_HARNESS", "browser-use")
suffix = os.environ.get("EVAL_TRACK_SUFFIX")
started_at = datetime.now()
print(default_run_directory(model, harness, started_at=started_at, track_suffix=suffix))
PY
  )"
  export EVAL_OUTPUT_DIR
  export EVAL_DATASET_PATH="${EVAL_OUTPUT_DIR}/dataset.json"
  _eval_ensure_deepeval_cache_folder
}

_eval_ensure_deepeval_cache_folder() {
  if [[ -n "${DEEPEVAL_CACHE_FOLDER:-}" ]]; then
    mkdir -p "$DEEPEVAL_CACHE_FOLDER"
    return 0
  fi
  if [[ -z "${EVAL_OUTPUT_DIR:-}" ]]; then
    return 0
  fi
  export DEEPEVAL_CACHE_FOLDER="${EVAL_OUTPUT_DIR}/.deepeval"
  mkdir -p "$DEEPEVAL_CACHE_FOLDER"
}

_eval_ensure_track_suffix() {
  if [[ -n "${EVAL_TRACK_SUFFIX:-}" ]]; then
    return 0
  fi
  export EVAL_TRACK_SUFFIX="$(python3 -c 'import uuid; print(uuid.uuid4().hex[:8])')"
}

_eval_default_deepeval_identifier() {
  python3 - <<'PY'
import os
from bench_eval.results import default_deepeval_identifier

print(
    default_deepeval_identifier(
        os.environ.get("EVAL_MOCK", "bench"),
        os.environ.get("AGENT_HARNESS", "browser-use"),
        os.environ.get("LLM_MODEL", "gpt-4.1-mini"),
    )
)
PY
}

_eval_ensure_deepeval_identifier() {
  if [[ -n "${DEEPEVAL_IDENTIFIER:-}" ]]; then
    return 0
  fi
  export DEEPEVAL_IDENTIFIER="$(_eval_default_deepeval_identifier)"
}

_eval_resolve_env_file() {
  local arg="${1:-}"
  if [[ -z "$arg" ]]; then
    return 0
  fi
  local candidate=""
  if [[ -f "$arg" ]]; then
    candidate="$arg"
  elif [[ -f "$EVAL_ROOT/envs/runs/${arg}.env" ]]; then
    candidate="$EVAL_ROOT/envs/runs/${arg}.env"
  elif [[ "$arg" == */* && -f "$EVAL_ROOT/envs/runs/${arg}.env" ]]; then
    candidate="$EVAL_ROOT/envs/runs/${arg}.env"
  elif [[ -f "$EVAL_ROOT/envs/${arg}.env" ]]; then
    candidate="$EVAL_ROOT/envs/${arg}.env"
  elif [[ -f "$EVAL_ROOT/envs/$arg" ]]; then
    candidate="$EVAL_ROOT/envs/$arg"
  else
    echo "Env-файл не найден: $arg" >&2
    echo "Ожидается путь или имя из envs/runs/<harness>/<model>.env" >&2
    echo "Примеры: browser-use/gemini-2.5-flash, ouroboros-cut/gigachat-3-ultra" >&2
    exit 1
  fi
  export EVAL_ENV_FILE="$candidate"
}

_eval_load_dotenv() {
  local env_file="${EVAL_ENV_FILE:-$EVAL_ROOT/.env}"
  if [[ -f "$env_file" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$env_file"
    set +a
  fi
  local var
  for var in "${_EVAL_OVERRIDE_VARS[@]}"; do
    if [[ -n "${_EVAL_SHELL_OVERRIDES[$var]+x}" ]]; then
      export "$var=${_EVAL_SHELL_OVERRIDES[$var]}"
    fi
  done
}

_eval_require_cmd() {
  local cmd=$1 hint=$2
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Команда не найдена: $cmd. $hint" >&2
    exit 1
  fi
}

_eval_require_deepeval() {
  if command -v deepeval >/dev/null 2>&1; then
    DEEPEVAL_CMD=(deepeval)
    return
  fi
  if python3 -c "import deepeval" >/dev/null 2>&1; then
    DEEPEVAL_CMD=(python3 -m deepeval)
    return
  fi
  echo "DeepEval не установлен. Из корня репозитория:" >&2
  echo "  git submodule update --init deepeval browser-use hermes-ouroboros ouroboros deepagents openhands openmanus" >&2
  echo "  pip install -r requirements-eval.txt && pip install -e ./deepeval -e ./browser-use -e ./hermes-ouroboros/sdk" >&2
  echo "  ./scripts/install_harnesses.sh  # для deepagents / openhands" >&2
  exit 1
}

_eval_check_harness_compat() {
  local harness="${AGENT_HARNESS:-browser-use}"
  if ! python3 "$EVAL_ROOT/scripts/check_harness_compat.py" --harness "$harness" >/dev/null 2>&1; then
    echo "Harness $harness не готов. Диагностика:" >&2
    python3 "$EVAL_ROOT/scripts/check_harness_compat.py" --harness "$harness" >&2 || true
    exit 1
  fi
}

_eval_wait_http() {
  local url=$1 label=$2 timeout=${3:-60}
  local i=0
  while (( i < timeout )); do
  # Backend отвечает 404 на /, но это значит, что порт слушает.
    if curl -sS --connect-timeout 1 -o /dev/null "$url" 2>/dev/null; then
      return 0
    fi
    sleep 1
    ((i++)) || true
  done
  echo "Сервис недоступен: $label ($url). Запустите ./scripts/start_dab.sh" >&2
  return 1
}

_eval_check_services() {
  if [[ "${EVAL_SKIP_SERVICE_CHECK:-false}" == "true" ]]; then
    return 0
  fi
  local api_port="${EVAL_API_ADDRESS##*:}"
  _eval_wait_http "http://127.0.0.1:${api_port}/" "WebPageBench backend" 30
  _eval_wait_http "http://${EVAL_FRONTEND_HOST}/" "WebPageBench frontend" 30
}

_eval_build_dataset() {
  _eval_require_cmd python3 "Нужен Python 3.12+."
  _eval_prepare_output_dir
  _eval_ensure_track_suffix
  local -a args=(--mock "$EVAL_MOCK" --frontend-host "$EVAL_FRONTEND_HOST")
  if [[ -n "${EVAL_DATASET_PATH:-}" ]]; then
    args+=(--output "$EVAL_DATASET_PATH")
  fi
  if [[ -n "${EVAL_TASK_FILTER:-}" ]]; then
    args+=(--task-filter "$EVAL_TASK_FILTER")
  fi
  if [[ -n "${EVAL_MAX_TASKS:-}" ]]; then
    args+=(--max-tasks "$EVAL_MAX_TASKS")
  fi
  python3 scripts/build_eval_dataset.py "${args[@]}"
}

_eval_run_deepeval() {
  _eval_require_deepeval
  _eval_check_harness_compat
  _eval_prepare_output_dir
  _eval_ensure_track_suffix
  _eval_ensure_deepeval_identifier
  local identifier="${DEEPEVAL_IDENTIFIER}"
  local -a extra=()
  if [[ -n "${DEEPEVAL_EXTRA_ARGS:-}" ]]; then
    # shellcheck disable=SC2206
    extra=($DEEPEVAL_EXTRA_ARGS)
  fi
  "${DEEPEVAL_CMD[@]}" test run tests/evals/test_agent_bench.py \
    --identifier "$identifier" \
    "${extra[@]}" \
    "$@"
}
