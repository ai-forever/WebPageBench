#!/usr/bin/env python3
"""Install strict pins from editable browser-use metadata (stdout = constraints file)."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys


def _distribution(name: str):
    try:
        from importlib.metadata import distribution
    except ImportError:
        from importlib_metadata import distribution  # type: ignore
    return distribution(name)


def normalize_pip_constraint(spec: str) -> str | None:
    """Return name==version suitable for pip -c; None if not a strict pin."""
    raw = str(spec).split(";", 1)[0].strip()
    if "==" not in raw:
        return None
    try:
        from packaging.requirements import Requirement

        req = Requirement(raw)
        if len(req.specifier) != 1:
            return None
        pin = next(iter(req.specifier))
        if pin.operator != "==":
            return None
        return f"{req.name}=={pin.version}"
    except Exception:
        # Fallback: strip extras manually (pip constraints disallow them).
        name_part, _, version_part = raw.partition("==")
        name = re.sub(r"\[.*\]", "", name_part).strip()
        version = version_part.strip()
        if not name or not version:
            return None
        return f"{name}=={version}"


def browser_use_constraint_lines() -> list[str]:
    try:
        dist = _distribution("browser-use")
    except Exception:
        return []
    lines: list[str] = []
    seen: set[str] = set()
    for req in dist.requires or ():
        line = normalize_pip_constraint(str(req))
        if line and line not in seen:
            seen.add(line)
            lines.append(line)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install",
        action="store_true",
        help="pip install browser-use requires (strict == pins only)",
    )
    parser.add_argument(
        "--constraints",
        action="store_true",
        help="print constraint lines to stdout",
    )
    args = parser.parse_args()

    lines = browser_use_constraint_lines()
    if args.constraints:
        for line in lines:
            print(line)

    if args.install:
        try:
            dist = _distribution("browser-use")
        except Exception as exc:
            print(f"browser-use not installed: {exc}", file=sys.stderr)
            return 1
        reqs = [str(req) for req in (dist.requires or ())]
        if not reqs:
            return 0
        print("Re-installing browser-use requires:", ", ".join(reqs), file=sys.stderr)
        subprocess.check_call([sys.executable, "-m", "pip", "install", *reqs])

    if not args.install and not args.constraints:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
