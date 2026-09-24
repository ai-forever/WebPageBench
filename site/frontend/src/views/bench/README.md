# Единый каталог бенчмарка (`views/bench`)

Обезличенные маршруты `bench_*`. Реестр: `registry.js`. Маршруты: `router/benchRoutes.js`.

| Префикс | Домен | Папка |
|---------|--------|--------|
| `bench_hub` | главная | `hub/` |
| `bench_catalog_*` | Маркет | `shop/` |
| `bench_books_*` | Книги | `books/` |
| `bench_grocery_*` | Продукты | `grocery/` |
| `bench_rail_*` | Поезда | `rail/` |
| `bench_hotel_*` | Отели | `hotels/` |
| `bench_files_*` | Файлы | `files/` |

Композируемые отельные виджеты: `site/frontend/src/hotels/`. CSS-корни разделов: `.bench-market`, `.bench-books`, `.bench-grocery`, `.bench-rail`, `.bench-hotels`, `.bench-files`.

Алиас `bench_main` указывает на тот же компонент, что и `bench_hub`.
