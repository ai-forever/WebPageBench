/**
 * Единый каталог страниц бенчмарка: обезличенное имя маршрута → реализация.
 */

export const benchPageLoaders = {
  bench_hub: () => import('./hub/Main.vue'),

  bench_catalog_main: () => import('./shop/Main.vue'),
  bench_catalog_profile: () => import('./shop/Profile.vue'),
  bench_catalog_favorites: () => import('./shop/Favorites.vue'),
  bench_catalog_basket: () => import('./shop/Basket.vue'),
  bench_catalog_item: () => import('./shop/Item.vue'),
  bench_catalog_search: () => import('./shop/Search.vue'),
  bench_catalog_catalog: () => import('./shop/Catalog.vue'),
  bench_catalog_orders: () => import('./shop/Orders.vue'),
  bench_catalog_purchase: () => import('./shop/Purchase.vue'),
  bench_catalog_payment_success: () => import('./shop/PaymentSuccess.vue'),

  bench_books_main: () => import('./books/Main.vue'),
  bench_books_basket: () => import('./books/Basket.vue'),
  bench_books_purchase: () => import('./books/Purchase.vue'),
  bench_books_purchase_sbp: () => import('./books/PurchaseSbp.vue'),
  bench_books_purchase_spasibo: () => import('./books/PurchaseSpasibo.vue'),
  bench_books_purchase_rucard: () => import('./books/PurchaseRuCard.vue'),
  bench_books_purchase_mir: () => import('./books/PurchaseMir.vue'),
  bench_books_purchase_card: () => import('./books/PurchaseCard.vue'),
  bench_books_purchase_paypal: () => import('./books/PurchasePayPal.vue'),
  bench_books_item: () => import('./books/BookItem.vue'),
  bench_books_profile: () => import('./books/Profile.vue'),
  bench_books_my_books: () => import('./books/MyBooks.vue'),
  bench_books_payment_success: () => import('./books/PaymentSuccess.vue'),
  bench_books_search: () => import('./books/Search.vue'),
  bench_books_catalog: () => import('./books/Catalog.vue'),
  bench_books_favorites: () => import('./books/Favorites.vue'),

  bench_grocery_main: () => import('./grocery/Main.vue'),
  bench_grocery_authorization: () => import('./grocery/Authorization.vue'),
  bench_grocery_profile: () => import('./grocery/Profile.vue'),
  bench_grocery_category: () => import('./grocery/Category.vue'),
  bench_grocery_basket: () => import('./grocery/Basket.vue'),
  bench_grocery_purchase: () => import('./grocery/Purchase.vue'),
  bench_grocery_catalog: () => import('./grocery/Catalog.vue'),

  bench_rail_main: () => import('./rail/Main.vue'),
  bench_rail_search: () => import('./rail/Search.vue'),
  bench_rail_profile: () => import('./rail/Profile.vue'),
  bench_rail_tarif_selection: () => import('./rail/TarifSelection.vue'),
  bench_rail_seat_selection: () => import('./rail/SeatSelection.vue'),
  bench_rail_passenger_selection: () => import('./rail/PassengerSelection.vue'),
  bench_rail_tickets_checkout: () => import('./rail/TicketsCheckout.vue'),
  bench_rail_tickets_payment: () => import('./rail/TicketsPayment.vue'),

  bench_hotel_main: () => import('./hotels/Main.vue'),
  bench_hotel_search: () => import('./hotels/Search.vue'),
  bench_hotel_hotel: () => import('./hotels/Hotel.vue'),
  bench_hotel_checkout: () => import('./hotels/Checkout.vue'),

  bench_files_cabinet: () => import('./files/Cabinet.vue'),
  bench_files_collection: () => import('./files/Collection.vue'),
};

export const benchRouteNames = Object.keys(benchPageLoaders);
