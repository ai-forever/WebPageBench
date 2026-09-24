#!/usr/bin/env bash
# Установка Ouroboros (submodule ouroboros/) в общий venv репозитория (full_* eval).
#
#   python3 -m venv .venv && source .venv/bin/activate
#   pip install -r requirements-eval.txt
#   pip install -e ./deepeval -e ./browser-use -e ./hermes-ouroboros/sdk
#   git submodule update --init ouroboros
#   ./scripts/install_ouroboros.sh
#
# После установки start_dab_ouroboros_preview.sh найдёт CLI в .venv/bin/ouroboros.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=_resolve_ouroboros_bin.sh
source "$ROOT/scripts/_resolve_ouroboros_bin.sh"
OUROBOROS_REPO_DIR="${OUROBOROS_REPO_DIR:-$ROOT/ouroboros}"
OUROBOROS_GIT_URL="${OUROBOROS_GIT_URL:-https://github.com/razzant/ouroboros.git}"
PYTHON="${PYTHON:-python3}"

_resolve_bench_venv() {
  if [[ -n "${VIRTUAL_ENV:-}" && -f "${VIRTUAL_ENV}/bin/activate" ]]; then
    printf '%s\n' "$VIRTUAL_ENV"
    return 0
  fi
  if [[ -f "$ROOT/.venv/bin/activate" ]]; then
    printf '%s\n' "$ROOT/.venv"
    return 0
  fi
  return 1
}

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python не найден: $PYTHON" >&2
  exit 1
fi

if [[ ! -e "$OUROBOROS_REPO_DIR/.git" ]]; then
  if [[ "$OUROBOROS_REPO_DIR" == "$ROOT/ouroboros" ]]; then
    echo "Инициализация submodule ouroboros ..."
    if ! command -v git >/dev/null 2>&1; then
      echo "git не найден — нужен для submodule." >&2
      exit 1
    fi
    (cd "$ROOT" && git submodule update --init ouroboros)
  elif command -v git >/dev/null 2>&1; then
    echo "Cloning $OUROBOROS_GIT_URL → $OUROBOROS_REPO_DIR"
    mkdir -p "$(dirname "$OUROBOROS_REPO_DIR")"
    git clone --depth 1 "$OUROBOROS_GIT_URL" "$OUROBOROS_REPO_DIR"
  else
    echo "Каталог не найден: $OUROBOROS_REPO_DIR" >&2
    echo "Выполните: git submodule update --init ouroboros" >&2
    exit 1
  fi
fi

if [[ ! -e "$OUROBOROS_REPO_DIR/.git" ]]; then
  echo "Ouroboros repo не найден: $OUROBOROS_REPO_DIR" >&2
  exit 1
fi

VENV_DIR=""
if ! VENV_DIR="$(_resolve_bench_venv)"; then
  cat >&2 <<EOF
Не найден venv репозитория. Создайте и активируйте общий .venv:

  cd "$ROOT"
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements-eval.txt
  pip install -e ./deepeval -e ./browser-use -e ./hermes-ouroboros/sdk
  ./scripts/install_ouroboros.sh
EOF
  exit 1
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

cd "$OUROBOROS_REPO_DIR"

python -m pip install --upgrade pip setuptools wheel

# pip install -e . (с зависимостями) поднимает click до 8.4+ и ломает pin browser-use (8.3.1).
# Общие пакеты уже в eval-стеке; докидываем только ouroboros-специфичное.
python -m pip install -e . --no-deps
python -m pip install \
  'dulwich' \
  'croniter' \
  'tree-sitter>=0.23.2,<0.25' \
  'tree-sitter-language-pack>=0.9.1,<1.0' \
  'tzdata' \
  'claude-agent-sdk>=0.1.60' \
  'uvicorn[standard]'

BIN="$VENV_DIR/bin/ouroboros"
if [[ ! -x "$BIN" ]]; then
  echo "Установка завершилась, но $BIN не найден." >&2
  exit 1
fi

"$BIN" --help >/dev/null 2>&1 || true

echo "==> Patching ouroboros submodule defaults for WebPageBench (cheap models only)"
python3 "$ROOT/scripts/patch_ouroboros_for_bench.py" --repo-dir "$OUROBOROS_REPO_DIR"

if ! _verify_ouroboros_import "$ROOT" python; then
  echo "Ouroboros установлен, но import get_version не проходит из корня репозитория." >&2
  echo "Каталог ouroboros/ (submodule) перекрывает pip-пакет, когда cwd=WebPageBench." >&2
  echo "Проверка (из корня репо):" >&2
  echo "  env -u PYTHONPATH PYTHONSAFEPATH=1 python -P -c \"from ouroboros import get_version; print(get_version())\"" >&2
  echo "Server launch: ouroboros запускается через _run_ouroboros_server (без ROOT в PYTHONPATH/cwd)." >&2
  exit 1
fi

cat <<EOF

Ouroboros установлен в общий venv.

  VENV_DIR=$VENV_DIR
  OUROBOROS_REPO_DIR=$OUROBOROS_REPO_DIR
  OUROBOROS_BIN=$BIN

Опционально envs/_ouroboros.env:
  OUROBOROS_REPO_DIR=$OUROBOROS_REPO_DIR
  OUROBOROS_BIN=$BIN

Запуск стека:
  ./scripts/start_dab_ouroboros_preview.sh
EOF
