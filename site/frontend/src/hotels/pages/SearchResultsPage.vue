<template>
  <div class="page">
    <div class="container">
      <div class="main-content-layout">
        <div class="main-content-wrapper">

          <div class="sidebar">
            <FiltersSidebar
              v-model="filters"
              :destination="destLabel"
              :dates="datesText"
              :guestsLabel="guestsText"
              :hotels="baseHotels"
              :nights="nights"
            />
          </div>

          <div class="list">
            <!-- Переключатели типов -->
            <div class="list-categories">
              <button class="tab-btn tab-btn-active" type="button">Все</button>
              <button class="tab-btn" type="button">Отели</button>
              <button class="tab-btn" type="button">Апартаменты и квартиры</button>
            </div>

            <!-- Количество доступных вариантов -->
            <div class="available-amount" style="margin-block-end: 12px;">
              <h1 class="available-amount-text">{{ filteredHotels.length }} доступных вариантов в {{ destLabel.split(', ').shift() }}</h1>
            </div>

            <!-- Список отелей карточками -->
            <div v-if="loading" class="state">Загрузка…</div>
            <div v-else-if="error" class="state err">Ошибка: {{ error }}</div>
            <div v-else class="cards">
              <HotelCard
                v-for="h in filteredHotels"
                :key="h.id"
                :hotel="h"
                :guests="guests"
                :rooms="rooms"
                :children="children"
                :nights="nights"
              />
            </div>
          </div>

        </div>
      </div>

      <SearchMap :query="mapQuery" :markerOffsetY="180" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';

import FiltersSidebar, { type FiltersModel } from '@/hotels/components/SearchResults/FiltersSidebar.vue';
import HotelCard from '@/hotels/components/SearchResults/HotelCard.vue';
import SearchMap from '@/hotels/components/SearchResults/SearchMap.vue';

import { useSearchDataset } from '@/hotels/composable/useSearchDataset';

const route = useRoute();
const datasetId = computed(() => String(route.query.dataset ?? 'ch'));
const cityId = computed(() => String(route.query.cityId ?? ''));
const destLabel = computed(() => String(route.query.dest ?? ''));
const guests = computed(() => Number(route.query.guests ?? 2));
const rooms = computed(() => Number(route.query.rooms ?? 1));
const children = computed(() => Number(route.query.children ?? 0));

const ds = useSearchDataset(datasetId);

const city = computed(() => {
  const cities = ds.dataset.value?.cities ?? [];
  return cities.find((c) => c.id === cityId.value);
});

const cityName = computed(() => city.value?.name ?? '');
const countryName = computed(() => city.value?.countryName ?? '');

// самый надежный query для карты
const mapQuery = computed(() => {
  const d = destLabel.value?.trim();
  if (d) return d;

  const parts = [cityName.value, countryName.value].filter(Boolean);
  return parts.join(', ');
});

function formatRuShort(d: Date) {
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' })
    .format(d)
    .replace('.', '');
}

function parseISODate(v: unknown) {
  if (!v || typeof v !== 'string') return null;
  const d = new Date(v);
  return isNaN(d.getTime()) ? null : d;
}

function diffNights(a: Date, b: Date) {
  const ms = 24 * 60 * 60 * 1000;
  const a0 = new Date(a); a0.setHours(0,0,0,0);
  const b0 = new Date(b); b0.setHours(0,0,0,0);
  return Math.max(1, Math.round((b0.getTime() - a0.getTime()) / ms));
}

const checkIn = computed(() => parseISODate(route.query.checkIn));
const checkOut = computed(() => parseISODate(route.query.checkOut));

const nights = computed(() => {
  if (!checkIn.value || !checkOut.value) return 1;
  return diffNights(checkIn.value, checkOut.value);
});

const datesText = computed(() => {
  if (!checkIn.value || !checkOut.value) return '';
  return `${formatRuShort(checkIn.value)} — ${formatRuShort(checkOut.value)}`;
});

