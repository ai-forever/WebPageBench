"""Tests for UI variant bench configs (tests/bench/configs/)."""

from __future__ import annotations

import pytest
from pathlib import Path

from ui_variant_profiles import (
    build_variant_config,
    list_variant_configs,
    load_variant_overlay,
    profile_domain_variants,
    profile_summary,
    validate_ui_variants,
)


class TestUiVariantConfigs:
    def test_all_profiles_load_and_validate(self):
        paths = list_variant_configs()
        assert len(paths) >= 30, f"Expected at least 30 variant configs, got {len(paths)}"
        for path in paths:
            overlay = load_variant_overlay(path)
            cfg = build_variant_config(overlay)
            errors = validate_ui_variants(cfg, label=path.name)
            assert not errors, f"{path.name}: {errors}"

    def test_hotels_profiles_cover_all_date_variants(self):
        date_variants = set()
        for path in list_variant_configs():
            if not path.name.startswith("hotels_"):
                continue
            overlay = load_variant_overlay(path)
            variants = profile_domain_variants(overlay, "hotels")
            if "date" in variants:
                date_variants.add(variants["date"])
        assert date_variants >= {"split_popup", "inline_calendar", "text_input", "single_popup"}

    def test_hotels_select_and_counter_variants(self):
        cities: set[str] = set()
        counters: set[str] = set()
        for path in list_variant_configs():
            if not path.name.startswith("hotels_"):
                continue
            overlay = load_variant_overlay(path)
            v = profile_domain_variants(overlay, "hotels")
            if "select_city" in v:
                cities.add(v["select_city"])
            if "counter_guests" in v:
                counters.add(v["counter_guests"])
        assert cities >= {"autocomplete", "native_select"}
        assert counters >= {"rooms_popup", "inline_stepper", "compact_select", "pill_buttons"}

    def test_rail_profiles_cover_date_and_station_variants(self):
        dates: set[str] = set()
        stations: set[str] = set()
        for path in list_variant_configs():
            if not path.name.startswith("rail_"):
                continue
            overlay = load_variant_overlay(path)
            v = profile_domain_variants(overlay, "rail")
            if "date" in v:
                dates.add(v["date"])
            if "select_station" in v:
                stations.add(v["select_station"])
        assert dates >= {"popup_grid", "native_input", "text_input"}
        assert stations >= {"typeahead", "native_select"}

    def test_text_search_domains(self):
        shop_styles: set[str] = set()
        books_styles: set[str] = set()
        for path in list_variant_configs():
            overlay = load_variant_overlay(path)
            for domain, bucket in (("shop", shop_styles), ("books", books_styles)):
                v = profile_domain_variants(overlay, domain).get("text_search")
                if v:
                    bucket.add(v)
        assert shop_styles >= {"underlined", "pill"}
        assert books_styles >= {"underlined", "pill", "filled"}

    def test_files_layout_variants(self):
        layouts: set[str] = set()
        for path in list_variant_configs():
            if not path.name.startswith("files_"):
                continue
            overlay = load_variant_overlay(path)
            v = profile_domain_variants(overlay, "files").get("collections")
            if v:
                layouts.add(v)
        assert layouts >= {"cards", "list", "tree", "compact"}

    def test_profile_summary_has_taxonomy_classes(self):
        overlay = load_variant_overlay("tests/bench/configs/hotels_mixed_v1.json")
        summary = profile_summary(overlay)
        assert "DATE" in summary["taxonomy_classes"]
        assert "SELECT_AC" in summary["taxonomy_classes"]
        assert "COUNTER" in summary["taxonomy_classes"]

    @pytest.mark.parametrize("profile_name", ["bench_taxonomy_all_domains", "hotels_single_modal_pills"])
    def test_profile_has_id(self, profile_name: str):
        overlay = load_variant_overlay(f"tests/bench/configs/{profile_name}.json")
        assert overlay.get("profile_id") == profile_name

    def test_theme_dark_profile_resolves_globally(self):
        from bench_eval.ui_variants import resolve_ui_variants

        overlay = load_variant_overlay("tests/bench/configs/theme_dark.json")
        cfg = build_variant_config(overlay)
        errors = validate_ui_variants(cfg, label="theme_dark")
        assert not errors, errors
        resolved = resolve_ui_variants(cfg, domain="shop")
        assert resolved["theme"] == "dark"

    def test_default_theme_is_light(self):
        from bench_eval.ui_variants import resolve_ui_variants
        from ui_variant_profiles import load_base_config

        resolved = resolve_ui_variants(load_base_config(), domain="hotels")
        assert resolved["theme"] == "light"


class TestUiVariantsDemoCatalog:
    def test_sample_demo_profiles_exist(self):
        from ui_variants_demo import DEMO_SAMPLE_PROFILES

        for pid in DEMO_SAMPLE_PROFILES:
            assert (Path("tests/bench/configs") / f"{pid}.json").is_file(), pid

    def test_profile_entry_urls(self):
        from ui_variants_demo import profile_entry_urls

        overlay = load_variant_overlay("tests/bench/configs/hotels_date_text.json")
        rows = profile_entry_urls(overlay, frontend="http://127.0.0.1:5173", track_id="ui_v_hotels_date_text")
        assert len(rows) == 1
        assert rows[0]["domain"] == "hotels"
        assert "DATE" in rows[0]["taxonomy"]
        assert "date=text_input" in rows[0]["variants"]
