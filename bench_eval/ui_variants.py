"""UI variant schema validation for bench configs."""

from __future__ import annotations

from typing import Any

UI_VARIANT_SCHEMA: dict[str, tuple[str, ...]] = {
    "date": ("split_popup", "inline_calendar", "text_input", "single_popup", "popup_grid", "native_input"),
    "select_city": ("autocomplete", "native_select"),
    "select_station": ("typeahead", "native_select"),
    "counter_guests": ("rooms_popup", "inline_stepper", "compact_select", "pill_buttons"),
    "text_search": ("standard", "outlined", "filled", "underlined", "pill", "large"),
    "collections": ("cards", "list", "tree", "compact"),
    "years": ("select", "buttons", "radio"),
    "buttons": ("solid", "outline", "icon", "split"),
    "theme": ("light", "dark"),
}

UI_VARIANT_DEFAULTS: dict[str, str] = {
    "date": "split_popup",
    "select_city": "autocomplete",
    "select_station": "typeahead",
    "counter_guests": "rooms_popup",
    "text_search": "standard",
    "collections": "cards",
    "years": "select",
    "buttons": "outline",
    "theme": "light",
}

DOMAIN_VARIANT_DEFAULTS: dict[str, dict[str, str]] = {
    "hotels": {
        "date": "split_popup",
        "select_city": "autocomplete",
        "counter_guests": "rooms_popup",
    },
    "rail": {
        "date": "popup_grid",
        "select_station": "typeahead",
    },
    "files": {"collections": "cards", "years": "select", "buttons": "outline"},
    "shop": {"text_search": "standard"},
    "books": {"text_search": "standard"},
    "grocery": {"text_search": "standard"},
}

DOMAIN_WIDGETS: dict[str, tuple[str, ...]] = {
    "hotels": ("date", "select_city", "counter_guests"),
    "rail": ("date", "select_station"),
    "files": ("collections", "years", "buttons"),
    "shop": ("text_search",),
    "books": ("text_search",),
}

WIDGET_TAXONOMY_CLASS: dict[str, str] = {
    "date": "DATE",
    "select_city": "SELECT_AC",
    "select_station": "SELECT_LIST",
    "counter_guests": "COUNTER",
    "text_search": "TXT",
    "collections": "CARD",
    "years": "SELECT_LIST",
    "buttons": "BTN",
}


def validate_ui_variants(cfg: dict[str, Any], *, label: str = "") -> list[str]:
    errors: list[str] = []
    prefix = f"{label}: " if label else ""

    def check_block(block: dict[str, Any], ctx: str) -> None:
        for widget, variant in block.items():
            allowed = UI_VARIANT_SCHEMA.get(widget)
            if not allowed:
                errors.append(f"{prefix}{ctx}: unknown widget type {widget!r}")
            elif variant not in allowed:
                errors.append(f"{prefix}{ctx}: invalid {widget} variant {variant!r}, expected one of {allowed}")

    top = cfg.get("ui_variants")
    if isinstance(top, dict):
        check_block(top, "ui_variants")

    td_variants = (cfg.get("test_data") or {}).get("ui_variants")
    if isinstance(td_variants, dict):
        check_block(td_variants, "test_data.ui_variants")

    for domain, domain_cfg in (cfg.get("domain_configs") or {}).items():
        variants = domain_cfg.get("ui_variants")
        if not isinstance(variants, dict):
            continue
        for widget in variants:
            if widget == "theme":
                continue
            if domain in DOMAIN_WIDGETS and widget not in DOMAIN_WIDGETS[domain]:
                errors.append(
                    f"{prefix}domain_configs.{domain}.ui_variants: widget {widget!r} "
                    f"not typical for domain (expected {DOMAIN_WIDGETS[domain]})"
                )
        check_block(variants, f"domain_configs.{domain}.ui_variants")

    return errors


def profile_taxonomy_classes(profile: dict[str, Any]) -> list[str]:
    """Return sorted UI taxonomy class IDs exercised by a variant profile overlay."""
    classes: set[str] = set()
    for domain_cfg in (profile.get("domain_configs") or {}).values():
        for widget in (domain_cfg.get("ui_variants") or {}):
            if widget in WIDGET_TAXONOMY_CLASS:
                classes.add(WIDGET_TAXONOMY_CLASS[widget])
    return sorted(classes)


def resolve_ui_variants(
    config: dict[str, Any],
    *,
    domain: str | None = None,
) -> dict[str, str]:
    """Resolve effective widget variants (docs/UI_TAXONOMY.md §11)."""
    test_data = config.get("test_data") or {}
    active_domain = (
        domain
        or test_data.get("active_bench_domain")
        or test_data.get("bench_first_domain")
    )
    widgets = DOMAIN_WIDGETS.get(active_domain or "", ())
    resolved: dict[str, str] = {}

    domain_variants = (
        (config.get("domain_configs") or {}).get(active_domain or "", {}).get("ui_variants")
        or {}
    )
    test_variants = test_data.get("ui_variants") or {}
    global_variants = config.get("ui_variants") or {}

    for widget in widgets:
        if widget in domain_variants:
            resolved[widget] = domain_variants[widget]
        elif widget in test_variants:
            resolved[widget] = test_variants[widget]
        elif widget in global_variants:
            resolved[widget] = global_variants[widget]
        else:
            domain_defaults = DOMAIN_VARIANT_DEFAULTS.get(active_domain or "", {})
            resolved[widget] = domain_defaults.get(
                widget, UI_VARIANT_DEFAULTS.get(widget, "standard")
            )
    theme = test_variants.get("theme") or global_variants.get("theme") or UI_VARIANT_DEFAULTS["theme"]
    resolved["theme"] = theme
    return resolved


def pattern_keys(variants: dict[str, str]) -> list[str]:
    return [f"{widget}:{variant}" for widget, variant in sorted(variants.items())]
