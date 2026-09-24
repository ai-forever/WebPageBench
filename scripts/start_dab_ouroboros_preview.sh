#!/usr/bin/env bash
# WebPageBench backend + frontend preview + Ouroboros server в одном терминале.
# Для eval с ouroboros-full-isolated / ouroboros-full-evolving.
#
#   ./scripts/start_dab_ouroboros_preview.sh
#
# Ouroboros CLI: ./scripts/install_ouroboros.sh  (см. envs/_ouroboros.env.example)
#
# Остановка: Ctrl+C
#
# Переменные:
#   DAB_API_PORT          — backend (по умолчанию 9000)
#   BENCH_FRONTEND_PORT   — vite preview (5173)
#   OUROBOROS_BIN         — CLI (auto-detect: PATH, OUROBOROS_REPO_DIR/.venv, ouroboros/)
#   OUROBOROS_HOST        — 127.0.0.1
#   OUROBOROS_PORT        — предпочтительный порт (9123); при занятости ищется свободный рядом
#   OUROBOROS_PORT_SCAN_MAX — сколько портов сканировать от OUROBOROS_PORT (200)
#   OUROBOROS_DATA_DIR    — по умолчанию .cache/ouroboros-preview/data в корне репо
#   OUROBOROS_EVAL_RUN    — envs/runs/<harness>/<model> для LLM sync (default: ouroboros-full-isolated/openrouter-ouroboros)
#   SKIP_FRONTEND_BUILD=1 — не пересобирать frontend (если dist уже актуален)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=_wait_port.sh
source "$ROOT/scripts/_wait_port.sh"
# shellcheck source=_resolve_ouroboros_bin.sh
source "$ROOT/scripts/_resolve_ouroboros_bin.sh"

