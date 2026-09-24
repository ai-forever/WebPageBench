<template>
  <article class="card">
    <div class="imgWrap">
      <img class="img" :src="hotel.imageUrl" alt="" />
    </div>

    <div class="body">

      <div class="top">
        <div class="hotel-card-content">
          <div class="hotel-card-headline">{{ hotel.name }}</div>
          <div class="hotel-card-stars">
            <HotelStars :stars="hotel.stars" :size="10" />
          </div>
          <div class="hotel-card-distances">
            <div class="hotel-card-address">{{ hotel.address }}</div>
            <div class="hotel-card-center">{{ hotel.distanceKm.toFixed(1) }} км до центра {{ hotel.address.split(', ').pop() }}</div>
          </div>
        </div>

        <div class="hotel-card-rating">
          <HotelRatingBadge :rating="hotel.rating" :reviews="hotel.reviews" />
        </div>
      </div>

      <div style="display: flex;">
        <div style="margin-inline-start: auto;">
          <HotelAmenities :amenities="hotel.amenities" :limit="5" />
        </div>
      </div>

      <div class="root">
        <div class="root-content">
          <div class="root-content-room">
            <div style="display: inline-flex;">
              <p class="room-title">{{ offer.roomTitle }}</p>
            </div>
            <p class="room-beds">{{ offer.beds }}</p>
          </div>
        
          <div style="flex: 2;">
            <ul class="room-value-list">
              <li v-for="p in roomPoints" :key="p.key" class="room-value-list-point">
                <div class="room-value-list-icon" :class="p.icon"></div>
                <p class="room-value-text">{{ p.text }}</p>
              </li>
            </ul>
          </div>
        
          <div class="price-container">
            <div class="rate-price">{{ rubleCurrency(hotel.priceTotalRub) }}</div>
            <div class="rate-destination">
              за {{ nightsShown }} ночей для {{ guestsShown }} {{ pluralGuests(guestsShown) }}
            </div>
          </div>
        </div>
      </div>

      <div class="bottom">
        <button class="btn" type="button" @click="goToHotelById(hotel.id)">
          Показать все номера
        </button>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import type { Hotel, HotelOffer, MealPlan, CancellationPolicy, PaymentType } from '@/hotels/services/searchDataset';
import HotelStars from './HotelStars.vue';
import HotelRatingBadge from './HotelRatingBadge.vue';
import HotelAmenities from './HotelAmenities.vue';
import { rubleCurrency } from '@/hotels/utils/rubleCurrency';
import { HOTEL_EVENTS, useHotelTrackEvent } from '@/hotels/composable/useHotelTrackEvent';
import { pushBenchRoute } from '@/common/benchNavigation';

const { send } = useHotelTrackEvent();

const props = defineProps<{
  hotel: Hotel;

  // ✅ приходит из страницы поиска
  nights?: number;
  guests?: number;
  rooms?: number;
  children?: number;
}>();

const route = useRoute();
const router = useRouter();

function goToHotel() {
  pushBenchRoute(router, {
    name: 'bench_hotel_hotel',
    stateId: 'state_hotels_hotel',
    trackId: route.params.track_id,
    query: {
      ...route.query,
      hotelId: (route.query.hotelId ?? undefined),
    },
  });
}

// ВАЖНО: route.query мы используем текущий,
// но hotelId надо поставить именно от этого отеля:
function goToHotelById(hotelId: string) {
  send(HOTEL_EVENTS.selectHotel, {
    hotelId,
    hotelName: props.hotel.name,
    cityId: props.hotel.cityId,
  });
  pushBenchRoute(router, {
    name: 'bench_hotel_hotel',
    stateId: 'state_hotels_hotel',
    trackId: route.params.track_id,
    query: {
      ...route.query,
      hotelId,
    },
  });
}

const rub = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 });

const nightsShown = computed(() => Math.max(1, props.nights ?? 1));
const guestsShown = computed(() => Math.max(1, props.guests ?? 2));

