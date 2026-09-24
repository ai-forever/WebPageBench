# Resolve ouroboros CLI path. Source from bash scripts.
# shellcheck shell=bash

_resolve_ouroboros_repo_dir() {
  local root="${1:-}"
  local repo_dir="${OUROBOROS_REPO_DIR:-}"
  if [[ -z "$repo_dir" ]]; then
    if [[ -n "$root" ]]; then
      printf '%s\n' "$root/ouroboros"
    fi
    return 0
  fi
  if [[ -n "$root" && "$repo_dir" != /* ]]; then
    printf '%s\n' "$root/$repo_dir"
    return 0
  fi
  printf '%s\n' "$repo_dir"
}

_resolve_ouroboros_bin() {
  local root="${1:-}"
  local candidate="${OUROBOROS_BIN:-ouroboros}"

  if [[ -n "$candidate" && -f "$candidate" && -x "$candidate" ]]; then
    printf '%s\n' "$(cd "$(dirname "$candidate")" && pwd)/$(basename "$candidate")"
    return 0
  fi

  if command -v "$candidate" >/dev/null 2>&1; then
    command -v "$candidate"
    return 0
  fi

  local -a search_paths=()
  if [[ -n "${VENV_PATH:-}" ]]; then
    search_paths+=("${VENV_PATH}/bin/ouroboros")
  fi
  local repo_dir=""
  repo_dir="$(_resolve_ouroboros_repo_dir "$root")"
  if [[ -n "$repo_dir" ]]; then
    search_paths+=(
      "${repo_dir}/.venv/bin/ouroboros"
      "${repo_dir}/venv/bin/ouroboros"
    )
  fi
  if [[ -n "$root" ]]; then
    search_paths+=(
      "$root/.venv/bin/ouroboros"
      "$root/../.venv/bin/ouroboros"
      "$root/../ouroboros/.venv/bin/ouroboros"
      "$root/ouroboros/.venv/bin/ouroboros"
    )
  fi
  if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    search_paths+=("${VIRTUAL_ENV}/bin/ouroboros")
  fi
  search_paths+=(
    "${HOME}/.local/bin/ouroboros"
    "${HOME}/Ouroboros/Ouroboros/bin/ouroboros"
    "/opt/Ouroboros/Ouroboros/bin/ouroboros"
  )

  local path
  for path in "${search_paths[@]}"; do
    if [[ -x "$path" ]]; then
      printf '%s\n' "$path"
      return 0
    fi
  done

  return 1
}

_ensure_ouroboros_cli() {
  local root="${1:-}"
  local resolved=""

  if resolved="$(_resolve_ouroboros_bin "$root")"; then
    printf '%s\n' "$resolved"
    return 0
  fi

  if [[ "${SKIP_OUROBOROS_INSTALL:-0}" == "1" ]]; then
    return 1
  fi

  if [[ -z "$root" || ! -f "$root/scripts/install_ouroboros.sh" ]]; then
    return 1
  fi

  echo "Ouroboros CLI not found — running install_ouroboros.sh ..." >&2
  if [[ ! -e "$root/ouroboros/.git" ]] && command -v git >/dev/null 2>&1; then
    echo "Initializing ouroboros submodule ..." >&2
    git -C "$root" submodule update --init ouroboros
  fi

  env -u PYTHONPATH "$root/scripts/install_ouroboros.sh"

  _resolve_ouroboros_bin "$root"
}

# Run ouroboros CLI/server without WebPageBench ROOT on PYTHONPATH.
# ``$ROOT/ouroboros/`` (submodule checkout) shadows the pip-installed package when
# cwd is the repo root (Python puts "" on sys.path). Use PYTHONSAFEPATH and a neutral cwd.
_verify_ouroboros_import() {
  local root="${1:-}"
  local python_cmd="${2:-python}"
  local check_cwd="${root:-.}"
  local safe_cwd="${TMPDIR:-/tmp}"

  if [[ ! -d "$check_cwd" ]]; then
    check_cwd="$safe_cwd"
  fi

  (
    cd "$check_cwd"
    env -u PYTHONPATH PYTHONSAFEPATH=1 "$python_cmd" -c "from ouroboros import get_version; get_version()"
  )
}

_run_ouroboros_server() {
  local safe_cwd="${TMPDIR:-/tmp}"
  local llm_env_file=""
  local hook_dir=""
  hook_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/ouroboros_httpx_hook"
  llm_env_file="$(mktemp)"
  if ! python3 - <<'PY' >"$llm_env_file"
from bench_eval.ouroboros_llm_sync import shell_export_lines

print("\n".join(shell_export_lines()))
PY
  then
    rm -f "$llm_env_file"
    return 1
  fi

  (
    if cd "$safe_cwd" 2>/dev/null; then
      :
    else
      cd "${TMPDIR:-/tmp}"
    fi
    if [[ -s "$llm_env_file" ]]; then
      set -a
      # shellcheck disable=SC1090
      source "$llm_env_file"
      set +a
    fi
    rm -f "$llm_env_file"
    unset PYTHONPATH
    # Dedicated sitecustomize only — never ROOT, which would shadow pip ouroboros.
    if [[ -f "$hook_dir/sitecustomize.py" ]]; then
      export PYTHONPATH="$hook_dir"
    fi
    export PYTHONSAFEPATH=1
    export HOME="${HOME:-}"
    export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-}"
    export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"
    export PLAYWRIGHT_INSTALL_WITH_DEPS="${PLAYWRIGHT_INSTALL_WITH_DEPS:-0}"
    export SKIP_PLAYWRIGHT_INSTALL_DEPS="${SKIP_PLAYWRIGHT_INSTALL_DEPS:-1}"
    exec "$@"
  )
}

_sync_ouroboros_server_llm_after_start() {
  local url="${1:?}"
  local repo_root="${2:-}"
  if [[ -n "$repo_root" ]]; then
    export PYTHONPATH="${repo_root}/lib/src:${repo_root}${PYTHONPATH:+:$PYTHONPATH}"
  fi
  python3 - <<PY
from bench_eval.ouroboros_client import OuroborosHTTPClient
from bench_eval.ouroboros_llm_sync import sync_ouroboros_server_llm

client = OuroborosHTTPClient("${url}", timeout=30.0, max_retries=3)
settings = sync_ouroboros_server_llm(client)
if settings:
    print(
        "[ouroboros] synced LLM settings:",
        ", ".join(sorted(settings.keys())),
        flush=True,
    )
else:
    print("[ouroboros] warning: no LLM settings to sync", flush=True)
PY
}

_print_ouroboros_install_hint() {
  local root="${1:-.}"
  cat >&2 <<EOF
Ouroboros CLI не найден (нужен только для ouroboros-full-isolated / ouroboros-full-evolving).

Варианты:

  1) Submodule + pip install (рекомендуется):
     git submodule update --init ouroboros
     ./scripts/install_ouroboros.sh

  2) Указать уже установленный бинарник:
     export OUROBOROS_BIN=/path/to/ouroboros
     # или путь к .venv/bin/ouroboros после pip install -e .

  3) envs/_ouroboros.env — override OUROBOROS_BIN / OUROBOROS_REPO_DIR

  4) Packaged release: https://github.com/razzant/ouroboros/releases

Для browser-use / ouroboros-cut Ouroboros не нужен — используйте:
  ./scripts/start_dab_preview.sh
EOF
}
