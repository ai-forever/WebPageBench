"""UI taxonomy class registry (docs/UI_TAXONOMY.md §2)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UITaxonomyClass:
    """Single UI interaction class from UI_TAXONOMY.md."""

    class_id: str
    name: str
    primary_events: tuple[str, ...]
    bench_domains: tuple[str, ...]


UI_TAXONOMY_CLASSES: tuple[UITaxonomyClass, ...] = (
    UITaxonomyClass("NAV", "Навигация", ("state_changed",), ("hub", "shop", "books", "grocery", "rail", "hotels", "files")),
    UITaxonomyClass("BTN", "Кнопки / ссылки", ("button_clicked", "state_changed"), ("books",)),
    UITaxonomyClass("TXT", "Ввод текста", (), ("shop", "books", "rail")),
    UITaxonomyClass("SEARCH", "Поиск", ("submit_search", "state_changed"), ("books", "rail", "shop")),
    UITaxonomyClass("SELECT_AC", "Autocomplete", ("bench_hotel_select_city",), ("hotels",)),
    UITaxonomyClass("SELECT_LIST", "Выбор из списка", ("select_city", "select_passenger", "bench_files_select_year"), ("rail", "hotels", "files")),
    UITaxonomyClass("DATE", "Выбор даты", ("select_date", "bench_hotel_select_start_date", "bench_hotel_select_end_date"), ("rail", "hotels")),
    UITaxonomyClass("COUNTER", "Счётчики", ("bench_hotel_select_guests", "basket_add", "basket_remove"), ("hotels", "rail", "grocery", "shop")),
    UITaxonomyClass("CHECK", "Чекбоксы", ("apply_filter",), ("rail", "books")),
    UITaxonomyClass("RADIO", "Радиокнопки / табы", ("select_tariff", "select_pay_method"), ("rail", "books")),
    UITaxonomyClass("CARD", "Карточки", ("select_train", "bench_hotel_select_hotel", "bench_hotel_select_room", "bench_files_select_collection", "state_changed"), ("shop", "books", "rail", "hotels", "files")),
    UITaxonomyClass("SEAT", "Выбор места", ("select_seat",), ("rail",)),
    UITaxonomyClass("BASKET", "Корзина", ("basket_add", "basket_remove"), ("shop", "grocery", "books", "rail")),
    UITaxonomyClass("FAV", "Избранное", ("add_favorites", "remove_favorites"), ("shop", "books")),
    UITaxonomyClass("FILTER", "Фильтрация / сортировка", ("apply_filter", "apply_sort"), ("rail", "books")),
    UITaxonomyClass("AUTH", "Авторизация", ("dialog_opened", "submit_phone", "submit_login", "submit_pass"), ("shop", "books")),
    UITaxonomyClass("PAY", "Оплата", ("submit_payment", "select_pay_method"), ("rail", "books")),
    UITaxonomyClass("FILES", "Кабинет файлов", ("bench_files_select_collection", "bench_files_select_year", "bench_files_download"), ("files",)),
    UITaxonomyClass("PASSIVE", "Пассивная телеметрия", ("click", "keypress", "scroll"), ("hub",)),
)

UI_TAXONOMY_CLASS_IDS: tuple[str, ...] = tuple(c.class_id for c in UI_TAXONOMY_CLASSES)
