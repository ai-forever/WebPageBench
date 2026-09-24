<template>
  <div class="page">
    <div class="container">
      <div class="header">
        <div class="breadcrumbs">
          <button class="crumbLink" type="button" @click="goBack">
            Все варианты в {{ cityTitle || 'городе' }}
          </button>
          <button class="crumbNewSearch" type="button" @click="goBack">
            Новый поиск
          </button>
        </div>
      </div>

      <div v-if="loading" class="state">Загрузка…</div>
      <div v-else-if="error" class="state err">Ошибка: {{ error }}</div>

      <template v-else>
        <div v-if="!hotel" class="state err">Отель не найден</div>

        <template v-else>
          <div class="head">
            <div class="headLeft">
              <div>
                <div style="margin-block-end: 2px;">
                  <HotelStars :stars="hotel.stars" :size="10" />
                </div>

                <h1 class="title">{{ hotel.name }}</h1>
              </div>

              <div>
                <div class="addressContainer">
                  <span class="addr">{{ hotel.address }}</span>
                  <button class="mapLink" type="button" @click="scrollToMap">
                    Показать на карте
                  </button>
                </div>

                <div class="distanceContainer">
                  {{ distanceText }}
                </div>
              </div>
            </div>

            <div class="headRight">
              <p class="priceTag">от {{ rubleCurrency(hotel.priceTotalRub) }}</p>

              <div class="priceContent">
                <button class="hotelHeartBtn" type="button">
                  <svg xmlns="http://www.w3.org/2000/svg" width="22" height="19" fill="none" viewBox="0 0 22 19">
                    <path fill="#868686" d="M10.952 1.547c2.631-2.01 6.427-2.16 9.018.383 1.075 1.054 1.722 2.465 1.943 3.92a7.603 7.603 0 01-.046 2.557A2.488 2.488 0 0020.5 8H20v-.5c0-.066-.003-.132-.008-.197.02-.382.002-.769-.056-1.152-.166-1.086-.641-2.082-1.366-2.794-1.937-1.899-4.955-1.7-6.917.224a1 1 0 01-1.4 0c-1.951-1.914-4.972-2.097-6.9-.207-.886.87-1.36 2.187-1.353 3.575.006 1.389.493 2.73 1.368 3.625 1.695 1.734 5.26 4.398 7.18 5.833l.44.329c.163-.13.348-.273.557-.436.505-.395 1.156-.904 2.022-1.585l.433-.343v.128c0 .712.297 1.354.775 1.81-.875.688-1.52 1.191-2.015 1.578-.502.392-.852.665-1.134.892a1 1 0 01-1.24.009 72.766 72.766 0 00-.915-.688c-1.868-1.394-5.706-4.259-7.533-6.13-1.3-1.33-1.93-3.2-1.938-5.013-.008-1.813.606-3.69 1.953-5.011 2.575-2.526 6.37-2.405 9-.4z"></path>
                    <path fill="#868686" d="M20.5 10a.5.5 0 01.5.5v1a.5.5 0 01-.5.5H18v2.5a.5.5 0 01-.5.5h-1a.502.502 0 01-.5-.5V12h-2.5a.5.5 0 01-.5-.5v-1a.5.5 0 01.5-.5H16V7.5a.5.5 0 01.5-.5h1a.5.5 0 01.5.5V10h2.5z"></path>
                  </svg>
                </button>

                <button class="checkPricesBtn" type="button">
                  <div class="checkPricesBtnText">Посмотреть цены</div>
                </button>
              </div>
            </div>
          </div>

          <HotelGallery :images="galleryImages" />

          <HotelPerksRow
            :rating="hotel.rating"
            :reviews="hotel.reviews"
            :review-author="featuredReview?.author"
            :review-author-country="featuredReview?.countryCode"
            :review-text="featuredReview?.text"
            :reviews-button-count="reviewsButtonCount"
            :popular-amenities="popularAmenities"
            :amenities-total="amenitiesTotal"
            :pois="nearPois"
            :pois-total="poisTotal"
          />

          <SearchDatesCard
            :from-url="true"
            :check-in-time="checkInTime"
            :check-out-time="checkOutTime"
            @change="openChangeDates()"
          />

          <HotelRoomOptions :hotel="hotel" />
          <HotelGeoBlock :hotel="hotel" />
          <HotelAboutBlock :hotel="hotel" />
          <AmenitiesBlock :hotel="hotel" />
          <HotelAccommodationRulesBlock :hotel="hotel" />
          <HotelAdditionalInfoBlock :hotel="hotel" />
          <HotelPaymentBlock :hotel="hotel" />
          <HotelReviewsBlock :hotel="hotel" />
        </template>
      </template>
    </div>

    <div ref="mapAnchor"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { useSearchDataset } from '../composable/useSearchDataset';
