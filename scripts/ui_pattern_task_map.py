"""Clone map: base bench tasks × UI widget variants and dark theme.

Used by scripts/build_bench_tasks.py. Do not hand-write clone JSON.
"""

from __future__ import annotations

from dataclasses import dataclass

BASE_TASK_COUNT = 65

HOTEL_SEARCH_STEMS = (
    "hotel_search_scenario",
    "hotel_search_scenario_dubai",
    "hotel_search_scenario_family",
    "hotel_search_scenario_seoul",
    "hotel_search_scenario_two_rooms",
)

RAIL_DATE_STEMS = (
    "rail_book_to_cart",
    "rail_book_to_cart_2_passengers",
    "rail_book_to_cart_business",
    "rail_book_to_cart_platskart",
    "rail_atomic_select_date",
)

RAIL_STATION_STEMS = (
    "rail_book_to_cart",
    "rail_book_to_cart_2_passengers",
    "rail_book_to_cart_business",
    "rail_book_to_cart_platskart",
    "rail_atomic_select_city_from",
)

FILES_MIXED_STEMS = (
    "files_download_pdf",
    "files_download_csv",
    "files_archive_pdf",
    "files_archive_month_pdf",
    "files_archive_quarter",
)

TEXT_SEARCH_STEMS = (
    "ecommerce_basket_named_product_02",
    "ecommerce_basket_named_product_03",
    "ecommerce_basket_named_smartphone",
    "digital_books_named_product_basket",
    "digital_books_named_product_favorites",
)

THEME_DARK_STEMS = (
    "ecommerce_basket_named_product_02",
    "ecommerce_favorites",
    "digital_books_named_product_basket",
    "digital_books_named_product_favorites",
    "grocery_basket_named_product",
    "grocery_basket_category_named_product",
    "rail_book_to_cart",
    "rail_book_and_pay",
    "hotel_search_scenario",
    "hotel_search_scenario_dubai",
    "files_archive_quarter",
    "files_download_pdf",
)

TEXT_SEARCH_VARIANTS = ("outlined", "filled", "underlined", "pill")

FILES_MIXED_VARIANTS = {
    "collections": "list",
    "years": "buttons",
    "buttons": "icon",
}


@dataclass(frozen=True)
class CloneSpec:
    source_stem: str
    filename: str
    domain: str | None
    variants: dict[str, str]
    profile_id: str

    @property
    def stem(self) -> str:
        return self.filename.removesuffix(".json")


def _isolated(
    stems: tuple[str, ...],
    domain: str,
    widget: str,
    variant: str,
    profile_id: str,
) -> list[CloneSpec]:
    return [
        CloneSpec(
            source_stem=stem,
            filename=f"{stem}__{widget}_{variant}.json",
            domain=domain,
            variants={widget: variant},
            profile_id=profile_id,
        )
        for stem in stems
    ]


def list_clone_specs() -> list[CloneSpec]:
    specs: list[CloneSpec] = []
    specs.extend(_isolated(HOTEL_SEARCH_STEMS, "hotels", "date", "inline_calendar", "hotels_date_inline"))
    specs.extend(_isolated(HOTEL_SEARCH_STEMS, "hotels", "date", "text_input", "hotels_date_text"))
    specs.extend(_isolated(HOTEL_SEARCH_STEMS, "hotels", "date", "single_popup", "hotels_date_single"))
    specs.extend(_isolated(HOTEL_SEARCH_STEMS, "hotels", "select_city", "native_select", "hotels_city_native"))
    specs.extend(_isolated(HOTEL_SEARCH_STEMS, "hotels", "counter_guests", "inline_stepper", "hotels_guests_inline"))
    specs.extend(_isolated(HOTEL_SEARCH_STEMS, "hotels", "counter_guests", "compact_select", "hotels_guests_compact"))
    specs.extend(_isolated(HOTEL_SEARCH_STEMS, "hotels", "counter_guests", "pill_buttons", "hotels_guests_pills"))
    specs.extend(_isolated(RAIL_DATE_STEMS, "rail", "date", "native_input", "rail_date_native"))
    specs.extend(_isolated(RAIL_DATE_STEMS, "rail", "date", "text_input", "rail_date_text"))
    specs.extend(_isolated(RAIL_STATION_STEMS, "rail", "select_station", "native_select", "rail_station_native"))
    for stem in FILES_MIXED_STEMS:
        specs.append(
            CloneSpec(
                source_stem=stem,
                filename=f"{stem}__files_list_buttons_icon.json",
                domain="files",
                variants=dict(FILES_MIXED_VARIANTS),
                profile_id="files_layout_list",
            )
        )
    for variant in TEXT_SEARCH_VARIANTS:
        for stem in TEXT_SEARCH_STEMS:
            domain = "books" if stem.startswith("digital_books_") else "shop"
            profile = f"{domain}_search_{variant}"
            specs.append(
                CloneSpec(
                    source_stem=stem,
                    filename=f"{stem}__text_search_{variant}.json",
                    domain=domain,
                    variants={"text_search": variant},
                    profile_id=profile,
                )
            )
    for stem in THEME_DARK_STEMS:
        specs.append(
            CloneSpec(
                source_stem=stem,
                filename=f"{stem}__theme_dark.json",
                domain=None,
                variants={"theme": "dark"},
                profile_id="theme_dark",
            )
        )
    return specs


def clone_count() -> int:
    return len(list_clone_specs())


def canonical_task_count() -> int:
    return BASE_TASK_COUNT + clone_count()


def pattern_to_stems() -> dict[str, list[str]]:
    """Map widget:variant (or theme:dark) to clone stems that set that key."""
    coverage: dict[str, list[str]] = {}
    for spec in list_clone_specs():
        for widget, variant in spec.variants.items():
            key = f"{widget}:{variant}"
            coverage.setdefault(key, []).append(spec.stem)
    return coverage


def apply_clone(base_task: dict, spec: CloneSpec) -> dict:
    """Copy a base task JSON and inject ui_variants. Prompts/conditions stay identical."""
    import copy

    cloned = copy.deepcopy(base_task)
    td = cloned.setdefault("test_data", {})
    td["ui_variants"] = {**(td.get("ui_variants") or {}), **spec.variants}
    td["ui_variant_profile"] = spec.profile_id
    widget_variants = {key: value for key, value in spec.variants.items() if key != "theme"}
    if spec.domain and widget_variants:
        domain_cfg = cloned.setdefault("domain_configs", {}).setdefault(spec.domain, {})
        domain_cfg["ui_variants"] = {**(domain_cfg.get("ui_variants") or {}), **widget_variants}
    return cloned