const guestsText = computed(() => {
  const r = rooms.value || 1;
  const g = guests.value || 2;

  const roomWord = r === 1 ? 'номер' : r >= 2 && r <= 4 ? 'номера' : 'номеров';
  const guestWord = g === 1 ? 'гостя' : 'гостей';

  return `${r} ${roomWord} для ${g} ${guestWord}`;
});

const loading = computed(() => ds.loading.value);
const error = computed(() => ds.error.value);

// ✅ ОБНОВЛЕНО: добавили 0 и 1 звезду + реальные чеклисты в модель
const filters = ref<FiltersModel>({
  minTotal: 0,
  maxTotal: 9999999,
  maxDistanceKm: 30,
  sort: 'popular',

  stars: { 0: true, 1: true, 2: true, 3: true, 4: true, 5: true },
  types: { hotel: true, hostel: true, apartment: true, aparthotel: true, guest_house: true, villa: true },

  reviewScoreMin: 0,

  amenitiesHotel: {},
  amenitiesRoom: {},
  placement: {},
  meals: {},
  paymentAndBooking: {},
  rooms: {},
  bedTypes: {},
});

const baseHotels = computed(() => {
  const all = ds.dataset.value?.hotels ?? [];
  return cityId.value ? all.filter((h) => h.cityId === cityId.value) : all;
});

// helpers для фильтрации чеклистов
type ChecklistState = Partial<Record<string, boolean>>;

function selectedKeys(state?: ChecklistState) {
  if (!state) return [];
  return Object.keys(state).filter((k) => !!state[k]);
}

function matchArray(arr: unknown, selected: string[], mode: 'and' | 'or') {
  if (!selected.length) return true;
  if (!Array.isArray(arr)) return false;
  return mode === 'and'
    ? selected.every((k) => arr.includes(k))
    : selected.some((k) => arr.includes(k));
}

// ✅ ОБНОВЛЕНО: теперь фильтруются ВСЕ секции (amenities/placement/meals/payment/rooms/bedTypes тоже)
const filteredHotels = computed(() => {
  const f = filters.value;
  let arr = baseHotels.value.slice();

  arr = arr.filter((h) => h.priceTotalRub >= f.minTotal && h.priceTotalRub <= f.maxTotal);
  arr = arr.filter((h) => h.distanceKm <= f.maxDistanceKm);
  arr = arr.filter((h) => !!f.stars[h.stars]);
  arr = arr.filter((h) => !!f.types[h.type]);

  const reviewMin = f.reviewScoreMin ?? 0;
  if (reviewMin > 0) arr = arr.filter((h) => h.rating >= reviewMin);

  const aHotel = selectedKeys(f.amenitiesHotel);
  const aRoom = selectedKeys(f.amenitiesRoom);
  const placement = selectedKeys(f.placement);
  const meals = selectedKeys(f.meals);
  const pay = selectedKeys(f.paymentAndBooking);
  const roomsSel = selectedKeys(f.rooms);
  const beds = selectedKeys(f.bedTypes);

  // ⚠️ h.filters может не быть в TS-типе из твоего dataset — поэтому аккуратно через any
  arr = arr.filter((h: any) => matchArray(h.filters?.amenitiesHotel, aHotel, 'and'));
  arr = arr.filter((h: any) => matchArray(h.filters?.amenitiesRoom, aRoom, 'and'));
  arr = arr.filter((h: any) => matchArray(h.filters?.placement, placement, 'and'));
  arr = arr.filter((h: any) => matchArray(h.filters?.paymentAndBooking, pay, 'and'));

  arr = arr.filter((h: any) => matchArray(h.filters?.meals, meals, 'or'));
  arr = arr.filter((h: any) => matchArray(h.filters?.bedTypes, beds, 'or'));

  if (roomsSel.length) {
    arr = arr.filter((h: any) => roomsSel.includes(String(h.filters?.rooms ?? '')));
  }

  switch (f.sort) {
    case 'priceAsc':
      arr.sort((a, b) => a.priceTotalRub - b.priceTotalRub);
      break;
    case 'priceDesc':
      arr.sort((a, b) => b.priceTotalRub - a.priceTotalRub);
      break;
    case 'ratingDesc':
      arr.sort((a, b) => b.rating - a.rating);
      break;
    default:
      arr.sort((a, b) => (b.rating * Math.log1p(b.reviews)) - (a.rating * Math.log1p(a.reviews)));
      break;
  }

  return arr;
});
</script>

