# %%
# Каталог UI-паттернов для ручного тестирования (tests/bench).
# Перед запуском: ./scripts/start_dab.sh
#
# MODE = "catalog" — 6 оригиналов (по вкладке хаба) + уникальные виджеты + тёмная тема.
# MODE = "one"     — один трек, TASK_NAME = stem из tests/bench/tasks/ без .json

import json
import os

from bench_eval.bench_verify import BENCH_TESTS_DIR, merge
from bench_eval.task_dates import apply_booking_dates
from bench_eval.task_url import resolve_entry_url
from lib.src.agent_bench import client

API_ADDRESS = os.environ.get("BENCH_API_ADDRESS", "localhost:9000")
FRONTEND_HOST = os.environ.get("EVAL_FRONTEND_HOST", "localhost:5173")

MODE = "catalog"  # "catalog" | "one"
TASK_NAME = "ecommerce_basket_any_product"

# (pattern, task_stem) — явный список уникальных паттернов, не все клоны.
MANUAL_CASES = [
    # 6 оригиналов (дефолтные виджеты)
    ("shop:default", "ecommerce_basket_named_product_02"),
    ("books:default", "digital_books_named_product_basket"),
    ("grocery:default", "grocery_basket_named_product"),
    ("rail:default", "rail_book_to_cart"),
    ("hotels:default", "hotel_search_scenario"),
    ("files:default", "files_download_pdf"),
    # hotels — alt-виджеты
    ("date:inline_calendar", "hotel_search_scenario__date_inline_calendar"),
    ("date:text_input", "hotel_search_scenario__date_text_input"),
    ("date:single_popup", "hotel_search_scenario__date_single_popup"),
    ("select_city:native_select", "hotel_search_scenario__select_city_native_select"),
    ("counter_guests:inline_stepper", "hotel_search_scenario__counter_guests_inline_stepper"),
    ("counter_guests:compact_select", "hotel_search_scenario__counter_guests_compact_select"),
    ("counter_guests:pill_buttons", "hotel_search_scenario__counter_guests_pill_buttons"),
    # rail — alt-виджеты
    ("date:native_input", "rail_book_to_cart__date_native_input"),
    ("date:text_input", "rail_book_to_cart__date_text_input"),
    ("select_station:native_select", "rail_book_to_cart__select_station_native_select"),
    # files — mixed overlay
    ("files:list+years:buttons+buttons:icon", "files_download_pdf__files_list_buttons_icon"),
    # shop — text_search
    ("text_search:outlined", "ecommerce_basket_named_product_02__text_search_outlined"),
    ("text_search:filled", "ecommerce_basket_named_product_02__text_search_filled"),
    ("text_search:underlined", "ecommerce_basket_named_product_02__text_search_underlined"),
    ("text_search:pill", "ecommerce_basket_named_product_02__text_search_pill"),
    # theme:dark — по одному на раздел
    ("theme:dark", "ecommerce_basket_named_product_02__theme_dark"),
    ("theme:dark", "digital_books_named_product_basket__theme_dark"),
    ("theme:dark", "grocery_basket_named_product__theme_dark"),
    ("theme:dark", "rail_book_to_cart__theme_dark"),
    ("theme:dark", "hotel_search_scenario__theme_dark"),
    ("theme:dark", "files_download_pdf__theme_dark"),
]


def _cases():
    raw = [(TASK_NAME, TASK_NAME)] if MODE == "one" else list(MANUAL_CASES)
    cases = []
    for pattern, stem in raw:
        path = BENCH_TESTS_DIR / "tasks" / f"{stem}.json"
        if path.is_file():
            cases.append((pattern, stem))
        else:
            print(f"пропуск [{pattern}] {stem}: нет {path.name}")
    return cases


def _create_track(stem: str) -> tuple[str, dict, str]:
    task_path = BENCH_TESTS_DIR / "tasks" / f"{stem}.json"
    base = json.loads((BENCH_TESTS_DIR / "config.json").read_text(encoding="utf-8"))
    task = json.loads(task_path.read_text(encoding="utf-8"))
    config = merge(base, task)
    apply_booking_dates(config)
    config["test_data"]["test_name"] = stem

    track_id = stem.replace(" ", "_").lower()
    build_path = BENCH_TESTS_DIR / "build" / f"{track_id}.json"
    build_path.parent.mkdir(parents=True, exist_ok=True)
    build_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    client.create_track(
        name=track_id,
        id=track_id,
        filepath=str(build_path),
        address=API_ADDRESS,
        delete_existing=True,
    )
    return track_id, config, str(build_path)


# %%
# Создать треки на backend

created = []
for pattern, stem in _cases():
    track_id, config, build_path = _create_track(stem)
    site_host = f"http://{FRONTEND_HOST}/{track_id}"
    hub_url = f"{site_host}/state_hub/bench_hub"
    page_url = resolve_entry_url(site_host, build_path)
    td = config["test_data"]
    task_text = td["task"].replace("%HOST%", site_host)
    n_cond = len(td.get("conditions") or [])
    created.append(
        {
            "pattern": pattern,
            "stem": stem,
            "track_id": track_id,
            "page_url": page_url,
            "hub_url": hub_url,
            "task": task_text,
            "n_cond": n_cond,
        }
    )
    print(f"[{pattern}] {track_id}")
    print(f"  страница: {page_url}")
    print(f"  хаб:      {hub_url}")
    print(f"  conditions: {n_cond}")
    print(f"  задача: {task_text}")
    print()

print(f"Всего треков: {len(created)}")

# %%
# Проверить conditions после ручных действий

if not created:
    print("Нет треков — сначала выполните ячейку создания")
else:
    for item in created:
        print(f"[{item['pattern']}] {item['track_id']}")
        results = client.check(item["track_id"], address=API_ADDRESS)
        if not results:
            print("  Нет conditions или трек не найден")
            continue
        for cond in results:
            name = cond.get("event_name", "?")
            ok = cond.get("success", False)
            print(f"  {name}: {'OK' if ok else 'FAIL'}")
        print()
