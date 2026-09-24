# Отели

Раздел хаба `hotels`: страницы `views/bench/hotels/`, виджеты `src/hotels/`, маршруты `bench_hotel_*`.

## Создание трека

Канон — мерж `tests/bench/config.json` с задачей из `tests/bench/tasks/` (см. `example.py`). Минимальный фрагмент конфига:

```json
{
  "trackId": "hotel_search_scenario",
  "trackConfig": {
    "test_data": {
      "test_name": "hotel_search_scenario",
      "bench_first_domain": "hotels"
    },
    "state_main": {
      "view_type": "bench_hotel_main"
    },
    "state_search": {
      "view_type": "bench_hotel_search"
    },
    "state_hotel": {
      "view_type": "bench_hotel_hotel"
    },
    "state_checkout": {
      "view_type": "bench_hotel_checkout"
    }
  }
}
```

## Загрузка KV

Файлы: `site/backend/static/kv/hotels/hotels_index.json` и `hotels_<страна>.json`.

Фронт сначала запрашивает индекс, затем датасет страны.

- `id` — короткий идентификатор датасета, из него строится имя файла `hotels_<id>.json`
- `label` — отображаемое название страны/набора данных

Пример index:

```json
[
  { "id": "ch", "label": "Швейцария" },
  { "id": "jp", "label": "Япония" },
  { "id": "us", "label": "США" }
]
```

Пути картинок отелей в KV указывают на CDN-копии в `public` (байты медиа не меняем). Пример полей отеля:

```json
{
  "id": "hotel-zurich-central-001",
  "cityId": "zurich",
  "name": "Hotel Central Zürich",
  "address": "Central 1, Zürich",
  "stars": 4,
  "rating": 8.9,
  "reviews": 1243,
  "priceTotalRub": 24800,
  "nights": 2,
  "distanceKm": 0.8,
  "type": "hotel",
  "amenities": ["wifi", "breakfast"],
  "offer": {
    "roomTitle": "Стандартный номер",
    "beds": "1 двуспальная кровать",
    "mealPlan": "breakfast",
    "cancellation": "free",
    "payment": "online"
  }
}
```
