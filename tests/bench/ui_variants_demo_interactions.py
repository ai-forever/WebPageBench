"""Playwright interactions for UI variants demo recording."""

from __future__ import annotations

from datetime import date

from bench_eval.task_dates import booking_iso_pair, format_dotted, iso_from_today


TYPE_DELAY_MS = 110
STEP_PAUSE_MS = 550
ACTION_PAUSE_MS = 750


def pause(page, ms: int = STEP_PAUSE_MS) -> None:
    page.wait_for_timeout(ms)


def focus_visible(locator) -> None:
    locator.scroll_into_view_if_needed()
    locator.hover()
    pause(locator.page, 180)


def click_visible(locator) -> None:
    focus_visible(locator)
    locator.click()
    pause(locator.page, 280)


def select_visible(locator, **kwargs) -> None:
    focus_visible(locator)
    locator.select_option(**kwargs)
    pause(locator.page, 350)


def type_slowly(locator, text: str, *, delay_ms: int = TYPE_DELAY_MS) -> None:
    focus_visible(locator)
    locator.click()
    pause(locator.page, 250)
    locator.fill("")
    locator.press_sequentially(text, delay=delay_ms)
    pause(locator.page, 350)


def fill_visible(locator, text: str) -> None:
    focus_visible(locator)
    locator.fill(text)
    pause(locator.page, 350)


def demo_hotels(page, variants: dict[str, str]) -> None:
    page.locator(".searchButton, .controlDestination").first.wait_for(state="visible", timeout=25_000)
    pause(page, 800)

    city_variant = variants.get("select_city", "autocomplete")
    if city_variant == "native_select":
        select_visible(page.locator(".native-select").first, index=2)
    else:
        type_slowly(page.locator(".controlDestination input, .textInput").first, "Лион")
        pause(page, 400)
        click_visible(page.locator(".opt").first)

    pause(page, ACTION_PAUSE_MS)

    date_variant = variants.get("date", "split_popup")
    check_in, check_out = booking_iso_pair(14, 7)
    if date_variant == "text_input":
        inputs = page.locator(".date-text-input")
        type_slowly(inputs.nth(0), format_dotted(date.fromisoformat(check_in)))
        pause(page)
        type_slowly(inputs.nth(1), format_dotted(date.fromisoformat(check_out)))
    elif date_variant == "inline_calendar":
        days = page.locator(".dayBtn:not([disabled])")
        click_visible(days.nth(8))
        click_visible(days.nth(12))
    elif date_variant == "single_popup":
        click_visible(page.locator(".singleCell, .singlePopup button").first)
        pause(page, 500)
        days = page.locator(".dayBtn:not([disabled])")
        click_visible(days.nth(10))
        click_visible(days.nth(14))
        page.keyboard.press("Escape")
    else:
        click_visible(page.locator(".controlDates .cell.left, .controlDates button, .drf button").first)
        pause(page, 500)
        days = page.locator(".dayBtn:not([disabled])")
        click_visible(days.nth(10))
        click_visible(days.nth(14))
        page.keyboard.press("Escape")

    pause(page, ACTION_PAUSE_MS)

    guest_variant = variants.get("counter_guests", "rooms_popup")
    if guest_variant == "pill_buttons":
        click_visible(page.locator(".pill").nth(2))
    elif guest_variant == "inline_stepper":
        click_visible(page.locator(".step-btn").last)
    elif guest_variant == "compact_select":
        select_visible(page.locator(".compact-select").first, value="3")
    else:
        click_visible(page.locator(".controlGuests, .guestsField").first)
        plus = page.locator(".plusBtn, .counter").filter(has_text="+")
        if plus.count():
            click_visible(plus.first)
        click_visible(page.locator(".doneBtn, button:has-text('Готово')").first)

    pause(page, 900)