function pluralGuests(n: number) {
  const n10 = n % 10;
  const n100 = n % 100;
  if (n100 >= 11 && n100 <= 14) return 'гостей';
  if (n10 === 1) return 'гостя';
  if (n10 >= 2 && n10 <= 4) return 'гостей';
  return 'гостей';
}

// ✅ дефолт на случай если offer не задан в JSON
const offer = computed<HotelOffer>(() => {
  const o = props.hotel.offer;
  if (o) return o;

  const mealPlan: MealPlan = props.hotel.amenities?.includes('breakfast') ? 'breakfast' : 'none';
  const cancellation: CancellationPolicy = 'no_free';
  const payment: PaymentType = 'online';

  return {
    roomTitle: 'Двухместный номер люкс',
    beds: 'двуспальная кровать',
    mealPlan,
    cancellation,
    payment,
  };
});

const roomPoints = computed(() => {
  const o = offer.value;

  return [
    {
      key: 'meal',
      icon: 'meal',
      text: o.mealPlan === 'breakfast' ? 'Завтрак включён' : 'Питание не вкл.',
    },
    {
      key: 'cancellation',
      icon: 'cancellation',
      text: o.cancellation === 'free' ? 'Бесплатная отмена' : 'Без беспл. отмены',
    },
    {
      key: 'payment',
      icon: 'payment',
      text: o.payment === 'at_hotel' ? 'Оплата в отеле' : 'Оплата на сайте',
    },
  ];
});
</script>

<style scoped>
.rate-destination {
  text-align: end;
  flex-basis: 100%;

  color: #868686;
  font-size: 12px;
  font-weight: 480;
  line-height: 16px;
}

