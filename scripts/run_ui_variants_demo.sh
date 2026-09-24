#!/usr/bin/env bash
# Демо UI-вариантов: регистрация треков по tests/bench/configs/.
# Backend и frontend должны быть уже запущены (например ./scripts/start_dab.sh).
#
#   ./scripts/run_ui_variants_demo.sh              # sample (12 профилей)
#   ./scripts/run_ui_variants_demo.sh --all        # все профили
#   PROFILE=hotels_date_text ./scripts/run_ui_variants_demo.sh --profile
#   ./scripts/run_ui_variants_demo.sh --record     # + запись demo.webm

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

API_PORT="${DAB_API_PORT:-9000}"
FRONTEND_PORT="${BENCH_FRONTEND_PORT:-5173}"

export BENCH_API_ADDRESS="${BENCH_API_ADDRESS:-localhost:${API_PORT}}"
export BENCH_FRONTEND_URL="${BENCH_FRONTEND_URL:-http://127.0.0.1:${FRONTEND_PORT}}"
export PYTHONPATH="${ROOT}:${ROOT}/lib/src:${ROOT}/tests/bench${PYTHONPATH:+:$PYTHONPATH}"

RECORD=0
DEMO_ARGS=(--sample)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all) DEMO_ARGS=(--all) ;;
    --sample) DEMO_ARGS=(--sample) ;;
    --profile)
      [[ -n "${PROFILE:-}" ]] || { echo "Set PROFILE=hotels_date_text" >&2; exit 1; }
      DEMO_ARGS=(--profile "$PROFILE")
      ;;
    --record) RECORD=1 ;;
    -h|--help)
      sed -n '2,9p' "$0"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
  shift
done

python3 "$ROOT/scripts/ui_variants_demo.py" "${DEMO_ARGS[@]}"

if [[ "$RECORD" -eq 1 ]]; then
  python3 "$ROOT/scripts/record_ui_variants_demo.py" "${DEMO_ARGS[@]}"
fi

echo ""
echo "Каталог: tests/bench/build/ui_variants_demo_catalog.md"
