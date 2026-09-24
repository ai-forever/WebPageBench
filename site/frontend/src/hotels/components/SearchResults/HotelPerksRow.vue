<template>
  <div class="perks">
    <div class="card reviews">
      <div style="margin-block-end: 12px;">
        <HotelRatingBadge :rating="rating" :reviews="reviews" badge-first reviews-as-link />
      </div>

      <div class="body">
        <div class="authorRow">
          <div class="flag" :style="{ backgroundImage: `url(${flagUrl})` }"></div>
          <span class="author">{{ safeReviewAuthor }}</span>
        </div>

        <p class="reviewText">{{ safeReviewText }}</p>
      </div>

      <div class="footer">
        <div class="arrows">
          <button class="iconBtn" type="button" aria-label="prev">
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor" class="arrow left">
              <path
                fill-rule="nonzero"
                d="M10.908 14.623l6.139-6.14c.5-.499.5-1.315 0-1.815l-.172-.174a1.29 1.29 0 0 0-1.817 0L10 11.553l-5.06-5.06a1.288 1.288 0 0 0-1.814 0l-.173.175c-.5.5-.5 1.316 0 1.816l6.14 6.139a1.288 1.288 0 0 0 1.815 0"
              />
            </svg>
          </button>

          <button class="iconBtn disabled" type="button" aria-label="next" tabindex="-1">
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor" class="arrow right">
              <path
                fill-rule="nonzero"
                d="M10.908 14.623l6.139-6.14c.5-.499.5-1.315 0-1.815l-.172-.174a1.29 1.29 0 0 0-1.817 0L10 11.553l-5.06-5.06a1.288 1.288 0 0 0-1.814 0l-.173.175c-.5.5-.5 1.316 0 1.816l6.14 6.139a1.288 1.288 0 0 0 1.815 0"
              />
            </svg>
          </button>
        </div>

        <button class="wideBtn" type="button">
          Читать все отзывы • {{ safeReviewsButtonCount }}
        </button>
      </div>
    </div>

    <div class="card simple">
      <div class="title">Популярные удобства</div>

      <ul class="amenityList">
        <li
          v-for="(a, i) in popularAmenitiesShown"
          :key="amenityKey(a, i)"
          class="amenityItem"
          :class="amenityClass(a)"
          :title="amenityText(a)"
        >
          {{ amenityText(a) }}
        </li>
      </ul>

      <button class="wideBtn" type="button">
        Все удобства • {{ safeAmenitiesTotal }}
      </button>
    </div>

    <div class="card simple">
      <div class="title">Что есть рядом</div>

      <ul class="PoisList">
        <li
          v-for="(p, i) in poisShown"
          :key="p.name + '-' + i"
          class="PoisItem"
          :class="poiClass(p)"
        >
          <span class="PoisName">{{ p.name }}</span>
          <span class="PoisDistance">{{ p.distance }}</span>
        </li>
      </ul>

      <button class="wideBtn" type="button">
        Смотреть на карте • {{ safePoisTotal }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import HotelRatingBadge from '../../components/SearchResults/HotelRatingBadge.vue';

type PoiType = 'historical' | 'church' | 'museum' | 'nature';

type Poi = {
  name: string;
  distance: string;
  type?: PoiType;
};

type AmenityInput =
  | string
  | {
      text?: string;
      label?: string;
      name?: string;
      key?: string;
      icon?: string;
    };

const props = withDefaults(
  defineProps<{
    rating: number;
    reviews: number;

    reviewAuthor?: string;
    reviewAuthorCountry?: string;
    reviewText?: string;
    reviewsButtonCount?: number;

    popularAmenities?: AmenityInput[];
    amenitiesTotal?: number;

    pois?: Poi[];
    poisTotal?: number;
  }>(),
  {
    reviewAuthor: '',
    reviewAuthorCountry: 'RU',
    reviewText: '',
    reviewsButtonCount: 0,
    popularAmenities: () => [],
    amenitiesTotal: 0,
    pois: () => [],
    poisTotal: 0,
  },
);

const safeReviewAuthor = computed(() => props.reviewAuthor || 'Гость');
const safeReviewText = computed(() => props.reviewText || 'Отзыв пока не добавлен.');
const safeReviewsButtonCount = computed(() => props.reviewsButtonCount || props.reviews || 0);
const safeAmenitiesTotal = computed(() => props.amenitiesTotal || props.popularAmenities.length || 0);
const safePoisTotal = computed(() => props.poisTotal || props.pois.length || 0);

const popularAmenitiesShown = computed(() => (props.popularAmenities ?? []).slice(0, 5));
const poisShown = computed(() => (props.pois ?? []).slice(0, 5));

const flagUrl = computed(() => {
  const code = (props.reviewAuthorCountry || 'ru').toLowerCase();
  return `/hotels/cdn/${code}.svg`;
});

function amenityText(a: AmenityInput): string {
  if (typeof a === 'string') return a;
  return a.text || a.label || a.name || a.key || 'Удобство';
}

function amenityKey(a: AmenityInput, i: number): string {
  if (typeof a === 'string') return `${a}-${i}`;
  return `${a.key || a.icon || a.text || a.label || a.name || 'amenity'}-${i}`;
}

function normalizeAmenityKey(a: AmenityInput): string {
  if (typeof a !== 'string') {
    const explicit = (a.icon || a.key || '').trim().toLowerCase();
    if (explicit) return explicit;
  }

  const n = amenityText(a).trim().toLowerCase();

  if (n.includes('wi-fi') || n.includes('wifi') || n.includes('интернет')) return 'internet';
  if (n.includes('трансфер') || n.includes('шаттл') || n.includes('airport')) return 'shuttle';
  if (n.includes('завтрак') || n.includes('питание') || n.includes('ресторан') || n.includes('бар') || n.includes('еда')) return 'meal';
  if (n.includes('парков')) return 'parking';
  if (n.includes('живот') || n.includes('pets')) return 'pets';
  if (n.includes('огранич') || n.includes('доступ') || n.includes('инвалид')) return 'disabled_support';
  if (n.includes('кондиционер') || n.includes('air') || n.includes('климат')) return 'air_conditioning';
  if (n.includes('бассейн') || n.includes('pool')) return 'pool';
  if (n.includes('спортзал') || n.includes('фитнес') || n.includes('gym')) return 'fitness';
  if (n.includes('спа') || n.includes('spa') || n.includes('сауна')) return 'spa';
  if (n.includes('пляж')) return 'beach';
  if (n.includes('кофе')) return 'coffee';
  if (n.includes('чай')) return 'tea';
  if (n.includes('телевизор') || n.includes('tv')) return 'tv';
  if (n.includes('полотен')) return 'towels';
  if (n.includes('ванн')) return 'bath';
  if (n.includes('душ')) return 'shower';
  if (n.includes('рабоч') || n.includes('business')) return 'business_center';
  if (n.includes('лифт')) return 'elevator';

  return 'default';
}

function amenityClass(a: AmenityInput) {
  const key = normalizeAmenityKey(a);

  switch (key) {
    case 'internet':
      return 'Amenities_amenity_HAS_INTERNET__rN0LF';
    case 'shuttle':
      return 'Amenities_amenity_HAS_AIRPORT_TRANSFER__BYIGq';
    case 'meal':
      return 'Amenities_amenity_HAS_MEAL__qVBWa';
    case 'disabled_support':
      return 'Amenities_amenity_HAS_DISABLED_SUPPORT__nt5ol';
    case 'pets':
      return 'Amenities_amenity_HAS_PETS__GVn0g';
    case 'parking':
      return 'Amenities_amenity_HAS_PARKING__local';
    case 'air_conditioning':
      return 'Amenities_amenity_HAS_AIR_CONDITIONING__local';
    case 'pool':
      return 'Amenities_amenity_HAS_POOL__local';
    case 'fitness':
      return 'Amenities_amenity_HAS_FITNESS__local';
    case 'spa':
      return 'Amenities_amenity_HAS_SPA__local';
    case 'beach':
      return 'Amenities_amenity_HAS_BEACH__local';
    case 'coffee':
      return 'Amenities_amenity_HAS_COFFEE__local';
    case 'tea':
      return 'Amenities_amenity_HAS_TEA__local';
    case 'tv':
      return 'Amenities_amenity_HAS_TV__local';
    case 'towels':
      return 'Amenities_amenity_HAS_TOWELS__local';
    case 'bath':
      return 'Amenities_amenity_HAS_BATH__local';
    case 'shower':
      return 'Amenities_amenity_HAS_SHOWER__local';
    case 'business_center':
      return 'Amenities_amenity_HAS_BUSINESS_CENTER__local';
    case 'elevator':
      return 'Amenities_amenity_HAS_ELEVATOR__local';
    default:
      return '';
  }
}

function poiClass(p: Poi) {
  const t = p.type ?? inferPoiType(p.name);

  switch (t) {
    case 'church':
      return 'Pois_poi_CHURCH__rtBlu';
    case 'museum':
      return 'Pois_poi_MUSEUM__bbwlF';
    case 'nature':
      return 'Pois_poi_NATURE__park';
    default:
      return 'Pois_poi_HISTORICAL_POI__d9O9B';
  }
}

function inferPoiType(name: string): PoiType {
  const n = name.toLowerCase();
  if (n.includes('церков') || n.includes('собор') || n.includes('катедрал')) return 'church';
  if (n.includes('музей')) return 'museum';
  if (n.includes('парк') || n.includes('сад') || n.includes('природ')) return 'nature';
  return 'historical';
}
</script>

<style scoped>
.perks {
  display: flex;
  gap: 8px;
  inline-size: 100%;
  max-inline-size: 100%;
}

.card {
  background-color: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 16px;
  inline-size: 100%;
  max-inline-size: 100%;
  min-inline-size: 0;
}

.reviews {
  block-size: 274px;
  flex-shrink: 1;
  inline-size: 100%;
  max-inline-size: 100%;
  justify-content: space-between;
}

.simple {
  block-size: 274px;
  inline-size: 280px;
  min-inline-size: 280px;
}

.body {
  overflow: hidden;
  align-items: flex-start;
  display: flex;
  inline-size: 100%;
  justify-content: space-between;
  max-inline-size: 100%;
  position: relative;
  flex-direction: column;
}

.authorRow {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.flag {
  background-repeat: no-repeat;
  background-size: contain;
  block-size: 12px;
  border-radius: 2px;
  flex-shrink: 0;
  inline-size: 18px;
}

.author {
  font-size: 14px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.reviewText {
  font-size: 14px;
  font-weight: 480;
  line-height: 20px;
  word-break: break-word;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.footer {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: auto;
}

.arrows {
  display: flex;
  gap: 4px;
}

.iconBtn {
  width: 32px;
  height: 32px;
  border-radius: 12px;
  border: 1px solid #0000;
  display: grid;
  place-items: center;
  cursor: pointer;
  color: var(--bench-primary, #0e41d2);
  background: var(--bench-primary-light, rgb(237, 242, 252));
}

.iconBtn.disabled {
  opacity: 0.35;
  cursor: default;
}

.arrow.left {
  transform: rotate(90deg);
}

.arrow.right {
  transform: rotate(-90deg);
}

.wideBtn {
  inline-size: 100%;
  flex: 1;
  min-block-size: 36px;
  block-size: 36px;
  max-block-size: 36px;
  padding: 0 8px;
  min-inline-size: 36px;
  border-radius: 12px;
  border: 1px solid #0000;
  background: var(--bench-primary-light, rgb(237, 242, 252));
  color: var(--bench-primary, #0e41d2);
  font-weight: 500;
  font-size: 16px;
  line-height: 20px;
  font-family: PTRootUI, Verdana, sans-serif;
  cursor: pointer;
}

.title {
  font-size: 16px;
  font-weight: 700;
  line-height: 22px;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.amenityList {
  block-size: 100%;
  box-sizing: border-box;
  column-gap: 20px;
  columns: 160px 2;
  list-style: none;
  padding: 12px 0;
  margin: 0;
}

.amenityItem {
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  overflow: hidden;
  padding-block-end: 6px;
  padding-block-start: 6px;
  padding-inline-start: 28px;
  position: relative;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: PTRootUI, Verdana, sans-serif;
  color: var(--bench-text, #2d3137);
}

.amenityItem::before {
  background-image: url(/hotels/cdn/default-dark.0cf44b86_d10b0eba_1.svg);
  background-position: 50%;
  background-repeat: no-repeat;
  background-size: contain;
  block-size: 100%;
  inline-size: 20px;
  content: "";
  position: absolute;
  top: 0;
  left: 0;
}

.Amenities_amenity_HAS_INTERNET__rN0LF::before {
  background-image: url(/hotels/cdn/internet.b8e3abca_a0e44ed8_1.svg);
}

.Amenities_amenity_HAS_AIRPORT_TRANSFER__BYIGq::before {
  background-image: url(/hotels/cdn/shuttle.3f845299_44c0baa1_1.svg);
}

.Amenities_amenity_HAS_MEAL__qVBWa::before {
  background-image: url(/hotels/cdn/meal.27c89335_accf8c11_1.svg);
}

.Amenities_amenity_HAS_DISABLED_SUPPORT__nt5ol::before {
  background-image: url(/hotels/cdn/disabled-support.cc65e41d_e96118b7_1.svg);
}

.Amenities_amenity_HAS_PETS__GVn0g::before {
  background-image: url(/hotels/cdn/pets.383546b8_b7a376b9_1.svg);
}

.Amenities_amenity_HAS_PARKING__local::before {
  background-image: url(/hotels/cdn/parking.43614c6c.svg);
}

.Amenities_amenity_HAS_AIR_CONDITIONING__local::before {
  background-image: url(/hotels/cdn/air-conditioning.ce1a9abe.svg);
}

.Amenities_amenity_HAS_POOL__local::before {
  background-image: url(/hotels/cdn/pool.svg);
}

.Amenities_amenity_HAS_FITNESS__local::before {
  background-image: url(/hotels/cdn/fitness.svg);
}

.Amenities_amenity_HAS_SPA__local::before {
  background-image: url(/hotels/cdn/spa.svg);
}

.Amenities_amenity_HAS_BEACH__local::before {
  background-image: url(/hotels/cdn/beach.svg);
}

.Amenities_amenity_HAS_COFFEE__local::before {
  background-image: url(/hotels/cdn/coffee.svg);
}

.Amenities_amenity_HAS_TEA__local::before {
  background-image: url(/hotels/cdn/tea.fde63893.svg);
}

.Amenities_amenity_HAS_TV__local::before {
  background-image: url(/hotels/cdn/tv.3c977110.svg);
}

.Amenities_amenity_HAS_TOWELS__local::before {
  background-image: url(/hotels/cdn/towels.svg);
}

.Amenities_amenity_HAS_BATH__local::before {
  background-image: url(/hotels/cdn/bath.c1d4458d.svg);
}

.Amenities_amenity_HAS_SHOWER__local::before {
  background-image: url(/hotels/cdn/shower.svg);
}

.Amenities_amenity_HAS_BUSINESS_CENTER__local::before {
  background-image: url(/hotels/cdn/business-center.31f9d0b6.svg);
}

.Amenities_amenity_HAS_ELEVATOR__local::before {
  background-image: url(/hotels/cdn/elevator.svg);
}

.PoisList {
  list-style: none;
  padding: 12px 0;
  margin: 0;
}

.PoisItem {
  display: flex;
  font-size: 14px;
  font-weight: 500;
  justify-content: space-between;
  line-height: 20px;
  max-inline-size: 100%;
  padding-block-end: 4px;
  padding-block-start: 4px;
  padding-inline-start: 28px;
  position: relative;
  font-family: PTRootUI, Verdana, sans-serif;
}

.PoisItem::before {
  background-image: url(/hotels/cdn/default-dark.0cf44b86_d10b0eba_1.svg);
  background-position: 50%;
  background-repeat: no-repeat;
  background-size: contain;
  block-size: 100%;
  inline-size: 20px;
  content: "";
  position: absolute;
  border-radius: 50%;
  top: 0;
  left: 0;
}

.Pois_poi_HISTORICAL_POI__d9O9B::before {
  background-image: url(/hotels/cdn/historical-places-of-interest.d2fd1030.svg);
}

.Pois_poi_CHURCH__rtBlu::before {
  background-image: url(/hotels/cdn/churches-and-cathedrals.21384bf7.svg);
}

.Pois_poi_MUSEUM__bbwlF::before {
  background-image: url(/hotels/cdn/museums.f2922b1d.svg);
}

.Pois_poi_NATURE__park::before {
  background-image: url(/hotels/cdn/nature-and-parks.8a4d71d7.svg);
}

.PoisName {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-inline-end: 10px;
  color: var(--bench-text, #2d3137);
}

.PoisDistance {
  flex-shrink: 0;
  padding: 2px 7px;
  border-radius: 100px;
  background: var(--bench-primary-light, #f4f4f4);
  color: var(--bench-text-muted, rgba(45, 49, 55, 0.75));
  font-size: 14px;
  margin-inline-start: 4px;
  white-space: nowrap;
  line-height: 20px;
  font-weight: 500;
  font-family: PTRootUI, Verdana, sans-serif;
}

@media (max-width: 1020px) {
  .perks {
    flex-direction: column;
  }

  .reviews,
  .simple {
    block-size: auto;
    inline-size: 100%;
    min-inline-size: 0;
  }
}
</style>