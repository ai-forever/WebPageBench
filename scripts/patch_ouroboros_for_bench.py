#!/usr/bin/env python3
"""Patch ouroboros submodule defaults so WebPageBench never ships expensive model IDs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

MARKER = "# patched-by-webpagebench-eval"
CHEAP_MODEL = "google/gemini-2.5-flash"
EXPENSIVE_GEMINI = "google/gemini-3.5-flash"

CONFIG_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (
        f'"OUROBOROS_MODEL": "{EXPENSIVE_GEMINI}"',
        f'"OUROBOROS_MODEL": "{CHEAP_MODEL}",  {MARKER}',
    ),
    (
        '"OUROBOROS_MODEL_FALLBACKS": "anthropic/claude-sonnet-4.6"',
        f'"OUROBOROS_MODEL_FALLBACKS": "{CHEAP_MODEL}",  {MARKER}',
    ),
    (
        '"OUROBOROS_MODEL_DEEP_SELF_REVIEW": "openai/gpt-5.5-pro"',
        f'"OUROBOROS_MODEL_DEEP_SELF_REVIEW": "{CHEAP_MODEL}",  {MARKER}',
    ),
    (
        '"OUROBOROS_WEBSEARCH_MODEL": "gpt-5.2"',
        f'"OUROBOROS_WEBSEARCH_MODEL": "{CHEAP_MODEL}",  {MARKER}',
    ),
    (
        f'"OUROBOROS_REVIEW_MODELS": "openai/gpt-5.5,{EXPENSIVE_GEMINI},anthropic/claude-opus-4.8"',
        f'"OUROBOROS_REVIEW_MODELS": "{CHEAP_MODEL}",  {MARKER}',
    ),
    (
        '"OUROBOROS_SCOPE_REVIEW_MODELS": "openai/gpt-5.5"',
        f'"OUROBOROS_SCOPE_REVIEW_MODELS": "{CHEAP_MODEL}",  {MARKER}',
    ),
    (
        '"OUROBOROS_SCOPE_REVIEW_MODEL": "openai/gpt-5.5"',
        f'"OUROBOROS_SCOPE_REVIEW_MODEL": "{CHEAP_MODEL}",  {MARKER}',
    ),
)

# Module-level assignments: never use ",  # comment" — trailing comma creates a tuple.
_PATCHED_ASSIGNMENT = f'  {MARKER}'

_EXTRA_FILE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (
        f'CONSOLIDATION_MODEL = "{EXPENSIVE_GEMINI}"',
        f'CONSOLIDATION_MODEL = "{CHEAP_MODEL}"{_PATCHED_ASSIGNMENT}',
    ),
    (
        f'DEFAULT_LIGHT_MODEL = "{EXPENSIVE_GEMINI}"',
        f'DEFAULT_LIGHT_MODEL = "{CHEAP_MODEL}"{_PATCHED_ASSIGNMENT}',
    ),
)

# Repair a previous buggy patch that used ",  # marker" on assignment lines.
_BROKEN_ASSIGNMENT_REPAIRS: tuple[tuple[str, str], ...] = (
    (
        f'CONSOLIDATION_MODEL = "{CHEAP_MODEL}",  {MARKER}',
        f'CONSOLIDATION_MODEL = "{CHEAP_MODEL}"{_PATCHED_ASSIGNMENT}',
    ),
    (
        f'DEFAULT_LIGHT_MODEL = "{CHEAP_MODEL}",  {MARKER}',
        f'DEFAULT_LIGHT_MODEL = "{CHEAP_MODEL}"{_PATCHED_ASSIGNMENT}',
    ),
)


def _patch_file(path: Path, replacements: tuple[tuple[str, str], ...]) -> bool:
    if not path.is_file():
        print(f"skip missing file: {path}", file=sys.stderr)
        return False
    original = path.read_text(encoding="utf-8")
    updated = original
    changed = False
    for old, new in replacements:
        if old in updated:
            updated = updated.replace(old, new)
            changed = True
        elif new.split(MARKER, 1)[0].rstrip() in updated and MARKER in updated:
            continue
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return changed


def _patch_remaining_gemini_35(pkg_dir: Path) -> list[str]:
    """Catch any other hardcoded gemini-3.5-flash constants in the package."""
    changed: list[str] = []
    if not pkg_dir.is_dir():
        return changed
    for path in sorted(pkg_dir.rglob("*.py")):
        original = path.read_text(encoding="utf-8")
        if EXPENSIVE_GEMINI not in original:
            continue
        updated = original.replace(EXPENSIVE_GEMINI, CHEAP_MODEL)
        if updated == original:
            continue
        path.write_text(updated, encoding="utf-8")
        changed.append(str(path))
    return changed


def patch_ouroboros_repo(repo_dir: Path) -> list[str]:
    changed: list[str] = []
    pkg_dir = repo_dir / "ouroboros"
    config_path = pkg_dir / "config.py"
    if _patch_file(config_path, CONFIG_REPLACEMENTS):
        changed.append(str(config_path))

    for rel_name in ("llm.py", "consolidator.py"):
        file_path = pkg_dir / rel_name
        if _patch_file(file_path, _BROKEN_ASSIGNMENT_REPAIRS):
            if str(file_path) not in changed:
                changed.append(str(file_path))
        if _patch_file(file_path, _EXTRA_FILE_REPLACEMENTS):
            if str(file_path) not in changed:
                changed.append(str(file_path))

    llm_path = pkg_dir / "llm.py"
    if llm_path.is_file():
        original = llm_path.read_text(encoding="utf-8")
        updated = original.replace(f'"{EXPENSIVE_GEMINI}"', f'"{CHEAP_MODEL}"')
        if updated != original:
            llm_path.write_text(updated, encoding="utf-8")
            if str(llm_path) not in changed:
                changed.append(str(llm_path))

    for path in _patch_remaining_gemini_35(pkg_dir):
        if path not in changed:
            changed.append(path)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "ouroboros",
        help="Path to ouroboros submodule checkout",
    )
    args = parser.parse_args()
    repo_dir = args.repo_dir.resolve()
    if not (repo_dir / "ouroboros" / "config.py").is_file():
        print(f"ouroboros checkout not found: {repo_dir}", file=sys.stderr)
        return 1
    changed = patch_ouroboros_repo(repo_dir)
    if changed:
        print("Patched ouroboros for WebPageBench:")
        for path in changed:
            print(f"  - {path}")
    else:
        print("ouroboros bench patch already applied (no changes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
