"""Register bench tracks for UI variant profiles and build a demo catalog."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from bench_eval.bench_verify import BENCH_TESTS_DIR
from bench_eval.ui_variants import WIDGET_TAXONOMY_CLASS
from ui_variant_profiles import (
    build_variant_config,
    list_variant_configs,
    load_variant_overlay,
    profile_summary,
)

BENCH_DIR = BENCH_TESTS_DIR

DEMO_SAMPLE_PROFILES: tuple[str, ...] = (
    "hotels_default",
    "hotels_date_text",
    "hotels_date_single",
    "hotels_city_modal",
    "hotels_guests_pills",
    "rail_date_popup",
    "rail_date_native",
    "rail_station_buttons",
    "files_layout_cards",
    "shop_search_underlined",
    "books_search_filled",
    "bench_taxonomy_all_domains",
)

DOMAIN_ROUTES: dict[str, tuple[str, str, str]] = {
    "hotels": ("state_hotels_main", "bench_hotel_main", "Отели"),
    "rail": ("state_rail_main", "bench_rail_main", "Поезда"),
    "files": ("state_files_main", "bench_files_cabinet", "Файлы"),
    "shop": ("state_shop_main", "bench_catalog_main", "Маркет"),
    "books": ("state_books_main", "bench_books_main", "Книги"),
}

TRACK_PREFIX = os.environ.get("UI_VARIANTS_TRACK_PREFIX", "ui_v_")


def track_id_for_profile(profile_id: str) -> str:
    return f"{TRACK_PREFIX}{profile_id}"


def page_url(frontend: str, track_id: str, state_id: str, view_type: str) -> str:
    base = frontend.rstrip("/")
    return f"{base}/{track_id}/{state_id}/{view_type}"


def profile_entry_urls(profile: dict[str, Any], *, frontend: str, track_id: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for domain, cfg in (profile.get("domain_configs") or {}).items():
        variants = cfg.get("ui_variants") or {}
        if not variants:
            continue
        route = DOMAIN_ROUTES.get(domain)
        if not route:
            continue
        state_id, view_type, label = route
        widget_parts = []
        taxonomy: set[str] = set()
        for widget, variant in variants.items():
            taxonomy.add(WIDGET_TAXONOMY_CLASS.get(widget, widget.upper()))
            widget_parts.append(f"{widget}={variant}")
        rows.append(
            {
                "domain": domain,
                "label": label,
                "url": page_url(frontend, track_id, state_id, view_type),
                "taxonomy": ", ".join(sorted(taxonomy)),
                "variants": "; ".join(widget_parts),
            }
        )
    return rows


def create_track(profile_id: str, *, api_address: str) -> str:
    from lib.src.agent_bench import client

    overlay = load_variant_overlay(BENCH_DIR / "configs" / f"{profile_id}.json")
    cfg = build_variant_config(overlay)
    cfg.setdefault("test_data", {})["ui_variant_profile"] = profile_id
    cfg["test_data"]["demo_track"] = True

    track_id = track_id_for_profile(profile_id)
    build_path = BENCH_DIR / "build" / f"{track_id}.json"
    build_path.parent.mkdir(parents=True, exist_ok=True)
    build_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    client.create_track(
        name=track_id,
        id=track_id,
        filepath=str(build_path),
        address=api_address,
        delete_existing=True,
    )
    return track_id


def register_profiles(
    profile_ids: list[str],
    *,
    api_address: str,
    frontend_url: str,
) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    for profile_id in profile_ids:
        overlay = load_variant_overlay(BENCH_DIR / "configs" / f"{profile_id}.json")
        summary = profile_summary(overlay)
        track_id = create_track(profile_id, api_address=api_address)
        entries = profile_entry_urls(overlay, frontend=frontend_url, track_id=track_id)
        catalog.append(
            {
                "profile_id": profile_id,
                "track_id": track_id,
                "description": summary.get("description", ""),
                "taxonomy_classes": summary.get("taxonomy_classes", []),
                "entries": entries,
                "hub_url": page_url(frontend_url, track_id, "state_hub", "bench_hub"),
            }
        )
    return catalog


def write_catalog(catalog: list[dict[str, Any]], out_path: Path) -> None:
    lines = ["# UI Variants Demo Catalog", ""]
    for item in catalog:
        lines.append(f"## {item['profile_id']}")
        lines.append("")
        lines.append(item["description"])
        lines.append("")
        lines.append(f"- Track: `{item['track_id']}`")
        lines.append(f"- Hub: {item['hub_url']}")
        lines.append(f"- Taxonomy: {', '.join(item['taxonomy_classes'])}")
        lines.append("")
        lines.append("| Домен | Классы UI | Варианты | URL |")
        lines.append("|-------|-----------|----------|-----|")
        for e in item["entries"]:
            lines.append(
                f"| {e['label']} ({e['domain']}) | {e['taxonomy']} | {e['variants']} | {e['url']} |"
            )
        lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def print_catalog(catalog: list[dict[str, Any]]) -> None:
    print("")
    print("=" * 72)
    print("UI Variants Demo — зарегистрированные треки")
    print("=" * 72)
    for item in catalog:
        print("")
        print(f"[{item['profile_id']}] {item['description']}")
        print(f"  hub: {item['hub_url']}")
        for e in item["entries"]:
            print(f"  {e['label']:8}  {e['taxonomy']:24}  {e['url']}")
    print("")
    print(f"Всего профилей: {len(catalog)}")
    print("=" * 72)


def resolve_profile_ids(args: argparse.Namespace) -> list[str]:
    if args.profile:
        return [args.profile]
    if args.all:
        return [p.stem for p in list_variant_configs()]
    return list(DEMO_SAMPLE_PROFILES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create demo tracks for UI variant configs.")
    parser.add_argument("--profile", help="Single profile_id from tests/bench/configs/")
    parser.add_argument("--sample", action="store_true", help=f"Demo subset ({len(DEMO_SAMPLE_PROFILES)} profiles)")
    parser.add_argument("--all", action="store_true", help="Register all configs/*.json profiles")
    parser.add_argument(
        "--api-address",
        default=os.environ.get("BENCH_API_ADDRESS", "localhost:9000"),
    )
    parser.add_argument(
        "--frontend-url",
        default=os.environ.get("BENCH_FRONTEND_URL", "http://127.0.0.1:5173"),
    )
    parser.add_argument(
        "--catalog-out",
        type=Path,
        default=BENCH_DIR / "build" / "ui_variants_demo_catalog.md",
    )
    args = parser.parse_args(argv)

    profile_ids = resolve_profile_ids(args)
    missing = [p for p in profile_ids if not (BENCH_DIR / "configs" / f"{p}.json").is_file()]
    if missing:
        print(f"Unknown profiles: {', '.join(missing)}", file=sys.stderr)
        return 1

    catalog = register_profiles(
        profile_ids,
        api_address=args.api_address,
        frontend_url=args.frontend_url,
    )
    write_catalog(catalog, args.catalog_out)
    print_catalog(catalog)
    print(f"Catalog saved: {args.catalog_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
