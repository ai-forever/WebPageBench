# Создание нового раздела WebPageBench

Инструкция по добавлению мок-раздела на примере **Маркета** (`views/bench/shop`).

В реальном магазине много экранов. В бенчмарке достаточно основного сценария: поиск → карточка → корзина → оплата. Реализуйте только то, что связано с задачами в `tests/bench/tasks/`.

Канон: шесть вкладок хаба (`shop`, `books`, `grocery`, `rail`, `hotels`, `files`) и маршруты `bench_*`. Реестр страниц — `site/frontend/src/views/bench/registry.js`.

## Страницы

Пример Маркета:

- Главная. `site/frontend/src/views/bench/shop/Main.vue`
- Результаты поиска. `site/frontend/src/views/bench/shop/Search.vue`
- Карточка товара. `site/frontend/src/views/bench/shop/Item.vue`
- Корзина. `site/frontend/src/views/bench/shop/Basket.vue`
- Оформление заказа. `site/frontend/src/views/bench/shop/Purchase.vue`
- Результат покупки. `site/frontend/src/views/bench/shop/PaymentSuccess.vue`
- Логин. Диалог `shop/components/ShopLoginDialog.vue` или отдельная страница.

### Дополнительные страницы

Заглушки с данными из конфига и кнопкой выхода:

- Профиль. `site/frontend/src/views/bench/shop/Profile.vue`
- Каталог. `site/frontend/src/views/bench/shop/Catalog.vue`
- Избранное. `site/frontend/src/views/bench/shop/Favorites.vue`

## Данные

### Описание товаров

Каталог лежит в KV JSON, путь задаётся в `tests/bench/config.json` (`kv_store_path` / `domain_configs`).

Для Маркета: `site/backend/static/kv/shop/shop_kv.json`.

Сайт при загрузке трека подтягивает файл через API. Запись выглядит так:

```json
{
  "item_136495278": {
    "id": "item_136495278",
    "name": "Whiskas «Аппетитный обед»",
    "price": 89,
    "currency": "RUB",
    "img": "/static/..."
  }
}
```

По ключам из KV страница берёт конкретный товар. Поля URL картинок не фильтруются.

### Картинки

Логотипы и баннеры — в `site/frontend/src/assets/img`. Во вьюхах они подключаются через `shop-assets.js` / `books-assets.js` / …, чтобы Vue разрешал относительные пути.

Картинки товаров в каталоге обычно остаются URL из KV.

## Роутер

Связь путь → `view_type` → компонент задаётся в `registry.js` и `router/benchRoutes.js`:

```js
export const benchPageLoaders = {
  bench_catalog_main: () => import('./shop/Main.vue'),
  bench_catalog_basket: () => import('./shop/Basket.vue'),
  // …
};
```

Маршрут: `/:track_id/:state_id/bench_catalog_main`. Имя маршрута (`bench_catalog_main`) — это `view_type` в конфиге. Переход:

```js
this.$router.push({
  name: 'bench_catalog_item',
  params: { state_id: 'item_136495278', track_id: this.$route.params.track_id },
});
```

Один `view_type` обслуживает много `state_id` (карточки товаров).

`:track_id` задаётся при создании трека. Если открыть только `/{track_id}` без пути, берётся стартовое состояние из конфига (`bench_hub` / `bench_first_state`).

## Local storage

Состояние пользователя (корзина, избранное, логин) хранится в localStorage через `site/frontend/src/utils/localCache.js` (`getShopBasket`, `favorites_shop`, …).

## Конфиги

Базовый конфиг: `tests/bench/config.json`. Задача: `tests/bench/tasks/<name>.json` (мержится поверх базы).

В `test_data`:

```json
"test_data": {
  "login_data": { "login": "bench@example.com", "password": "bench123", "phone": "9150000000" },
  "card_data": { "number": "4000060000000006", "date": "10/35", "cvv": "102" },
  "kv_store_path": "shop/shop_kv.json"
}
```

Креды логина и карты сверяются с тем, что агент вводит на моке.

В `common_elements` / `domain_configs.<domain>` — хедер, меню, поиск, сетки товаров (`kv_id`).

В секциях `state_*` задаётся `view_type` страницы.

## Логирование

Пассивные события — mixin `ActivityTracker` (`site/frontend/src/common/tracker.js`).

Кастомные события:

```js
import { _logActivity } from "@/common/trackHelper";

_logActivity(this, { type: 'submit_login', value: this.login, result: 'success' });
_logActivity(this, { type: 'dialog_opened', name: 'login' });
```

События отелей: `useHotelTrackEvent` (`site/frontend/src/hotels/composable/useHotelTrackEvent.ts`).

Все события уходят на backend и привязаны к `track_id`.

## События

`target_events` в конфиге ни на что не влияет — подсветка на `/<track>/events`.

`conditions` — набор событий для проверки. В `parameters` указываются только сверяемые поля. Пример: лог `{"type":"state_changed","new_state":"bench_catalog_basket"}` → условие `{"event_name":"state_changed","parameters":{"new_state":"bench_catalog_basket"}}`.

Для количества в корзине `amount` — **точное итоговое** число этого `item_id`, не «хотя бы N». Чекер смотрит последнее `basket_add` / `basket_remove` по товару: если в задаче `amount: 2`, а в корзине 3, условие не проходит, даже если по пути было 2.

Типовые события:

- `basket_add` / `basket_remove` — корзина (`item_id`, `amount`)
- `add_favorites` / `remove_favorites` — избранное
- `state_changed` — переход (`new_state` = имя маршрута `bench_*`)
- `submit_search` — поиск
- `submit_login` / `submit_phone` / `submit_pass` — авторизация
- `dialog_opened` — модалка
- `select_pay_method` / `submit_payment` — оплата
- `select_city` / `select_date` / `select_train` / `select_tariff` / `select_seat` — поезда
- `bench_hotel_select_*` — отели
- `bench_files_*` — кабинет файлов

Недостающие события добавляйте через `_logActivity`.

## Client

Библиотека: `./lib`. Создание трека:

```python
from lib.src.agent_bench import client

client.create_track(
    name="Test shop basket",
    id="ecommerce_basket_any_product",
    filepath="./tests/bench/build/ecommerce_basket_any_product.json",
    address="localhost:9000",
    delete_existing=True,
)
```

См. `example.py` и `tests.py` — они мержат `tests/bench/config.json` с задачей из `tests/bench/tasks/`.