def demo_rail(page, variants: dict[str, str]) -> None:
    page.locator(".rail-search-widget").wait_for(state="visible", timeout=25_000)
    pause(page, 800)

    station_variant = variants.get("select_station", "typeahead")
    if station_variant == "native_select":
        selects = page.locator(".native-select")
        select_visible(selects.nth(0), index=1)
        select_visible(selects.nth(1), index=2)
    else:
        type_slowly(page.locator(".rail-search-widget .station-field input").first, "Моск")
        pause(page, 400)
        click_visible(page.locator(".dropdown-item").filter(has_text="Москва").first)
        type_slowly(page.locator(".rail-search-widget .station-field input").nth(1), "Санкт")
        pause(page, 400)
        click_visible(page.locator(".dropdown-item").filter(has_text="Санкт-Петербург").first)

    pause(page, ACTION_PAUSE_MS)

    date_variant = variants.get("date", "popup_grid")
    rail_out = iso_from_today(14)
    rail_back = iso_from_today(21)
    if date_variant == "native_input":
        fill_visible(page.locator(".native-date-input, input[type='date']").first, rail_out)
        fill_visible(page.locator(".native-date-input, input[type='date']").nth(1), rail_back)
    elif date_variant == "text_input":
        text_inputs = page.locator(".text-date-input")
        type_slowly(text_inputs.nth(0), format_dotted(date.fromisoformat(rail_out)))
        pause(page)
        type_slowly(text_inputs.nth(1), format_dotted(date.fromisoformat(rail_back)))
    else:
        click_visible(page.locator(".date-field .field-inner").first)
        pause(page, 500)
        click_visible(page.locator(".datepicker-container .day-number, .day-number").first)
        click_visible(page.locator(".date-field.return-date-field .field-inner, .date-field .field-inner").nth(1))
        pause(page, 400)
        click_visible(page.locator(".datepicker-container .day-number, .day-number").nth(4))
        page.keyboard.press("Escape")

    pause(page, 900)


def demo_files(page, variants: dict[str, str]) -> None:
    page.locator(".bench-files").first.wait_for(state="visible", timeout=25_000)
    pause(page, 800)
    click_visible(page.get_by_role("button", name="Отчёты лаборатории").first)
    pause(page, 700)
    select = page.locator(".bench-files select")
    if select.count():
        select.first.select_option("2024")
    else:
        click_visible(page.locator(".bench-files__year").filter(has_text="2024").first)
    pause(page, 900)


def demo_shop(page, variants: dict[str, str]) -> None:
    page.locator(".bench-market-header .search-input input, .search-input input").first.wait_for(
        state="visible", timeout=25_000
    )
    pause(page, 800)
    type_slowly(page.locator(".bench-market-header .search-input input, .search-input input").first, "iphone")
    pause(page, 500)
    page.keyboard.press("Enter")
    pause(page, 900)


def demo_books(page, variants: dict[str, str]) -> None:
    page.locator(".searchbar .search-input input").first.wait_for(state="visible", timeout=25_000)
    pause(page, 800)
    type_slowly(page.locator(".searchbar .search-input input").first, "эшвуд")
    pause(page, 500)
    click_visible(page.locator(".searchbar .search-btn").first)
    pause(page, 900)


DOMAIN_HANDLERS = {
    "hotels": demo_hotels,
    "rail": demo_rail,
    "files": demo_files,
    "shop": demo_shop,
    "books": demo_books,
}


def next_step_label(domain: str, variants: dict[str, str]) -> str:
    labels: list[str] = []
    if domain == "hotels":
        city = {"autocomplete": "autocomplete города", "native_select": "select города"}.get(
            variants.get("select_city", ""), "город"
        )
        date = {
            "split_popup": "popup-календарь",
            "inline_calendar": "inline-календарь",
            "text_input": "ввод дат строкой",
            "single_popup": "одно поле дат",
        }.get(variants.get("date", ""), "даты")
        guests = {
            "rooms_popup": "popup гостей",
            "inline_stepper": "stepper гостей",
            "compact_select": "select гостей",
            "pill_buttons": "pill-кнопки гостей",
        }.get(variants.get("counter_guests", ""), "гости")
        labels.extend([city, date, guests])
    elif domain == "rail":
        st = {"typeahead": "typeahead станций", "native_select": "select станций"}.get(
            variants.get("select_station", ""), "станции"
        )
        dt = {"popup_grid": "popup-календарь", "native_input": "native date", "text_input": "даты строкой"}.get(
            variants.get("date", ""), "даты"
        )
        labels.extend([st, dt])
    elif domain == "files":
        labels.append(f"коллекции ({variants.get('collections', 'cards')})")
    elif domain in ("shop", "books"):
        labels.append(f"ввод в поиск ({variants.get('text_search', 'standard')})")
    return " → ".join(labels) if labels else "взаимодействие с формой"


def interact_domain(page, domain: str, variants: dict[str, str]) -> None:
    handler = DOMAIN_HANDLERS.get(domain)
    if handler:
        handler(page, variants)