ENVS_DIR="$ROOT/envs"
if [[ -f "$ENVS_DIR/_ouroboros.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ENVS_DIR/_ouroboros.env"
  set +a
fi

API_PORT="${DAB_API_PORT:-9000}"
FRONTEND_PORT="${BENCH_FRONTEND_PORT:-5173}"
OUROBOROS_HOST="${OUROBOROS_HOST:-127.0.0.1}"
OUROBOROS_PORT_PREFERRED="${OUROBOROS_PORT:-9123}"
OUROBOROS_PORT_SCAN_MAX="${OUROBOROS_PORT_SCAN_MAX:-200}"
OUROBOROS_DATA_DIR="${OUROBOROS_DATA_DIR:-$ROOT/.cache/ouroboros-preview/data}"
OUROBOROS_PORT_FILE="${OUROBOROS_PORT_FILE:-$OUROBOROS_DATA_DIR/state/server_port}"

if [[ "$OUROBOROS_PORT_PREFERRED" == "$API_PORT" ]]; then
  echo "OUROBOROS_PORT ($OUROBOROS_PORT_PREFERRED) совпадает с DAB_API_PORT — задайте другой порт." >&2
  exit 1
fi

_resolve_ouroboros_port() {
  local preferred=$1
  local -a scan_starts=("$preferred" 19001)
  local start scan_max=$OUROBOROS_PORT_SCAN_MAX port
  for start in "${scan_starts[@]}"; do
    if port="$(find_bindable_port "$OUROBOROS_HOST" "$start" "$scan_max" "$API_PORT" "$FRONTEND_PORT")"; then
      printf '%s\n' "$port"
      return 0
    fi
  done
  return 1
}

if ! OUROBOROS_PORT="$(_resolve_ouroboros_port "$OUROBOROS_PORT_PREFERRED")"; then
  cat >&2 <<EOF
Не удалось найти свободный TCP-порт для Ouroboros на ${OUROBOROS_HOST}
(сканировали ${OUROBOROS_PORT_PREFERRED}–$((OUROBOROS_PORT_PREFERRED + OUROBOROS_PORT_SCAN_MAX - 1)) и 19001–$((19001 + OUROBOROS_PORT_SCAN_MAX - 1)),
исключая WebPageBench :${API_PORT} и frontend :${FRONTEND_PORT}).

На общих машинах низкие порты (9001–9010) часто заняты другими процессами.
Проверка: ss -tlnp | grep -E ':(912[0-9]|913[0-9]|190[0-9]{2})'
Задайте свободный порт явно: OUROBOROS_PORT=9200 ./scripts/start_dab_ouroboros_preview.sh
EOF
  exit 1
fi

if [[ "$OUROBOROS_PORT" != "$OUROBOROS_PORT_PREFERRED" ]]; then
  echo "Ouroboros: порт ${OUROBOROS_PORT_PREFERRED} занят, используем :${OUROBOROS_PORT}"
fi

export OUROBOROS_DATA_DIR OUROBOROS_PORT_FILE
mkdir -p "$(dirname "$OUROBOROS_PORT_FILE")"

if ! OUROBOROS_BIN="$(_ensure_ouroboros_cli "$ROOT")"; then
  _print_ouroboros_install_hint "$ROOT"
  exit 1
fi
export OUROBOROS_BIN

export DAB_API_PORT="$API_PORT"
export VITE_API_URL="${VITE_API_URL:-http://127.0.0.1:${API_PORT}/}"

BACKEND_PID=""
FRONTEND_PID=""
OUROBOROS_PID=""

cleanup() {
  [[ -n "$OUROBOROS_PID" ]] && kill "$OUROBOROS_PID" 2>/dev/null || true
  [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  [[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait_http() {
  local url=$1 label=$2 timeout=${3:-90}
  local i=0
  while (( i < timeout )); do
    if curl -fsS --connect-timeout 1 -o /dev/null "$url" 2>/dev/null; then
      return 0
    fi
    sleep 1
    ((i++)) || true
  done
  echo "Сервис недоступен: $label ($url)" >&2
  return 1
}

if [[ "${SKIP_FRONTEND_BUILD:-0}" != "1" ]]; then
  echo "Building frontend with VITE_API_URL=${VITE_API_URL} ..."
  (cd "$ROOT/site/frontend" && npm run build)
else
  echo "SKIP_FRONTEND_BUILD=1 — пропуск npm run build"
fi

echo "Using Ouroboros CLI: $OUROBOROS_BIN"

if [[ -d "$ROOT/ouroboros/ouroboros" ]] || [[ -f "$ROOT/ouroboros/ouroboros/config.py" ]]; then
  python3 "$ROOT/scripts/patch_ouroboros_for_bench.py" --repo-dir "$ROOT/ouroboros"
fi

OUROBOROS_EVAL_RUN="${OUROBOROS_EVAL_RUN:-ouroboros-full-isolated/openrouter-ouroboros}"
OUROBOROS_EVAL_ENV="$ROOT/envs/runs/${OUROBOROS_EVAL_RUN}.env"
if [[ -f "$OUROBOROS_EVAL_ENV" ]]; then
  echo "Loading eval env for Ouroboros server: $OUROBOROS_EVAL_ENV"
  set -a
  # shellcheck disable=SC1090
  source "$OUROBOROS_EVAL_ENV"
  set +a
else
  echo "Eval env not found for Ouroboros preview: $OUROBOROS_EVAL_ENV" >&2
  exit 1
fi

export PYTHONPATH="${ROOT}/lib/src:${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<'PY'
from bench_eval.ouroboros_llm_sync import validate_ouroboros_llm_settings

validate_ouroboros_llm_settings()
PY

(cd "$ROOT/site/backend" && python3 -c "import config; from main import app; app.run(host='0.0.0.0', port=config.API_PORT, debug=False, use_reloader=False)") &
BACKEND_PID=$!

(cd "$ROOT/site/frontend" && npm run preview -- --host 127.0.0.1 --port "$FRONTEND_PORT" --strictPort) &
FRONTEND_PID=$!

export OUROBOROS_SERVER_HOST="$OUROBOROS_HOST"
export OUROBOROS_SERVER_PORT="$OUROBOROS_PORT"

_run_ouroboros_server "$OUROBOROS_BIN" server --host "$OUROBOROS_HOST" --port "$OUROBOROS_PORT" &
OUROBOROS_PID=$!

_read_ouroboros_bound_port() {
  local preferred=$1 port_file=$2 timeout=${3:-30}
  local i=0 actual=""
  while (( i < timeout )); do
    if [[ -f "$port_file" ]]; then
      actual="$(tr -d '[:space:]' < "$port_file")"
      if [[ "$actual" =~ ^[0-9]+$ ]]; then
        printf '%s\n' "$actual"
        return 0
      fi
    fi
    if ! kill -0 "$OUROBOROS_PID" 2>/dev/null; then
      return 1
    fi
    sleep 1
    ((i++)) || true
  done
  printf '%s\n' "$preferred"
}

wait_port 127.0.0.1 "$API_PORT" 90 || { echo "Backend did not start on :${API_PORT}" >&2; exit 1; }
kill -0 "$BACKEND_PID" 2>/dev/null || { echo "Backend process exited" >&2; exit 1; }

wait_port 127.0.0.1 "$FRONTEND_PORT" 120 || { echo "Frontend preview did not start on :${FRONTEND_PORT}" >&2; exit 1; }
kill -0 "$FRONTEND_PID" 2>/dev/null || {
  echo "Frontend preview failed (port :${FRONTEND_PORT} busy?)." >&2
  exit 1
}

if ! OUROBOROS_BOUND_PORT="$(_read_ouroboros_bound_port "$OUROBOROS_PORT" "$OUROBOROS_PORT_FILE" 60)"; then
  echo "Ouroboros process exited до записи порта в ${OUROBOROS_PORT_FILE}." >&2
  exit 1
fi
if [[ "$OUROBOROS_BOUND_PORT" != "$OUROBOROS_PORT" ]]; then
  echo "Ouroboros привязался к :${OUROBOROS_BOUND_PORT} (запрошен :${OUROBOROS_PORT})"
  OUROBOROS_PORT="$OUROBOROS_BOUND_PORT"
fi

wait_http "http://${OUROBOROS_HOST}:${OUROBOROS_PORT}/api/health" "Ouroboros API" 120 || {
  kill -0 "$OUROBOROS_PID" 2>/dev/null || echo "Ouroboros process exited." >&2
  exit 1
}

_sync_ouroboros_server_llm_after_start "http://${OUROBOROS_HOST}:${OUROBOROS_PORT}" "$ROOT" || exit 1
export OUROBOROS_URL="http://${OUROBOROS_HOST}:${OUROBOROS_PORT}"

echo "Backend:            http://127.0.0.1:${API_PORT}/"
echo "Frontend (preview): http://127.0.0.1:${FRONTEND_PORT}/"
echo "Ouroboros API:      http://${OUROBOROS_HOST}:${OUROBOROS_PORT}/"
if [[ "${OUROBOROS_PORT}" != "${OUROBOROS_PORT_PREFERRED}" ]]; then
  echo "Для eval задайте: export OUROBOROS_URL=http://${OUROBOROS_HOST}:${OUROBOROS_PORT}"
fi
echo "Ctrl+C — остановить все три сервиса."

wait "$BACKEND_PID" "$FRONTEND_PID" "$OUROBOROS_PID"
