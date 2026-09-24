#!/usr/bin/env bash
# Copy liderboard/ files changed in the latest commit into a WebPageBench checkout.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_PREFIX="liderboard"
DEST="${WEBPAGEBENCH_DIR:-${1:-}}"

usage() {
  cat <<'EOF'
Usage: sync_liderboard_to_webpagebench.sh [DEST]

Copy only files under liderboard/ that were added, modified, or deleted
in the latest git commit (HEAD) into DEST (WebPageBench Space repo).

Environment:
  WEBPAGEBENCH_DIR   default destination if DEST argument is omitted

Examples:
  ./scripts/sync_liderboard_to_webpagebench.sh ../WebPageBench
  WEBPAGEBENCH_DIR=~/spaces/WebPageBench ./scripts/sync_liderboard_to_webpagebench.sh
EOF
}

if [[ -z "${DEST}" ]]; then
  usage >&2
  exit 1
fi

if ! git -C "$REPO_ROOT" rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "No commits in $REPO_ROOT" >&2
  exit 1
fi

if [[ ! -d "$DEST" ]]; then
  echo "Destination directory not found: $DEST" >&2
  exit 1
fi

mapfile -t CHANGES < <(
  git -C "$REPO_ROOT" diff-tree --no-commit-id --name-status -r HEAD -- "$SRC_PREFIX"
)

if [[ "${#CHANGES[@]}" -eq 0 ]]; then
  echo "No liderboard/ changes in HEAD"
  exit 0
fi

copied=0
deleted=0

rel_path() {
  local path="$1"
  local rel="${path#${SRC_PREFIX}/}"
  if [[ "$rel" == "$path" ]]; then
    return 1
  fi
  printf '%s' "$rel"
}

copy_file() {
  local path="$1"
  local rel
  rel="$(rel_path "$path")" || return 0
  local src_file="$REPO_ROOT/$path"
  local dest_file="$DEST/$rel"
  if [[ ! -f "$src_file" ]]; then
    echo "Skip missing source: $path" >&2
    return 0
  fi
  mkdir -p "$(dirname "$dest_file")"
  cp "$src_file" "$dest_file"
  echo "copied: $rel"
  copied=$((copied + 1))
}

delete_file() {
  local path="$1"
  local rel
  rel="$(rel_path "$path")" || return 0
  local dest_file="$DEST/$rel"
  if [[ -e "$dest_file" ]]; then
    rm -f "$dest_file"
    echo "deleted: $rel"
    deleted=$((deleted + 1))
  fi
}

for entry in "${CHANGES[@]}"; do
  IFS=$'\t' read -r status path arg <<<"$entry"
  case "$status" in
    A|M)
      copy_file "$path"
      ;;
    D)
      delete_file "$path"
      ;;
    R*)
      delete_file "$path"
      copy_file "$arg"
      ;;
    *)
      echo "Skip unsupported status $status for $path" >&2
      ;;
  esac
done

echo "Done: $copied copied, $deleted deleted -> $DEST"