import type { Hotel } from '../services/searchDataset';

import HotelStars from '../components/SearchResults/HotelStars.vue';
import HotelPerksRow from '../components/SearchResults/HotelPerksRow.vue';
import HotelRoomOptions from '../components/SearchResults/HotelRoomOptions.vue';
import HotelGeoBlock from '../components/SearchResults/HotelGeoBlock.vue';
import HotelAboutBlock from '../components/SearchResults/HotelAboutBlock.vue';
import HotelAdditionalInfoBlock from '../components/SearchResults/HotelAdditionalInfoBlock.vue';
import HotelAccommodationRulesBlock from '../components/SearchResults/HotelAccommodationRulesBlock.vue';
import HotelPaymentBlock from '../components/SearchResults/HotelPaymentBlock.vue';
import AmenitiesBlock from '../components/SearchResults/AmenitiesBlock.vue';
import HotelReviewsBlock from '../components/SearchResults/HotelReviewsBlock.vue';

import HotelGallery from '../components/HotelDetails/HotelGallery.vue';
import SearchDatesCard from '../components/SearchResults/SearchDatesCard.vue';

import { rubleCurrency } from '../utils/rubleCurrency';
import { pushBenchRoute } from '@/common/benchNavigation';

type PoiType = 'historical' | 'church' | 'museum' | 'nature';
type PoiItem = { name: string; distance: string; type?: PoiType };

const route = useRoute();
const router = useRouter();

const datasetId = computed(() => String(route.query.dataset ?? 'ch'));
const hotelId = computed(() => String(route.query.hotelId ?? ''));

function parseLocalISODate(v: unknown): Date | null {
  if (!v || typeof v !== 'string') return null;
  const m = v.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return null;

  const y = Number(m[1]);
  const mo = Number(m[2]) - 1;
  const d = Number(m[3]);

  const dt = new Date(y, mo, d);
  return Number.isNaN(dt.getTime()) ? null : dt;
}

const checkIn = computed(() => parseLocalISODate(route.query.checkIn));
const checkOut = computed(() => parseLocalISODate(route.query.checkOut));

const ds = useSearchDataset(datasetId);
const loading = computed(() => ds.loading.value);
const error = computed(() => ds.error.value);

const hotel = computed<Hotel | null>(() => {
  const all = ds.dataset.value?.hotels ?? [];
  const id = hotelId.value;
  if (!id) return null;
  return all.find((h: any) => h.id === id) ?? null;
});

const hotelExt = computed<any>(() => hotel.value as any);

const cityTitle = computed(() => {
  const d = ds.dataset.value;
  if (!d || !hotel.value) return '';
  const c = d.cities.find((x: any) => x.id === hotel.value!.cityId);
  return c?.name ?? '';
});

const poiItems = computed(() => {
  const groups = hotelExt.value?.geoBlock?.poiGroups ?? [];
  const nearby = groups.find((g: any) => g.id === 'nearby');
  if (nearby?.items?.length) return nearby.items;

  const firstNonEmpty = groups.find((g: any) => Array.isArray(g.items) && g.items.length);
  return firstNonEmpty?.items ?? [];
});

const nearPois = computed<PoiItem[]>(() => {
  return poiItems.value.slice(0, 5).map((item: any) => ({
    name: item.name,
    distance: item.distance,
    type: mapPoiType(item.type),
  }));
});

const poisTotal = computed<number>(() => poiItems.value.length);

