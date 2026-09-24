#!/usr/bin/env python3
"""Generate typical taxonomy task JSONs under tests/bench/tasks/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_ROOT = _SCRIPTS.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_SCRIPTS))
try:
    from brand_replacements import EVENT_RENAMES, apply_text_replacements
except ImportError:
    EVENT_RENAMES: dict[str, str] = {}

    def apply_text_replacements(s: str) -> str:
        return s
from bench_eval.ui_taxonomy_classify import annotate_task
from ui_pattern_task_map import apply_clone, list_clone_specs

OUT = Path(__file__).resolve().parents[1] / "tests" / "bench" / "tasks"
OUT.mkdir(parents=True, exist_ok=True)

LOGIN = {
    "login": "bench@example.com",
    "password": "bench123",
    "phone": "9150000000",
    "email": "bench@example.com",
}

VIEW_PREFIX_MAP = [
    ("МАРКЕТ_", "bench_catalog_"),
    ("Книги_", "bench_books_"),
    ("Доставка_", "bench_grocery_"),
    ("ЖД_", "bench_rail_"),
    ("Отели_", "bench_hotel_"),
]


def remap_view_type(name: str) -> str:
    if not isinstance(name, str):
        return name
    if name in ("bench_main", "Книги_main"):
        return "bench_hub" if name == "bench_main" else "bench_books_main"
    for old, new in VIEW_PREFIX_MAP:
        if name.startswith(old):
            return new + name[len(old) :]
    return name


def remap_params(params: dict | None) -> dict:
    if not params:
        return {}
    out = dict(params)
    if isinstance(out.get("new_state"), str):
        out["new_state"] = remap_view_type(out["new_state"])
    return out


def anonymize_task_text(s: str) -> str:
    return apply_text_replacements(s)


def cond(event_name: str, parameters: dict | None = None, description: str | None = None) -> dict:
    event_name = EVENT_RENAMES.get(event_name, event_name)
    c: dict = {"event_name": event_name}
    if parameters is not None:
        c["parameters"] = remap_params(parameters)
    if description:
        c["description"] = description
    return c


def base(domain: str, state: str, task: str, **extra) -> dict:
    td = {
        "login_data": LOGIN,
        "bench_first_domain": domain,
        "bench_first_state": state,
        "task": anonymize_task_text(task),
        **extra,
    }
    if extra.get("conditions"):
        td["conditions"] = extra["conditions"]
    return {"test_data": td}


def files_base(task: str, conditions: list, **extra) -> dict:
    td = {
        "login_data": LOGIN,
        "bench_first_domain": "files",
        "bench_first_state": "state_files_main",
        "task": anonymize_task_text(task),
        "conditions": conditions,
        **extra,
    }
    return {"test_data": td}


# fmt: off
TASKS: list[tuple[str, dict]] = [
    ("bench_grocery_navigation.json", base(
        "grocery", "state_grocery_main",
        "На %HOST% в «Продукты» открой главную, перейди по категориям меню и добавь товар в корзину.",
        conditions=[
            cond("state_changed", {"new_state": "bench_grocery_category"}),
            cond("basket_add", {}),
        ],
    )),

    # --- ecommerce: basket_named_product ---
    # Уточнения в промптах обязательны: в каталоге есть однобрендовые дубли
    # (Whiskas «Аппетитный обед» / «с нежным паштетом», Purina ONE
    # «для стерилизованных» / «при домашнем образе жизни», Zewa Deluxe 24 / 8 рулонов).
    ("ecommerce_basket_named_product_02.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» найди сухой корм Purina ONE для стерилизованных кошек с говядиной и пшеницей и добавь в корзину.",
        conditions=[cond("basket_add", {"item_id": "item_150030882", "amount": 1})],
    )),
    ("ecommerce_basket_named_product_03.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» найди туалетную бумагу Zewa Deluxe без аромата, 3 слоя, 24 рулона, и добавь в корзину.",
        conditions=[cond("basket_add", {"item_id": "item_1160040708", "amount": 1})],
    )),
    ("ecommerce_basket_named_smartphone.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» найди смартфон Google Pixel 9 Pro XL на 128 ГБ в серого цвета и добавь в корзину.",
        conditions=[cond("basket_add", {"item_id": "item_1864018295", "amount": 1})],
    )),

    # --- ecommerce: basket_multiple ---
    # amount — точное итоговое число в корзине (checker смотрит last qty, не промежуточный клик).
    ("ecommerce_basket_multiple_02.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» добавь в корзину 2 упаковки туалетной бумаги Papia Bali flower на 32 рулона.",
        conditions=[cond("basket_add", {"item_id": "item_647371114", "amount": 2})],
    )),

    # --- ecommerce: basket_typo ---
    ("ecommerce_basket_typo_02.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» найди сухой корм Перфект Фит «Лосось» для красивой шерсти (название на слух) и добавь в корзину.",
        conditions=[cond("basket_add", {"item_id": "item_2316709053", "amount": 1})],
    )),

    # --- ecommerce: favorites ---
    ("ecommerce_favorites_05.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» найди сухой корм для кошек CATTERA с говядиной и добавь в избранное.",
        conditions=[cond("add_favorites", {"item_id": "item_1805895777"})],
    )),

    # --- ecommerce: basket_typo ---
    ("ecommerce_basket_typo.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» найди сухой корм Puria ONE для стерилизованных кошек с говядиной (опечатка в названии) и добавь в корзину.",
        conditions=[cond("basket_add", {"item_id": "item_150030882", "amount": 1})],
    )),

    # --- ecommerce: favorites ---
    ("ecommerce_favorites.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» найди изотоник Batterade Arctic Storm и добавь в избранное.",
        conditions=[cond("add_favorites", {"item_id": "item_1441302164"})],
        target_events=["add_favorites", "state_changed"],
    )),

    # --- ecommerce: favorites_any_product ---
    ("ecommerce_favorites_any_product.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» добавь в избранное любой товар с главной страницы.",
        conditions=[cond("add_favorites", {})],
    )),

    # --- ecommerce: basket_any_product ---
    ("ecommerce_basket_any_product.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» добавь в корзину любой товар из каталога.",
        conditions=[cond("basket_add", {})],
    )),

    # --- ecommerce: basket_and_favorites ---
    ("ecommerce_basket_and_favorites.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» найди туалетную бумагу Zewa Deluxe без аромата на 24 рулона, добавь в избранное и в корзину.",
        conditions=[
            cond("basket_add", {"item_id": "item_1160040708"}),
            cond("add_favorites", {"item_id": "item_1160040708"}),
        ],
    )),
    ("ecommerce_basket_and_favorites_02.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» найди туалетную бумагу Zewa Deluxe без аромата на 8 рулонов, добавь её в корзину и в избранное.",
        conditions=[
            cond("basket_add", {"item_id": "item_29288925"}),
            cond("add_favorites", {"item_id": "item_29288925"}),
        ],
    )),

    # --- ecommerce: basket_price_constraint ---
    # Цены сверены с site/backend/static/kv/shop/shop_kv.json (поле data_price).
    ("ecommerce_basket_price_constraint.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» найди Bombbar Изотоник без сахара Оригинальный, 500 мл x 6 шт, и добавь в корзину (около 1100 ₽).",
        conditions=[cond("basket_add", {"item_id": "item_1646171704", "amount": 1})],
    )),
    ("ecommerce_basket_price_1k.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» добавь в корзину самый дешёвый товар с главной страницы каталога.",
        conditions=[cond("basket_add", {"item_id": "item_712618381", "amount": 1})],
    )),
    ("ecommerce_basket_price_35k.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» найди единственный смартфон дешевле 40 000 ₽ и добавь в корзину.",
        conditions=[cond("basket_add", {"item_id": "item_1048871548", "amount": 1})],
    )),

    # --- ecommerce: basket_multiple ---
    # amount — точное итоговое число в корзине.
    ("ecommerce_basket_multiple.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» найди сухой корм Whiskas «Аппетитный обед» и добавь в корзину 3 штуки.",
        conditions=[cond("basket_add", {"item_id": "item_136495278", "amount": 3})],
    )),

    # --- ecommerce: basket_multi_product ---
    # Несколько разных SKU с разным итоговым amount. Checker матчит last qty по item_id.
    ("ecommerce_basket_two_products.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» добавь в корзину 2 упаковки изотоника O.DRINK Multifruit Zero и 1 упаковку изотоника WaterON с электролитами и витамином С (10 стиков).",
        conditions=[
            cond("basket_add", {"item_id": "item_1931974549", "amount": 2}),
            cond("basket_add", {"item_id": "item_1554210173", "amount": 1}),
        ],
    )),
    ("ecommerce_basket_three_products.json", base(
        "shop", "state_shop_main",
        "На %HOST% в «Маркете» добавь в корзину 3 упаковки влажного корма Felix «Аппетитные кусочки» с ягнёнком в желе, 1 упаковку туалетной бумаги Zewa Just 1 на 12 рулонов (4 слоя) и 2 упаковки изотоника Snace со вкусом земляники.",
        conditions=[
            cond("basket_add", {"item_id": "item_714958775", "amount": 3}),
            cond("basket_add", {"item_id": "item_1417585321", "amount": 1}),
            cond("basket_add", {"item_id": "item_1717020676", "amount": 2}),
        ],
    )),

    # --- digital_books: named_product_basket ---
    ("digital_books_named_product_basket.json", base(
        "books", "state_books_main",
        "На %HOST% в «Книги» найди «Тихий янтарь в последнем вагоне» Веры Рудневой (текст) и добавь в корзину.",
        conditions=[
            cond("state_changed", {"new_state": "bench_books_item", "state_id": "item_72271483"}),
            cond("basket_add", {"item_id": "item_72271483"}),
        ],
    )),
    ("digital_books_named_product_basket_02.json", base(
        "books", "state_books_main",
        "На %HOST% в «Книги» найди «Ночной кипарис без обратного адреса!» (текст) и добавь в корзину.",
        conditions=[
            cond("state_changed", {"new_state": "bench_books_item", "state_id": "item_71273134"}),
            cond("basket_add", {"item_id": "item_71273134"}),
        ],
    )),

    # --- digital_books: named_product_favorites ---
    ("digital_books_named_product_favorites.json", base(
        "books", "state_books_main",
        "На %HOST% в «Книги» найди книгу «Ночной кипарис без обратного адреса!» (текст) и добавь в избранное.",
        conditions=[cond("add_favorites", {"item_id": "item_71273134"})],
    )),
    ("digital_books_named_product_favorites_02.json", base(
        "books", "state_books_main",
        "На %HOST% в «Книги» найди «Высокий циферблат» Генри Эшвуда в текстовом формате (не аудиокнигу) и добавь в избранное.",
        conditions=[cond("add_favorites", {"item_id": "item_51598283"})],
    )),
    ("digital_books_named_product_favorites_03.json", base(
        "books", "state_books_main",
        "На %HOST% в «Книги» найди «Белый камертон над тихой рекой» (текст) и добавь в избранное.",
        conditions=[cond("add_favorites", {"item_id": "item_66367392"})],
    )),

    # --- digital_books: author_aggregate_basket ---
    # Агрегаты требуют однозначного минимума/максимума по автору в books_kv.json.
    # У Генри Эшвуда максимум неоднозначен (679 ₽ у двух аудиокниг), поэтому
    # «самая дорогая» построена на Нике Ледневой (689 ₽ — единственный максимум).
    # У Эдварда Принса в каталоге одна книга — сравнение не требуется.
    # Вера Руднева: 18 книг, 139 ₽ — единственный минимум (Полина Шустова
    # имеет 20, но уже занята в author_expensive_favorites).
    ("digital_books_author_cheapest_basket.json", base(
        "books", "state_books_main",
        "На %HOST% в «Книги» найди самую дешёвую книгу автора Вера Руднева и добавь в корзину.",
        conditions=[
            cond("state_changed", {"new_state": "bench_books_item", "state_id": "item_68503715"}),
            cond("basket_add", {"item_id": "item_68503715"}),
        ],
    )),
    ("digital_books_author_expensive_basket.json", base(
        "books", "state_books_main",
        "На %HOST% в «Книги» найди самую дорогую книгу Ники Ледневой и добавь в корзину.",
        conditions=[
            cond("state_changed", {"new_state": "bench_books_item", "state_id": "item_69446647"}),
            cond("basket_add", {"item_id": "item_69446647"}),
        ],
    )),

    # --- digital_books: author_aggregate_favorites ---
    ("digital_books_author_expensive_favorites.json", base(
        "books", "state_books_main",
        "На %HOST% в «Книги» найди самую дорогую книгу Полины Шустовой и добавь в избранное.",
        conditions=[cond("add_favorites", {"item_id": "item_71466352"})],
    )),

    # --- digital_books: audio ---
    ("digital_books_audio_basket.json", base(
        "books", "state_books_main",
        "На %HOST% в «Книги» найди аудиокнигу «Тонкий фарфор у закрытой станции» и добавь в корзину.",
        conditions=[
            cond("state_changed", {"new_state": "bench_books_item", "state_id": "item_51565901"}),
            cond("basket_add", {"item_id": "item_51565901"}),
        ],
    )),
    ("digital_books_audio_favorites.json", base(
        "books", "state_books_main",
        "На %HOST% в «Книги» найди аудиокнигу «Белый секстант» Генри Эшвуда и добавь в избранное.",
        conditions=[cond("add_favorites", {"item_id": "item_41817095"})],
    )),
    ("digital_books_audio_basket_02.json", base(
        "books", "state_books_main",
        "На %HOST% в «Книги» найди аудиокнигу «Северный графит» и добавь в корзину.",
        conditions=[
            cond("state_changed", {"new_state": "bench_books_item", "state_id": "item_22967843"}),
            cond("basket_add", {"item_id": "item_22967843"}),
        ],
    )),

    # --- grocery ---
    # У раздела «Продукты» нет страницы поиска, а с главной доступны только пять
    # категорий (produkty_11, vsyo_goryachee_1, seychas_sezon, molochnoe_i_yaytsa,
    # tantsuyut_vse). Поэтому named_product берём с витрины главной либо из
    # produkty_11 — всё остальное недостижимо.
    ("grocery_basket_named_product.json", base(
        "grocery", "state_grocery_main",
        "На %HOST% в «Продукты» найди безлактозное молоко Parmalat Comfort 1,8% и добавь в корзину.",
        conditions=[cond("basket_add", {"item_id": "item_3b51864a"})],
    )),
    ("grocery_basket_named_product_02.json", base(
        "grocery", "state_grocery_main",
        "На %HOST% в «Продукты» найди розовые томаты Панамера и добавь в корзину.",
        conditions=[cond("basket_add", {"item_id": "item_9dfcd949"})],
    )),
    ("grocery_basket_price_expensive.json", base(
        "grocery", "state_grocery_main",
        "На %HOST% в «Продукты» добавь в корзину самый дорогой товар с витрины главной страницы.",
        conditions=[cond("basket_add", {"item_id": "item_9dfcd949"})],
    )),
    ("grocery_basket_multiple.json", base(
        "grocery", "state_grocery_main",
        "На %HOST% в «Продукты» добавь в корзину 3 упаковки безлактозного молока Parmalat Comfort 3,5%.",
        # amount — точное итоговое число в корзине.
        conditions=[cond("basket_add", {"item_id": "item_04dd559b", "amount": 3})],
    )),
    ("grocery_basket_category_named_product.json", base(
        "grocery", "state_grocery_main",
        "На %HOST% в «Продукты» открой категорию «Продукты», найди оливки без косточки и добавь в корзину.",
        conditions=[
            cond("state_changed", {"new_state": "bench_grocery_category"}),
            cond("basket_add", {"item_id": "item_66079548"}),
        ],
    )),
    ("grocery_basket_category_named_product_02.json", base(
        "grocery", "state_grocery_main",
        "На %HOST% в «Продукты» открой категорию «Овощи и фрукты», найди батат Артфрут и добавь в корзину.",
        conditions=[
            cond("state_changed", {"new_state": "bench_grocery_category"}),
            cond("basket_add", {"item_id": "item_9d1ebf15"}),
        ],
    )),
    ("grocery_basket_any_product.json", base(
        "grocery", "state_grocery_main",
        "На %HOST% в «Продукты» добавь в корзину любой товар из категории.",
        conditions=[cond("basket_add", {})],
    )),

    # --- hotel: search_scenario ---
    ("hotel_search_scenario.json", base(
        "hotels", "state_hotels_main",
        "На %HOST% в «Отели» покажи варианты: Цюрих, Швейцария, заезд 15.09.2026, выезд 20.09.2026, 2 гостя.",
        conditions=[
            cond("bench_hotel_select_city", {"cityId": "ch-zrh", "label": "Цюрих, Швейцария", "cityName": "Цюрих", "countryName": "Швейцария"}),
            cond("bench_hotel_select_start_date", {"date": "2026-09-15"}),
            cond("bench_hotel_select_end_date", {"date": "2026-09-20"}),
            cond("bench_hotel_select_guests", {"rooms": [{"adults": 2, "kids": []}], "roomsCount": 1, "guestsCount": 2}),
            cond("state_changed", {"new_state": "bench_hotel_search"}),
        ],
        target_events=["bench_hotel_select_city", "bench_hotel_select_start_date", "bench_hotel_select_end_date", "bench_hotel_select_guests", "state_changed"],
    )),
    ("hotel_search_scenario_family.json", base(
        "hotels", "state_hotels_main",
        "На %HOST% в «Отели» подбери жильё в Цюрихе, Швейцария с 15 по 20 сентября 2026 для 2 взрослых и ребёнка 7 лет в одном номере.",
        conditions=[
            cond("bench_hotel_select_city", {"cityId": "ch-zrh", "label": "Цюрих, Швейцария", "cityName": "Цюрих", "countryName": "Швейцария"}),
            cond("bench_hotel_select_start_date", {"date": "2026-09-15"}),
            cond("bench_hotel_select_end_date", {"date": "2026-09-20"}),
            cond("bench_hotel_select_guests", {"rooms": [{"adults": 2, "kids": [7]}], "roomsCount": 1, "guestsCount": 3}),
            cond("state_changed", {"new_state": "bench_hotel_search"}),
        ],
    )),

    ("hotel_search_scenario_dubai.json", base(
        "hotels", "state_hotels_main",
        "На %HOST% в «Отели» найди жильё в Дубае, ОАЭ на 05–09.03.2027 для 2 гостей и открой Marina Skyline Towers.",
        conditions=[
            cond("bench_hotel_select_city", {"cityId": "ae-dubai", "label": "Дубай, ОАЭ", "cityName": "Дубай", "countryName": "ОАЭ"}),
            cond("bench_hotel_select_start_date", {"date": "2027-03-05"}),
            cond("bench_hotel_select_end_date", {"date": "2027-03-09"}),
            cond("bench_hotel_select_guests", {"rooms": [{"adults": 2, "kids": []}], "roomsCount": 1, "guestsCount": 2}),
            cond("state_changed", {"new_state": "bench_hotel_search"}),
            cond("bench_hotel_select_hotel", {"hotelId": "h-ae-dubai-2", "hotelName": "Marina Skyline Towers", "cityId": "ae-dubai"}),
        ],
    )),
    ("hotel_search_scenario_seoul.json", base(
        "hotels", "state_hotels_main",
        "На %HOST% в «Отели» покажи варианты в Сеуле, Южная Корея с 01 по 05 октября 2026 для 2 гостей.",
        conditions=[
            cond("bench_hotel_select_city", {"cityId": "kr-sel", "label": "Сеул, Южная Корея", "cityName": "Сеул", "countryName": "Южная Корея"}),
            cond("bench_hotel_select_start_date", {"date": "2026-10-01"}),
            cond("bench_hotel_select_end_date", {"date": "2026-10-05"}),
            cond("bench_hotel_select_guests", {"rooms": [{"adults": 2, "kids": []}], "roomsCount": 1, "guestsCount": 2}),
            cond("state_changed", {"new_state": "bench_hotel_search"}),
        ],
    )),
    ("hotel_search_scenario_two_rooms.json", base(
        "hotels", "state_hotels_main",
        "На %HOST% в «Отели» подбери жильё в Милане, Италия на 12–16.09.2026: два номера по 2 взрослых в каждом.",
        conditions=[
            cond("bench_hotel_select_city", {"cityId": "it-mil", "label": "Милан, Италия", "cityName": "Милан", "countryName": "Италия"}),
            cond("bench_hotel_select_start_date", {"date": "2026-09-12"}),
            cond("bench_hotel_select_end_date", {"date": "2026-09-16"}),
            cond("bench_hotel_select_guests", {"rooms": [{"adults": 2, "kids": []}, {"adults": 2, "kids": []}], "roomsCount": 2, "guestsCount": 4}),
            cond("state_changed", {"new_state": "bench_hotel_search"}),
        ],
    )),

    # --- hotel: search_scenario_typo ---
    ("hotel_search_scenario_typo.json", base(
        "hotels", "state_hotels_main",
        "На %HOST% в «Отелях» укажи направление Токиео, Япония (с опечаткой в промпте).",
        conditions=[
            cond("bench_hotel_select_city", {"cityId": "jp-tyo", "label": "Токио, Япония", "cityName": "Токио", "countryName": "Япония"}),
        ],
    )),

    # --- hotel: atomic_ui_step ---
    ("hotel_atomic_select_city.json", base(
        "hotels", "state_hotels_main",
        "На %HOST% в «Отелях» укажи направление: Токио, Япония.",
        conditions=[
            cond("bench_hotel_select_city", {"cityId": "jp-tyo", "label": "Токио, Япония", "cityName": "Токио", "countryName": "Япония"}),
        ],
    )),
    ("hotel_atomic_select_start_date.json", base(
        "hotels", "state_hotels_main",
        "На %HOST% в «Отелях» выбери дату заезда 15 сентября 2026.",
        conditions=[cond("bench_hotel_select_start_date", {"date": "2026-09-15"})],
    )),

    # --- rail: atomic_ui_step ---
    ("rail_atomic_select_city_from.json", base(
        "rail", "state_rail_main",
        "На %HOST% в «Поездах» в поле «Откуда» укажи Москва.",
        conditions=[cond("select_city", {"field": "from", "name": "Москва"})],
    )),
    ("rail_atomic_select_date.json", base(
        "rail", "state_rail_main",
        "На %HOST% в «Поездах» выбери дату отправления 04 октября 2026.",
        conditions=[cond("select_date", {"date": "2026-10-04"})],
    )),

    # --- rail: book_to_cart ---
    # Не закрепляем train_name: `select_train`/`basket_add` логируют имя прямо из
    # rail_kv.json (ТВЕРСК, «экспресс», «Красная стрела», …), а конфиг обезличен —
    # обезличенного имени «экспресс» в событиях не бывает, такое условие
    # невыполнимо. Тариф закрепляем: сверен с tickets[].type в kv.
    ("rail_book_to_cart.json", base(
        "rail", "state_rail_main",
        "На %HOST% в «Поездах» найди поезд Москва — Санкт-Петербург на 04.10.2026, 1 пассажир, тариф «Эконом», добавь в корзину.",
        conditions=[
            cond("select_city", {"field": "from", "name": "Москва"}),
            cond("select_city", {"field": "to", "name": "Санкт-Петербург"}),
            cond("select_date", {"date": "2026-10-04"}),
            cond("submit_search", {}),
            cond("select_train", {}),
            cond("select_tariff", {"tarif_name": "Эконом"}),
            cond("select_seat", {"seats_amount": 1}),
            cond("select_passenger", {"passenger_index": 1}),
            cond("basket_add", {}),
        ],
        target_events=["select_city", "select_date", "submit_search", "select_train", "select_tariff", "select_seat", "select_passenger", "basket_add"],
    )),
    ("rail_book_to_cart_2_passengers.json", base(
        "rail", "state_rail_main",
        "На %HOST% в «Поездах» найди билеты Москва — Санкт-Петербург на 04.09.2026, 2 пассажира, добавь в корзину.",
        conditions=[
            cond("select_city", {"field": "from", "name": "Москва"}),
            cond("select_city", {"field": "to", "name": "Санкт-Петербург"}),
            cond("select_date", {"date": "2026-09-04"}),
            cond("submit_search", {}),
            cond("select_train", {}),
            cond("select_tariff", {}),
            cond("select_seat", {"seats_amount": 2}),
            cond("select_passenger", {"passenger_index": 1}),
            cond("select_passenger", {"passenger_index": 2}),
            cond("basket_add", {}),
        ],
    )),
    ("rail_book_to_cart_business.json", base(
        "rail", "state_rail_main",
        "На %HOST% в «Поездах» купи билет Москва — СПб на 22.09.2026, 1 пассажир, тариф «Бизнес», до корзины.",
        conditions=[
            cond("select_city", {"field": "from", "name": "Москва"}),
            cond("select_city", {"field": "to", "name": "Санкт-Петербург"}),
            cond("select_date", {"date": "2026-09-22"}),
            cond("select_train", {}),
            cond("select_tariff", {"tarif_name": "Бизнес"}),
            cond("basket_add", {}),
        ],
    )),

    # Тарифы ниже сверены с tickets[].type в rail_kv.json для маршрута
    # Москва → Санкт-Петербург: Купе, СВ, Люкс, Плацкартный, Первый класс, Бизнес.
    ("rail_book_to_cart_platskart.json", base(
        "rail", "state_rail_main",
        "На %HOST% в «Поездах» подбери плацкартный билет Москва — Санкт-Петербург на 04.10.2026 и добавь в корзину.",
        conditions=[
            cond("select_city", {"field": "from", "name": "Москва"}),
            cond("select_city", {"field": "to", "name": "Санкт-Петербург"}),
            cond("select_date", {"date": "2026-10-04"}),
            cond("submit_search", {}),
            cond("select_tariff", {"tarif_name": "Плацкартный"}),
            cond("basket_add", {}),
        ],
    )),

    # --- rail: book_pay_checkout ---
    ("rail_book_and_pay_business.json", base(
        "rail", "state_rail_main",
        "На %HOST% в «Поездах» купи и оплати билет Москва — Санкт-Петербург на 22.09.2026, 1 пассажир, тариф «Бизнес».",
        conditions=[
            cond("select_city", {"field": "from", "name": "Москва"}),
            cond("select_city", {"field": "to", "name": "Санкт-Петербург"}),
            cond("select_date", {"date": "2026-09-22"}),
            cond("select_tariff", {"tarif_name": "Бизнес"}),
            cond("basket_add", {}),
            cond("submit_payment", {"result": "success"}),
        ],
    )),
    ("rail_book_and_pay.json", base(
        "rail", "state_rail_main",
        "На %HOST% в «Поездах» купи билет Москва — СПб на 22.09.2026, 1 пассажир, тариф «Эконом»: в корзину и оплати.",
        conditions=[
            cond("select_city", {"field": "from", "name": "Москва"}),
            cond("select_city", {"field": "to", "name": "Санкт-Петербург"}),
            cond("select_date", {"date": "2026-09-22"}),
            cond("select_train", {}),
            cond("select_tariff", {"tarif_name": "Эконом"}),
            cond("basket_add", {}),
            cond("submit_payment", {"result": "success"}),
        ],
    )),
    ("rail_book_and_pay_2_passengers.json", base(
        "rail", "state_rail_main",
        "На %HOST% в «Поездах» оформи и оплати билет Москва — Санкт-Петербург на 04.09.2026 для 2 пассажиров.",
        conditions=[
            cond("select_city", {"field": "from", "name": "Москва"}),
            cond("select_city", {"field": "to", "name": "Санкт-Петербург"}),
            cond("select_date", {"date": "2026-09-04"}),
            cond("select_seat", {"seats_amount": 2}),
            cond("select_passenger", {"passenger_index": 1}),
            cond("select_passenger", {"passenger_index": 2}),
            cond("basket_add", {}),
            cond("submit_payment", {"result": "success"}),
        ],
    )),

    # --- files cabinet ---
    ("files_select_collection.json", files_base(
        "На %HOST% в разделе «Файлы» выбери коллекцию «Отчёты лаборатории».",
        [cond("bench_files_select_collection", {"collection": "lab_reports"})],
    )),
    ("files_select_year.json", files_base(
        "На %HOST% в разделе «Файлы» открой «Отчёты лаборатории» и выбери 2024 год.",
        [
            cond("bench_files_select_collection", {"collection": "lab_reports"}),
            cond("bench_files_select_year", {"year": "2024"}),
        ],
    )),
    ("files_select_year_archive.json", files_base(
        "На %HOST% в разделе «Файлы» открой «Архив проектов» и выбери 2023 год — появится список файлов.",
        [
            cond("bench_files_select_collection", {"collection": "project_archive"}),
            cond("bench_files_select_year", {"year": "2023"}),
        ],
    )),
    ("files_download_pdf.json", files_base(
        "На %HOST% в разделе «Файлы» открой «Отчёты лаборатории», выбери 2024 год и скачай файл lab-reports-2024.pdf.",
        [
            cond("bench_files_select_collection", {"collection": "lab_reports"}),
            cond("bench_files_select_year", {"year": "2024"}),
            cond("bench_files_download", {"collection": "lab_reports", "year": "2024", "format": "pdf", "file": "lab-reports-2024.pdf"}),
        ],
    )),
    ("files_download_csv.json", files_base(
        "На %HOST% в разделе «Файлы» открой «Отчёты лаборатории», выбери 2025 год и скачай файл lab-reports-2025.csv.",
        [
            cond("bench_files_select_collection", {"collection": "lab_reports"}),
            cond("bench_files_select_year", {"year": "2025"}),
            cond("bench_files_download", {"collection": "lab_reports", "year": "2025", "format": "csv", "file": "lab-reports-2025.csv"}),
        ],
    )),
    ("files_archive_pdf.json", files_base(
        "На %HOST% в разделе «Файлы» открой «Архив проектов», выбери 2023 год и среди файлов скачай годовой PDF project-archive-2023.pdf.",
        [
            cond("bench_files_select_collection", {"collection": "project_archive"}),
            cond("bench_files_select_year", {"year": "2023"}),
            cond("bench_files_download", {"collection": "project_archive", "year": "2023", "format": "pdf", "file": "project-archive-2023.pdf"}),
        ],
    )),
    # Без имени файла: на карточке «Добавлен 22.03.2024», в марте CSV один.
    ("files_archive_csv.json", files_base(
        "На %HOST% в разделе «Файлы» открой «Архив проектов», выбери 2024 год и скачай CSV от 22 марта.",
        [
            cond("bench_files_select_collection", {"collection": "project_archive"}),
            cond("bench_files_select_year", {"year": "2024"}),
            cond("bench_files_download", {"collection": "project_archive", "year": "2024", "format": "csv", "file": "project-archive-2024.csv"}),
        ],
    )),
    ("files_archive_month_pdf.json", files_base(
        "На %HOST% в разделе «Файлы» открой «Архив проектов», выбери 2023 год и скачай файл за июнь project-archive-2023-06.pdf.",
        [
            cond("bench_files_select_collection", {"collection": "project_archive"}),
            cond("bench_files_select_year", {"year": "2023"}),
            cond("bench_files_download", {"collection": "project_archive", "year": "2023", "format": "pdf", "file": "project-archive-2023-06.pdf"}),
        ],
    )),
    # Февраль 2024 в архиве один файл — в промпте только месяц, без имени и расширения.
    ("files_archive_month_csv.json", files_base(
        "На %HOST% в разделе «Файлы» открой «Архив проектов», выбери 2024 год и скачай файл за февраль.",
        [
            cond("bench_files_select_collection", {"collection": "project_archive"}),
            cond("bench_files_select_year", {"year": "2024"}),
            cond("bench_files_download", {"collection": "project_archive", "year": "2024", "format": "csv", "file": "project-archive-2024-02.csv"}),
        ],
    )),
    # 31 марта PDF неоднозначен (тот же день у квартального q1). 30 сентября PDF уникален.
    ("files_archive_date.json", files_base(
        "На %HOST% в разделе «Файлы» открой «Архив проектов», выбери 2024 год и скачай PDF от 30 сентября.",
        [
            cond("bench_files_select_collection", {"collection": "project_archive"}),
            cond("bench_files_select_year", {"year": "2024"}),
            cond("bench_files_download", {"collection": "project_archive", "year": "2024", "format": "pdf", "file": "project-archive-2024-09-30.pdf"}),
        ],
    )),
    ("files_archive_quarter.json", files_base(
        "На %HOST% в разделе «Файлы» открой «Архив проектов», выбери 2024 год и скачай квартальный PDF project-archive-2024-q1.pdf.",
        [
            cond("bench_files_select_collection", {"collection": "project_archive"}),
            cond("bench_files_select_year", {"year": "2024"}),
            cond("bench_files_download", {"collection": "project_archive", "year": "2024", "format": "pdf", "file": "project-archive-2024-q1.pdf"}),
        ],
    )),
]
# fmt: on


def main() -> None:
    annotated_by_stem: dict[str, dict] = {}
    outputs: list[tuple[str, dict]] = []
    for name, data in TASKS:
        stem = Path(name).stem
        annotated = annotate_task(data, task_stem=stem)
        annotated_by_stem[stem] = annotated
        outputs.append((name, annotated))

    missing_sources: list[str] = []
    for spec in list_clone_specs():
        base = annotated_by_stem.get(spec.source_stem)
        if base is None:
            missing_sources.append(spec.source_stem)
            continue
        outputs.append((spec.filename, apply_clone(base, spec)))
    if missing_sources:
        raise SystemExit(f"Clone source tasks missing from TASKS: {sorted(set(missing_sources))}")

    defined = {name for name, _ in outputs}
    for old in OUT.glob("*.json"):
        if old.name not in defined:
            old.unlink()
            print("removed", old.name)

    for name, data in outputs:
        path = OUT / name
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {len(outputs)} tasks ({len(TASKS)} base + {len(outputs) - len(TASKS)} clones) to {OUT}")


if __name__ == "__main__":
    main()
