# Типовые задачи `tests/bench/tasks`

Сгенерировано: `python3 scripts/build_bench_tasks.py` (**152** файла: 65 канонических + 87 вариантов контролов). Карта вариантов: `scripts/ui_pattern_task_map.py`.

Канон — JSON в `tests/bench/tasks/` (сценарий, `conditions`, `ui_taxonomy`). Каталог `tests/bench/build/` — локальный дамп смерженных треков и артефактов прогона, в git не входит.

Распределение по доменам и вариантам не дублируется здесь; актуальная сводка
находится в [TAXONOMY.md](./TAXONOMY.md#разделы-бенчмарка-вкладки-хаба).

## Сводка по подкатегориям

Канонические сценарии (варианты наследуют подкатегорию донора; суффикс `__widget_variant` / `__theme_dark`).

| Подкатегория | Файлов | Примеры |
|--------------|-------:|---------|
| `basket_named_product` | 7 | `ecommerce_basket_named_product_{02,03}.json`, `ecommerce_basket_named_smartphone.json`, `grocery_basket_named_product{,_02}.json`, `grocery_basket_category_named_product{,_02}.json` |
| `basket_typo` | 2 | `ecommerce_basket_typo{,_02}.json` |
| `favorites` | 2 | `ecommerce_favorites.json`, `ecommerce_favorites_05.json` |
| `favorites_any_product` | 1 | `ecommerce_favorites_any_product.json` |
| `basket_any_product` | 2 | `ecommerce_basket_any_product.json`, `grocery_basket_any_product.json` |
| `basket_and_favorites` | 2 | `ecommerce_basket_and_favorites{,_02}.json` |
| `basket_price_constraint` | 4 | `ecommerce_basket_price_{1k,35k,constraint}.json`, `grocery_basket_price_expensive.json` |
| `basket_multiple` | 3 | `ecommerce_basket_multiple{,_02}.json`, `grocery_basket_multiple.json` |
| `basket_multi_product` | 2 | `ecommerce_basket_two_products.json`, `ecommerce_basket_three_products.json` |
| Навигация по категориям | 1 | `bench_grocery_navigation.json` |
| Книги: по названию | 2 | `digital_books_named_product_basket{,_02}.json` |
| Книги: избранное по названию | 3 | `digital_books_named_product_favorites*.json` |
| Книги: агрегат по автору | 3 | `digital_books_author_*.json` |
| Книги: аудио | 3 | `digital_books_audio_*.json` |
| `search_scenario` | 5 | `hotel_search_scenario*.json` (Цюрих, Дубай, семья с ребёнком, Сеул, два номера) |
| `search_scenario_typo` | 1 | `hotel_search_scenario_typo.json` |
| `atomic_ui_step` (отели) | 2 | `hotel_atomic_select_{city,start_date}.json` |
| `atomic_ui_step` (поезда) | 2 | `rail_atomic_select_{city_from,date}.json` |
| `book_to_cart` | 4 | `rail_book_to_cart*.json` — 1/2 пассажира, тарифы Эконом, Бизнес, Плацкартный |
| `book_pay_checkout` | 3 | `rail_book_and_pay*.json` |
| Кабинет файлов | 11 | `files_select_collection.json`, `files_select_year*.json`, `files_download_{csv,pdf}.json`, `files_archive_*.json` |

## Сводка по классам UI-таксономии (`ui_taxonomy.primary`)

| Класс | Файлов |
|-------|-------:|
| `BASKET` | 33 |
| `FILES` | 11 |
| `FAV` | 8 |
| `COUNTER` | 4 |
| `PAY` | 3 |
| `SELECT_AC` | 2 |
| `DATE` | 2 |
| `CARD` | 1 |
| `SELECT_LIST` | 1 |

## Инварианты

Все `new_state` в conditions используют обезличенные имена (`bench_catalog_main`,
`bench_books_item`, `bench_hotel_search`, …).

Условия сверяются с событиями **по точному равенству** каждого закреплённого
параметра (`lib/src/agent_bench/client.py`), поэтому любое значение в
`conditions[].parameters` должно совпадать с тем, что мок реально логирует.

### Товары и цены

Задачи с ценами и агрегатами («самый дешёвый», «самая дорогая книга автора»)
опираются на данные `site/backend/static/kv/{shop,books,grocery}/*.json`:

* цена в промпте должна соответствовать `data_price` (Маркет) / `price`
  (Книги, Продукты) целевого товара;
* агрегат по автору требует **однозначного** минимума/максимума — при равенстве
  цен у двух книг задача нерешаема (так, у Генри Эшвуда и минимум, и максимум
  неоднозначны: 499 ₽ и 679 ₽ сразу у двух книг). Поэтому «самая дорогая»
  построена на Нике Ледневой (689 ₽) и Полине Шустовой (479 ₽), а «самая дешёвая»
  — на Вере Рудневой (139 ₽). У Эдварда Принса в каталоге одна книга;
* названный товар должен быть достижим от стартового состояния: у «Продуктов»
  нет страницы поиска, поэтому достижимы только витрина главной и пять
  категорий, на которые ведут пункты меню (`produkty_11`, `vsyo_goryachee_1`,
  `seychas_sezon`, `molochnoe_i_yaytsa`, `tantsuyut_vse`);
* промпт должен однозначно указывать на один товар — в Маркете есть
  однобрендовые дубли (Whiskas «Аппетитный обед» / «с нежным паштетом»,
  Purina ONE «для стерилизованных» / «при домашнем образе жизни»,
  Zewa Deluxe на 24 / 8 рулонов, Papia белая / Papia Bali flower,
  KIX / KIX Aroma Sense). Книги в Маркете и Продуктах не продаются
  (только вкладка «Книги»). В Маркете есть бакалея и молочка (копии
  упакованных SKU из Продуктов, крошка «Продукты питания»); они
  доступны поиском, на витрину попадают только дороже STEELPOWER.
  Уникальные якоря витрины Маркета: самый дешёвый SKU — STEELPOWER
  `item_712618381` (1004 ₽); единственный смартфон дешевле 40 000 ₽ —
  `item_1048871548`.

### Поезда

`select_train` и `basket_add` логируют `train_name` **прямо из `rail_kv.json`**
(`ТВЕРСК`, `«экспресс»`, `«Красная стрела»`, `«Экспресс»`, …). Поэтому `train_name`
в conditions не закрепляется: такое условие невыполнимо без точного совпадения с KV.

Тариф (`select_tariff.tarif_name`) закреплять можно — значения сверены с
`tickets[].type`. Для маршрута Москва → Санкт-Петербург поиск возвращает 8
поездов, суммарно дающих: `Эконом`, `Эконом+`, `Бизнес`, `Первый класс`, `Купе`,
`СВ`, `Люкс`, `Плацкартный`, `Купе (для инвалидов)`.

### Отели

`bench_hotel_select_guests` логирует полную структуру номеров:

```
{"rooms": [{"adults": 2, "kids": []}], "roomsCount": 1, "guestsCount": 2}
{"rooms": [{"adults": 2, "kids": [7]}], "roomsCount": 1, "guestsCount": 3}
{"rooms": [{"adults": 2, "kids": []}, {"adults": 2, "kids": []}], "roomsCount": 2, "guestsCount": 4}
```

Возраст ребёнка попадает в `kids` списком. `cityId` / `hotelId` берутся из
`site/backend/static/kv/hotels/hotels_*.json`, `label` имеет вид
«Город, Страна».

### Файлы

Задачи стартуют в кабинете коллекций (`bench_files_cabinet`), без логина и поиска.
Ярлыки коллекций совпадают с `domain_configs.files.collections`: «Отчёты лаборатории»,
«Архив проектов», «Руководства», «Наборы данных». Пока год не выбран, карточек файлов нет.
После выбора года список зависит от коллекции: у отчётов/руководств/датасетов коротко
(2–5 файлов), в архиве — 12 (2023) и 18 (2024) файлов с именами месяцев `YYYY-MM`, дат и квартала.
Часть задач называет файл явно; в `files_archive_csv` / `files_archive_month_csv` / `files_archive_date` имени нет: только дата и расширение на карточке «Добавлен», либо месяц, если в срезе месяца файл один. Скачивать нужно найденный файл, а не первую карточку.

Задачи `files_download_*` / `files_archive_*`
требуют **реального скачивания файла**: в eval-пути это включается `agent_downloads_enabled`
(см. `bench_eval/browser_profile.py`), который также заставляет использовать
полноценный Chromium вместо `chrome-headless-shell`. Файлы лежат в
`site/frontend/public/mocks/files/`.