const amenitiesGroups = computed(() => {
  return hotelExt.value?.amenitiesBlock?.groups ?? [];
});

const popularAmenities = computed<string[]>(() => {
  const popularGroup = amenitiesGroups.value.find((g: any) => g.id === 'popular');
  if (popularGroup?.items?.length) {
    return popularGroup.items.slice(0, 5);
  }

  const fallbackMap: Record<string, string> = {
    wifi: 'Бесплатный интернет',
    breakfast: 'Завтрак',
    parking: 'Парковка',
    pets: 'Разрешено с домашними животными',
    accessible: 'Для гостей с ограниченными возможностями',
    airConditioning: 'Кондиционер',
  };

  const hotelAmenities = hotel.value?.amenities ?? [];
  return hotelAmenities.slice(0, 5).map((a: string) => fallbackMap[a] ?? a);
});

const amenitiesTotal = computed<number>(() => {
  if (amenitiesGroups.value.length) {
    return amenitiesGroups.value.reduce((sum: number, g: any) => {
      return sum + (Array.isArray(g.items) ? g.items.length : 0);
    }, 0);
  }

  return hotel.value?.amenities?.length ?? 0;
});

const reviewsList = computed(() => {
  return hotelExt.value?.reviewsBlock?.reviews ?? [];
});

const featuredReview = computed<any | null>(() => {
  const featured = hotelExt.value?.reviewsBlock?.featuredReviews ?? [];
  if (featured.length) return featured[0];
  if (reviewsList.value.length) return reviewsList.value[0];
  return null;
});

const reviewsButtonCount = computed<number>(() => {
  return (
    hotelExt.value?.reviewsBlock?.ratingSummary?.totalReviews ??
    hotelExt.value?.reviewsBlock?.total ??
    hotel.value?.reviews ??
    reviewsList.value.length ??
    0
  );
});

const checkInTime = computed<string>(() => {
  const raw =
    hotelExt.value?.accommodationBlock?.checkInOut?.checkIn?.value ??
    hotelExt.value?.accommodationBlock?.checkInTime ??
    'После 14:00';

  return extractTime(raw, '14:00');
});

const checkOutTime = computed<string>(() => {
  const raw =
    hotelExt.value?.accommodationBlock?.checkInOut?.checkOut?.value ??
    hotelExt.value?.accommodationBlock?.checkOutTime ??
    'До 11:00';

  return extractTime(raw, '11:00');
});

const distanceText = computed(() => {
  if (hotelExt.value?.distanceFromCenter) return hotelExt.value.distanceFromCenter;

  const distance = hotel.value?.distanceKm;
  if (typeof distance !== 'number') return 'Расстояние до центра не указано';
  return `${distance.toFixed(1)} км от центра`;
});

function extractTime(raw: string, fallback: string) {
  const m = String(raw).match(/(\d{1,2}:\d{2})/);
  return m ? m[1] : fallback;
}

function mapPoiType(type?: string): PoiType {
  switch (type) {
    case 'CHURCH':
      return 'church';
    case 'MUSEUM':
      return 'museum';
    case 'PARK':
    case 'NATURE':
    case 'NATURE_AND_PARKS':
      return 'nature';
    default:
      return 'historical';
  }
}

function openChangeDates() {
  console.log('change dates');
}

const galleryImages = computed(() => {
  const fromImages = Array.isArray(hotel.value?.images) ? hotel.value!.images : [];
  const fromCover = hotel.value?.imageUrl ? [hotel.value!.imageUrl] : [];
  const combined = [...fromImages, ...fromCover];

  const cleaned = combined
    .map((s) => (typeof s === 'string' ? s.trim() : ''))
    .filter((s) => !!s);

  const unique = Array.from(new Set(cleaned));
  if (!unique.length) return ['/hotels/cdn/island.png'];
  return unique.slice(0, 10);
});

function goBack() {
  const q = { ...route.query };
  delete (q as any).hotelId;

  pushBenchRoute(router, {
    name: 'bench_hotel_search',
    stateId: 'state_hotels_search',
    trackId: route.params.track_id,
    query: q,
  });
}

const mapAnchor = ref<HTMLElement | null>(null);