.rate-price {
  align-items: flex-end;
  column-gap: 4px;
  display: flex;
  flex-wrap: wrap;

  font-size: 20px;
  line-height: 24px;
  color: var(--bench-text, #2d3137);
  font-weight: 700;
}

.price-container {
  align-items: flex-end;
  display: flex;
  flex-direction: column;

  flex: 2;
}

.room-value-text {
  font-size: 12px;
  font-weight: 500;
  line-height: 16px;

  color: var(--bench-text, #2d3137);
}

.meal {
  -webkit-mask-image: url(/hotels/cdn/meal.418dda29.svg);
  mask-image: url(/hotels/cdn/meal.418dda29.svg);
}

.cancellation {
  -webkit-mask-image: url(/hotels/cdn/cancellation.398c95fa.svg);
  mask-image: url(/hotels/cdn/cancellation.398c95fa.svg);
}

.payment {
  -webkit-mask-image: url(/hotels/cdn/payment.2db08cdd.svg);
  mask-image: url(/hotels/cdn/payment.2db08cdd.svg);
}

.room-value-list-icon {
  top: 0;
  left: 0;

  align-self: flex-start;
  background-color: var(--bench-text, #2d3137);
  block-size: 16px;
  content: "";
  flex-shrink: 0;
  inline-size: 16px;
  mask-position: center;
  mask-repeat: no-repeat;
  mask-size: contain;
  position: relative;

  font-size: 12px;
  font-weight: 500;
  line-height: 16px;
}

.room-value-list-point {
  align-items: center;
  display: flex;
  gap: 6px;
  position: relative;
}

.room-value-list {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  font-weight: 500;
  gap: 4px;
  line-height: 16px;

  list-style: none;
  padding: 0;
}

.room-title {
  -webkit-box-orient: vertical;
  display: -webkit-box;
  font-size: 14px;
  font-weight: 500;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  line-height: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--bench-text, #2d3137);
}

.room-beds {
  color: #868686;
  font-size: 12px;
  font-weight: 480;
  line-height: 16px;
  text-transform: lowercase;
}

.root-content-room {
  align-self: flex-start;
  inline-size: 130px;
}

.root-content {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.root {
  background-color: var(--bench-primary-light, #f4f4f4);
  border-radius: 12px;
  margin-block-end: 12px;
  margin-block-start: 8px;
  padding: 12px;
}

.hotel-card-rating-reviews {
  color: #868686;
  font-size: 12px;
  font-weight: 480;
  line-height: 16px; 
}

.hotel-card-rating-category {
  font-size: 16px;
  font-weight: 700;
  line-height: 22px;
}

.hotel-card-rating-content {
  position: absolute;
  margin-block-end: 7px;
  font-size: 16px;
  color: #FFF;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
}

.hotel-card-rating-icon {
  top: 0;
  left: 0;

  block-size: 100%;
  inline-size: 100%;
  position: absolute;

  overflow-clip-margin: content-box;
  overflow: hidden;
}

.hotel-card-total-rating {
  block-size: 48px;
  font-size: 16px;
  inline-size: 35px;

  display: flex;
  align-items: center;
  background-size: cover;
  color: #FFF;
  font-weight: 700;
  justify-content: center;
  line-height: 16px;
  padding-block-start: 4px;
  position: relative;
  text-align: center;
  text-decoration: none;
}

.hotel-card-center {
  font-size: 12px;
  line-height: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--bench-text, #2d3137);
}

.hotel-card-address {
  cursor: pointer;
  color: var(--bench-text, #2d3137);
  font-size: 12px;
  line-height: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hotel-card-distances {
  margin-block-start: 8px;

  color: #868686;
  font-size: 12px;
  font-weight: 500;
  line-height: 16px;
}

.hotel-card-stars {
  margin-block-end: 2px;
}

.hotel-card-headline {
  font-size: 16px;
  line-height: 22px;

  display: flex;
  align-items: center;
  font-weight: 700;
  position: relative;
  gap: 4px;

  color: var(--bench-text, #2d3137);
}


.card {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  display: flex;
  flex-direction: row;
  overflow: hidden;
  position: relative;
  /* min-height: 180px; */
}

.imgWrap {
  inline-size: 100%;
  margin-inline-end: 0;
  max-block-size: 100%;
  max-inline-size: 293px;
  min-block-size: 256px;

  border-radius: 12px;
  display: flex;
  flex-shrink: 0;
  margin: 4px;
  overflow: hidden;
  position: relative;
}

.img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.body {
  flex: 3;
  padding: 12px;

  display: flex;
  flex-direction: column;
  min-inline-size: 0;
  position: relative;
}

.top {
  display: flex;
  min-block-size: 70px;
  justify-content: space-between;
  gap: 12px;
}

.name {
  font-size: 16px;
  font-weight: 900;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, sans-serif;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stars {
  font-size: 12px;
  color: rgba(45, 49, 55, 0.55);
}

.addr {
  margin-top: 6px;
  font-size: 12px;
  font-weight: 700;
  color: rgba(45, 49, 55, 0.55);
  font-family: PTRootUI, sans-serif;
}

.meta {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.rate {
  display: flex;
  align-items: center;
  gap: 8px;
}

.badge {
  min-width: 34px;
  height: 28px;
  border-radius: 10px;
  background: #0e41d2;
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 900;
  font-family: PTRootUI, sans-serif;
  font-size: 12px;
}

.reviews,
.dist {
  font-size: 12px;
  font-weight: 800;
  color: rgba(45, 49, 55, 0.65);
  font-family: PTRootUI, sans-serif;
}

.bottom {
  align-items: flex-end;
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 16px;
  justify-content: flex-end;
}

.sum {
  font-size: 18px;
  font-weight: 900;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, sans-serif;
}

.small {
  font-size: 11px;
  font-weight: 800;
  color: rgba(45, 49, 55, 0.55);
  font-family: PTRootUI, sans-serif;
}

.btn {
  block-size: 40px;
  min-inline-size: 40px;
  padding: 0 12px;
  font-size: 16px;
  line-height: 20px;
  border: 1px solid #0000;
  background-color: #0e41d2;
  border-radius: 12px;
  font-weight: 500;
  justify-content: center;
  align-items: center;
  display: inline-flex;
  transition: background-color .16s ease, color .16s ease, box-shadow .16s ease;
  user-select: none;
  text-decoration: none;
  color: #FFF;
  font-family: PTRootUI, sans-serif;
  cursor: pointer;
}

@media (max-width: 760px) {
  .card {
    grid-template-columns: 1fr;
  }
  .imgWrap {
    height: 180px;
  }
}
</style>