<style scoped>
.available-amount-text {
  font-size: 16px;
  font-weight: 700;
  line-height: 22px;
  margin: 0;
  display: inline;
  color: var(--bench-text, #2d3137);
}

button:focus {
  outline: none;
}

.tab-btn-active::before {
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;

  border: 2px solid #0E41D2;
  border-radius: 16px;
  content: "";
  position: absolute;
}

.tab-btn-active {
  background-color: var(--bench-primary-light, #E3EBFD) !important;
  position: relative;
}

.tab-btn {
  font-size: 16px;
  line-height: 20px;
  padding: 14px 16px;

  align-items: center;
  color: var(--bench-text, #2d3137);
  cursor: pointer;
  flex: 1;
  font-weight: 500;
  text-align: center;
  border-radius: 16px;
  background: none;
  margin: 0;
  border: 0;
}

.list-categories {
  border-radius: 16px;
  background-color: var(--bench-surface-elevated, #fff);
  display: flex;
  margin-block-end: 12px;
}

.main-content-wrapper {
  display: flex;
  gap: 16px;
}

.main-content-layout {
  margin: 8px 16px 20px;
}

.page {
  display: flex;
  /* padding: 16px; */
}

.container {
  /* max-width: 1240px; */
  width: 100%;
  display: flex;
  /* margin: 0 auto; */
  /* padding: 0 20px; */
  /* box-sizing: border-box; */
}

.sidebar {
  /* position: sticky;
  top: 16px; */

  flex-shrink: 0;
  inline-size: 250px;
}

.list {
  inline-size: 800px;
  flex-grow: 1;

  display: flex;
  flex-direction: column;
}

.listHead {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 14px;
  padding: 8px 0 12px 0;
}

.h1 {
  font-size: 22px;
  font-weight: 800;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, sans-serif;
}

.sub {
  margin-top: 4px;
  font-size: 13px;
  font-weight: 600;
  color: rgba(45, 49, 55, 0.55);
  font-family: PTRootUI, sans-serif;
}

.count {
  font-size: 13px;
  font-weight: 700;
  color: rgba(45, 49, 55, 0.75);
  font-family: PTRootUI, sans-serif;
}

.cards {
  display: grid;
  gap: 12px;
}

.state {
  padding: 16px;
  border-radius: 14px;
  background: var(--bench-surface-elevated, #fff);
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.06);
  font-family: PTRootUI, sans-serif;
  font-weight: 700;
  color: rgba(45, 49, 55, 0.75);
}

.state.err {
  color: #b42318;
}

.map {
  position: sticky;
  top: 0;
  flex-grow: 1;
  /* block-size: 100vh; */
}

.mapStub {
  height: calc(100vh - 32px);
  min-height: 520px;
  border-radius: 16px;
  background: rgba(0, 0, 0, 0.05);
  display: grid;
  place-items: center;
  text-align: center;
  padding: 18px;
  box-sizing: border-box;
}

.mapTitle {
  font-size: 16px;
  font-weight: 800;
  color: rgba(45, 49, 55, 0.85);
  font-family: PTRootUI, sans-serif;
}

.mapSub {
  margin-top: 6px;
  font-size: 12px;
  font-weight: 700;
  color: rgba(45, 49, 55, 0.55);
  font-family: PTRootUI, sans-serif;
}

@media (max-width: 1100px) {
  .layout {
    grid-template-columns: 280px 1fr;
  }
  .map {
    display: none;
  }
}
</style>