function scrollToMap() {
  mapAnchor.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
</script>

<style scoped>
.perks {
  display: flex;
  gap: 8px;
  inline-size: 100%;
  max-inline-size: 100%;
}

.reviews {
  block-size: 274px;
  flex-shrink: 1;
  inline-size: 100%;
  max-inline-size: 100%;
  background-color: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 16px;
}

.reviewsHeader {
  block-size: 48px;
  box-sizing: border-box;
  display: flex;
  gap: 8px;
  justify-content: space-between;
  margin-block-end: 12px;
  overflow: hidden;
  position: relative;
}

.reviewsBody {
  align-items: center;
  display: flex;
  inline-size: 100%;
  justify-content: space-between;
  max-inline-size: 100%;
  position: relative;
}

.reviewsFooter {
  align-items: center;
  display: flex;
  gap: 8px;
  margin-block-start: auto;
}

.page {
  background: var(--bench-surface, #f4f4f4);
  min-height: 100vh;
}

.container {
  max-width: 1085px;
  margin: 0 auto;
  font-family: PTRootUI, Verdana, sans-serif;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 20px;
}

.header {
  display: flex;
  flex-direction: column;
  max-inline-size: 1400px;
  padding-top: 12px;
}

.breadcrumbs {
  display: flex;
  gap: 8px;
}

.crumbLink,
.crumbNewSearch {
  border: 0;
  background: none;
  padding: 8px 12px;
  line-height: 18px;
  gap: 4px;
  cursor: pointer;
  color: var(--bench-text, #2d3137);
  font-weight: 500;
  font-size: 16px;
  display: flex;
  border-radius: 12px;
  background-color: var(--bench-surface-elevated, #fff);
  align-items: center;
  font-family: PTRootUI, Verdana, sans-serif;
}

.crumbLink::before {
  background-image: url(/hotels/cdn/arrow.3425ad31.svg);
  background-position: 50%;
  background-repeat: no-repeat;
  background-size: contain;
  block-size: 18px;
  content: "";
  inline-size: 18px;
  color: var(--bench-text, #2d3137);
}

.crumbNewSearch::before {
  background-image: url(/hotels/cdn/search.9af92a6c.svg);
  background-position: 50%;
  background-repeat: no-repeat;
  background-size: contain;
  block-size: 18px;
  content: "";
  inline-size: 18px;
}

.crumbSep {
  opacity: 0.6;
}

.crumbNow {
  color: rgba(45, 49, 55, 0.75);
}

.state {
  padding: 16px;
  border-radius: 16px;
  background: var(--bench-surface-elevated, #fff);
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.06);
  font-size: 14px;
  font-weight: 600;
  color: rgba(45, 49, 55, 0.75);
}

.state.err {
  color: #b42318;
}

.head {
  align-items: center;
  background-color: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  padding-block-end: 12px;
  padding-block-start: 12px;
  padding-inline-end: 20px;
  padding-inline-start: 16px;
}

.headLeft {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.headRight {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  inline-size: max-content;
  justify-content: flex-start;
  margin-inline-start: auto;
}

.priceTag {
  font-size: 20px;
  font-weight: 600;
  line-height: 25px;
  margin-block-end: 6px;
  margin-block-start: 4px;
  margin-inline-end: 0;
  margin-inline-start: auto;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.priceContent {
  display: flex;
  gap: 12px;
  inline-size: 100%;
  justify-content: flex-end;
}

.hotelHeartBtn {
  align-items: center;
  background: none;
  block-size: 40px;
  border: none;
  border-radius: 12px;
  color: #868686;
  cursor: pointer;
  display: flex;
  flex-shrink: 0;
  inline-size: 40px;
  justify-content: center;
  position: relative;
  transition: transform 0.2s, color 0.2s;
  background-color: var(--bench-primary-light, #f4f4f4);
}

.checkPricesBtn {
  block-size: 40px;
  min-inline-size: 40px;
  padding: 0 12px;
  font-size: 16px;
  line-height: 20px;
  align-items: center;
  background-color: #0e41d2;
  border: 1px solid #0000;
  border-radius: 12px;
  color: #fff;
  display: inline-flex;
  font-weight: 500;
  justify-content: center;
  position: relative;
  font-family: PTRootUI, Verdana, sans-serif;
  transition: background-color 0.16s ease, color 0.16s ease, box-shadow 0.16s ease;
}

.checkPricesBtnText {
  font-family: PTRootUI, Verdana, sans-serif;
  font-weight: 500;
  color: #fff;
  font-size: 16px;
  padding: 0 4px;
}

.title {
  font-size: 20px;
  font-weight: 700;
  line-height: 24px;
  margin: 0;
  vertical-align: middle;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.addressContainer {
  display: flex;
}

.distanceContainer {
  color: #868686;
  display: flex;
  flex-wrap: wrap;
  font-size: 12px;
  font-weight: 480;
  overflow: hidden;
  overflow: clip;
  font-family: PTRootUI, Verdana, sans-serif;
}

.subRow {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(45, 49, 55, 0.75);
  font-size: 13px;
  font-weight: 500;
}

.addr {
  font-size: 12px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.dot {
  opacity: 0.6;
}

.mapLink {
  border: 0;
  background: none;
  padding: 0;
  cursor: pointer;
  position: relative;
  color: #0e41d2;
  font-weight: 700;
  font-size: 12px;
  margin-inline-start: 18px;
  font-family: PTRootUI, Verdana, sans-serif;
}

.mapLink::before {
  left: -12px;
  color: #868686;
  content: "•";
  position: absolute;
  font-size: 12px;
  font-weight: 700;
  font-family: PTRootUI, Verdana, sans-serif;
}

.metaRow {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: rgba(45, 49, 55, 0.65);
  font-weight: 500;
}

.layout {
  margin-top: 12px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 16px;
  align-items: start;
}

.card {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.06);
  padding: 14px;
}

.cardTitle {
  font-size: 16px;
  line-height: 22px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
}

.cardSub {
  margin-top: 4px;
  font-size: 12px;
  line-height: 16px;
  color: rgba(45, 49, 55, 0.65);
  font-weight: 500;
}

.offers {
  margin-top: 12px;
  display: grid;
  gap: 12px;
}

.amenitiesRow {
  margin-top: 10px;
}

.text {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 18px;
  color: rgba(45, 49, 55, 0.75);
}

.aside {
  position: sticky;
  top: 12px;
}

.bookCard {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.06);
  padding: 14px;
}

.bookTitle {
  font-size: 16px;
  line-height: 22px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
  margin-bottom: 10px;
}

.bookLine {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 8px;
}

.bookLabel {
  font-size: 12px;
  color: rgba(45, 49, 55, 0.65);
  font-weight: 600;
}

.bookValue {
  font-size: 12px;
  color: var(--bench-text, #2d3137);
  font-weight: 600;
  text-align: right;
}

.bookHr {
  height: 1px;
  background: rgba(45, 49, 55, 0.1);
  margin: 12px 0;
}

.bookPriceRow {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

.bookPriceLabel {
  font-size: 12px;
  color: rgba(45, 49, 55, 0.65);
  font-weight: 700;
}

.bookPrice {
  font-size: 18px;
  font-weight: 800;
  color: var(--bench-text, #2d3137);
}

.bookHint {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(45, 49, 55, 0.55);
  font-weight: 600;
  text-align: right;
}

.bookBtn {
  margin-top: 12px;
  width: 100%;
  height: 44px;
  border-radius: 12px;
  border: 0;
  background: #0e41d2;
  color: #fff;
  cursor: pointer;
  font-family: PTRootUI, Verdana, sans-serif;
  font-weight: 600;
  font-size: 15px;
}

.bookNote {
  margin-top: 10px;
  font-size: 12px;
  line-height: 16px;
  color: rgba(45, 49, 55, 0.55);
  font-weight: 500;
}

.mapStub {
  margin-top: 10px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.04);
  padding: 14px;
  font-size: 13px;
  color: rgba(45, 49, 55, 0.7);
}

@media (max-width: 1020px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .aside {
    position: static;
  }

  .addr {
    max-width: 100%;
  }
}
</style>