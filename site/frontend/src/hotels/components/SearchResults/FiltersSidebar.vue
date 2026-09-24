<!-- FiltersSidebar.vue -->
<template>
  <div class="sidebar">
    <!-- SEARCH SUMMARY CARD (top) -->
    <div class="searchCard">
      <div class="searchTextBox">
        <p class="searchDestination">{{ destinationText }}</p>
        <div>
          <p class="searchText">{{ datesText }}</p>
          <p class="searchText">{{ guestsText }}</p>
        </div>

        <svg class="searchIcon" width="22" height="22" viewBox="0 0 24 24" fill="none">
          <path
            d="M10.5 18.5c4.418 0 8-3.582 8-8s-3.582-8-8-8-8 3.582-8 8 3.582 8 8 8Z"
            stroke="#0E41D2"
            stroke-width="2"
          />
          <path d="M21 21l-4.35-4.35" stroke="#0E41D2" stroke-width="2" stroke-linecap="round" />
        </svg>
      </div>
    </div>

    <!-- FILTERS -->
    <div class="card">
      <div class="filtersContainer">
        <!-- Favorites -->
        <div class="favoritesRow">
          <div class="favLeft">
            <span class="heartIcon"></span>
            <div class="favTitle">Избранное</div>
          </div>

          <label class="switch">
            <input type="checkbox" v-model="favOnly" />
            <span class="slider"></span>
          </label>
        </div>

        <!-- 1) Sort -->
        <div class="section">
          <div class="sectionTitle">Сортировка</div>
          <div class="selectWrap">
            <select class="select" :value="m.sort" @change="onSort($event)">
              <option value="popular">По популярности</option>
              <option value="priceAsc">Цена: по возрастанию</option>
              <option value="priceDesc">Цена: по убыванию</option>
              <option value="ratingDesc">Рейтинг</option>
            </select>

            <span class="selectChevron">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="#868686">
                <path
                  fill-rule="nonzero"
                  d="M10.908 14.623l6.139-6.14c.5-.499.5-1.315 0-1.815l-.172-.174a1.29 1.29 0 0 0-1.817 0L10 11.553l-5.06-5.06a1.288 1.288 0 0 0-1.814 0l-.173.175c-.5.5-.5 1.316 0 1.816l6.14 6.139a1.288 1.288 0 0 0 1.815 0"
                />
              </svg>
            </span>
          </div>
        </div>

        <!-- 2) Price -->
        <div class="section">
          <div class="sectionTitle">Цена</div>

          <div class="segmented">
            <button class="segBtn" :class="{ active: priceMode === 'night' }" @click="priceMode = 'night'" type="button">
              за ночь
            </button>
            <button class="segBtn" :class="{ active: priceMode === 'total' }" @click="priceMode = 'total'" type="button">
              за все время
            </button>
          </div>

          <div class="priceBox">
            <div class="priceCell">
              <input class="priceInput" type="number" :value="priceUi.min" @input="onPriceInput('min', $event)" />
              <span class="priceSuffix">₽</span>
            </div>

            <div class="priceDivider"></div>

            <div class="priceCell">
              <input class="priceInput" type="number" :value="priceUi.max" @input="onPriceInput('max', $event)" />
              <span class="priceSuffix">₽</span>
            </div>
          </div>

          <div class="priceSlider">
            <DoubleRange
              v-model="priceUi"
              :min="0"
              :max="priceUiMax"
              :step="priceUiStep"
            />
          </div>
        </div>

        <!-- 3) Type -->
        <section class="section">
          <div class="sectionTitle">Тип жилья</div>

          <div class="list">
            <div v-for="it in typeItemsWithCounts" :key="it.key" class="row">
              <label class="rowLeft">
                <input
                  class="chk"
                  type="checkbox"
                  :checked="isTypeChecked(it.key)"
                  @change="toggleType(it.key, $event)"
                />
                <span class="rowText">
                  <span class="labelText">{{ it.label }}</span>
                </span>
              </label>

              <div v-if="typeof it.count === 'number'" class="count">{{ it.count }}</div>
            </div>
          </div>
        </section>

        <!-- 4) Distance -->
        <div class="section">
          <div class="sectionTitle">Расстояние от центра</div>

          <input class="distanceInp" type="text" :value="`${m.maxDistanceKm} км`" readonly />

          <div class="distanceSlider">
            <input
              class="singleRange"
              type="range"
              min="1"
              max="30"
              step="1"
              :value="m.maxDistanceKm"
              @input="onDistance($event)"
            />
          </div>
        </div>

        <!-- 5) Amenities (hotel) -->
        <FilterChecklistSection
          title="Услуги и удобства"
          subtitle="В отеле"
          :items="amenitiesHotelItemsWithCounts"
          v-model="amenitiesHotelState"
        />

        <!-- 6) Amenities (room) -->
        <FilterChecklistSection
          subtitle="В номере"
          :items="amenitiesRoomItemsWithCounts"
          v-model="amenitiesRoomState"
        />

        <!-- 7) Placement -->
        <FilterChecklistSection
          title="Особенности размещения"
          :items="placementItemsWithCounts"
          v-model="placementState"
        />

        <!-- 8) Meals -->
        <FilterChecklistSection
          title="Питание"
          :items="mealsItemsWithCounts"
          v-model="mealsState"
        />

        <!-- 9) Stars -->
        <section class="section">
          <div class="sectionTitle">Звёзды</div>

          <div class="list">
            <div v-for="s in starsRows" :key="s.key" class="row">
              <label class="rowLeft">
                <input
                  class="chk"
                  type="checkbox"
                  :checked="isStarsRowChecked(s.key)"
                  @change="toggleStarsRow(s.key, $event)"
                />
                <span class="rowText">
                  <span class="starsWrap">
                    <template v-if="s.key !== 'oneOrZero'">
                      <span v-for="n in Number(s.key)" :key="n" class="star">★</span>
                    </template>
                    <template v-else>
                      <span class="star">★</span>
                      <span class="labelText">&nbsp;или без звёзд</span>
                    </template>
                  </span>
                </span>
              </label>

              <div v-if="typeof s.count === 'number'" class="count">{{ s.count }}</div>
            </div>
          </div>
        </section>

        <!-- 10) Review rating (radio) -->
        <section class="section">
          <div class="sectionTitle">Оценка по отзывам</div>

          <div class="radioList">
            <label v-for="opt in reviewScoreOptionsWithCounts" :key="opt.value" class="radioRow">
              <input
                class="radioInp"
                type="radio"
                name="reviewScore"
                :value="opt.value"
                :checked="reviewScore === opt.value"
                @change="setReviewScore(opt.value)"
              />
              <span class="radioUi"></span>
              <span class="radioLabel">{{ opt.label }}</span>
              <span v-if="typeof opt.count === 'number' && opt.value !== 'any'" class="radioCount">{{ opt.count }}</span>
            </label>
          </div>
        </section>

        <!-- 11) Payment & booking -->
        <FilterChecklistSection
          title="Оплата и бронирование"
          :items="paymentAndBookingItemsWithCounts"
          v-model="paymentBookingState"
        />

        <!-- 12) Number of rooms -->
        <FilterChecklistSection
          title="Число комнат"
          :items="numberOfRoomsItemsWithCounts"
          v-model="numOfRoomsState"
        />

        <!-- 13) Bed types -->
        <FilterChecklistSection
          title="Тип кроватей"
          :items="bedTypeItemsWithCounts"
          v-model="bedTypeState"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue';
import FilterChecklistSection, { type ChecklistItem } from './FilterChecklistSection.vue';
import DoubleRange from './DoubleRange.vue';
import { HotelType } from '../../services/searchDataset';

export type FiltersModel = {
  minTotal: number;
  maxTotal: number;
  maxDistanceKm: number;
  sort: 'popular' | 'priceAsc' | 'priceDesc' | 'ratingDesc';
  stars: Record<number, boolean>;
  types: Record<HotelType, boolean>;
  reviewScoreMin?: 0 | 5 | 6 | 7 | 8 | 9;

  // ✅ новые реальные фильтры (чеклисты)
  amenitiesHotel?: Partial<Record<string, boolean>>;
  amenitiesRoom?: Partial<Record<string, boolean>>;
  placement?: Partial<Record<string, boolean>>;
  meals?: Partial<Record<string, boolean>>;
  paymentAndBooking?: Partial<Record<string, boolean>>;
  rooms?: Partial<Record<string, boolean>>;   // ключи "1","2","3"...
  bedTypes?: Partial<Record<string, boolean>>;
};

type HotelForCounts = {
  id: string;
  type: HotelType;
  stars: number;
  rating: number;
  priceTotalRub: number;
  distanceKm: number;
  filters?: {
    amenitiesHotel?: string[];
    amenitiesRoom?: string[];
    placement?: string[];
    meals?: string[];
    paymentAndBooking?: string[];
    rooms?: number;
    bedTypes?: string[];
  };
};

const props = defineProps<{
  modelValue: FiltersModel;

  destination?: string;
  dates?: string;
  guestsLabel?: string;

  /** IMPORTANT: чтобы цифры работали, передай сюда baseHotels из родителя */
  hotels?: HotelForCounts[];

  /** чтобы “за ночь” корректно переводить в total — передай nights из родителя */
  nights?: number;
}>();

/**
 * ВАЖНО:
 * Мы НЕ эмитим update:modelValue намеренно — у тебя в родителе v-model сидит на reactive(const),
 * из-за чего попытка присвоения “filters = v” ломает обновления.
 * Поэтому просто мутируем объект modelValue (он один и тот же reactive-объект).
 */
const m = computed(() => props.modelValue);

function patch(p: Partial<FiltersModel>) {
  Object.assign(props.modelValue as any, p);
}

function clamp(n: number, a: number, b: number) {
  return Math.max(a, Math.min(b, n));
}

const nightsSafe = computed(() => {
  const n = Number(props.nights ?? 1);
  return Number.isFinite(n) && n > 0 ? n : 1;
});

const destinationText = computed(() => props.destination ?? '');
const datesText = computed(() => props.dates ?? '');
const guestsText = computed(() => props.guestsLabel ?? '');

/** ---------- defaults / self-heal ---------- */
watchEffect(() => {
  if (!m.value.sort) patch({ sort: 'popular' });

  if (!Number.isFinite(m.value.maxDistanceKm) || m.value.maxDistanceKm <= 0) patch({ maxDistanceKm: 30 });

  if (!Number.isFinite(m.value.minTotal) || m.value.minTotal < 0) patch({ minTotal: 0 });
  if (!Number.isFinite(m.value.maxTotal) || m.value.maxTotal <= 0) patch({ maxTotal: 9999999 });
  if (m.value.maxTotal < m.value.minTotal) patch({ maxTotal: m.value.minTotal });

  const starVals = Object.values(m.value.stars ?? {});
  if (starVals.length && starVals.every((v) => !v)) {
    const repaired: Record<number, boolean> = {};
    for (const k of Object.keys(m.value.stars)) repaired[Number(k)] = true;
    patch({ stars: repaired });
  }

  const typeVals = Object.values(m.value.types ?? {});
  if (typeVals.length && typeVals.every((v) => !v)) {
    const repaired: Record<HotelType, boolean> = { ...(m.value.types as any) };
    (Object.keys(repaired) as HotelType[]).forEach((k) => (repaired[k] = true));
    patch({ types: repaired });
  }

  if (m.value.reviewScoreMin === undefined) patch({ reviewScoreMin: 0 });

  // ✅ гарантируем, что чеклисты существуют
  if (!m.value.amenitiesHotel) patch({ amenitiesHotel: {} });
  if (!m.value.amenitiesRoom) patch({ amenitiesRoom: {} });
  if (!m.value.placement) patch({ placement: {} });
  if (!m.value.meals) patch({ meals: {} });
  if (!m.value.paymentAndBooking) patch({ paymentAndBooking: {} });
  if (!m.value.rooms) patch({ rooms: {} });
  if (!m.value.bedTypes) patch({ bedTypes: {} });
});

/** ---------- price UI (за ночь / за всё время) ---------- */
const priceMode = ref<'night' | 'total'>('night');

const hotelsBase = computed(() => props.hotels ?? []);

const priceUiMax = computed(() => {
  const hs = hotelsBase.value;
  if (!hs.length) return priceMode.value === 'night' ? 100000 : 999999;
  if (priceMode.value === 'night') {
    const perNightMax = Math.max(...hs.map((h) => Math.ceil(h.priceTotalRub / nightsSafe.value)));
    return Math.max(100000, Math.ceil(perNightMax / 1000) * 1000);
  }
  const totalMax = Math.max(...hs.map((h) => h.priceTotalRub));
  return Math.max(100000, Math.ceil(totalMax / 1000) * 1000);
});

const priceUiStep = computed(() => (priceMode.value === 'night' ? 100 : 1000));

const priceUi = computed<{ min: number; max: number }>({
  get() {
    const n = nightsSafe.value;

    const min = priceMode.value === 'night' ? Math.floor(m.value.minTotal / n) : m.value.minTotal;
    const max = priceMode.value === 'night' ? Math.ceil(m.value.maxTotal / n) : m.value.maxTotal;

    return {
      min: clamp(Number(min) || 0, 0, priceUiMax.value),
      max: clamp(Number(max) || 0, 0, priceUiMax.value),
    };
  },
  set(v) {
    const n = nightsSafe.value;

    const minUi = clamp(Number(v.min) || 0, 0, priceUiMax.value);
    const maxUi = clamp(Number(v.max) || 0, 0, priceUiMax.value);

    if (priceMode.value === 'night') {
      patch({ minTotal: minUi * n, maxTotal: maxUi * n });
    } else {
      patch({ minTotal: minUi, maxTotal: maxUi });
    }
  },
});

function onPriceInput(which: 'min' | 'max', e: Event) {
  const raw = Number((e.target as HTMLInputElement).value);
  const next = { ...priceUi.value };
  next[which] = Number.isFinite(raw) ? raw : 0;

  if (which === 'min' && next.min > next.max) next.max = next.min;
  if (which === 'max' && next.max < next.min) next.min = next.max;

  priceUi.value = next;
}

/** ---------- sort / distance ---------- */
function onSort(e: Event) {
  const v = (e.target as HTMLSelectElement).value as FiltersModel['sort'];
  patch({ sort: v });
}

function onDistance(e: Event) {
  const v = Number((e.target as HTMLInputElement).value);
  patch({ maxDistanceKm: clamp(v, 1, 30) });
}

/** ---------- helpers for live counts (как на букинге) ---------- */
type ChecklistState = Partial<Record<string, boolean>>;
type ExcludeKey =
  | 'price'
  | 'distance'
  | 'types'
  | 'stars'
  | 'review'
  | 'amenitiesHotel'
  | 'amenitiesRoom'
  | 'placement'
  | 'meals'
  | 'paymentAndBooking'
  | 'rooms'
  | 'bedTypes';

function selectedKeys(state?: ChecklistState) {
  if (!state) return [];
  return Object.keys(state).filter((k) => !!state[k]);
}

function uniq<T>(arr: T[]) {
  return Array.from(new Set(arr));
}

function matchArray(arr: unknown, selected: string[], mode: 'and' | 'or') {
  if (!selected.length) return true;
  if (!Array.isArray(arr)) return false;
  return mode === 'and'
    ? selected.every((k) => arr.includes(k))
    : selected.some((k) => arr.includes(k));
}

function baseForCounts(exclude: Set<ExcludeKey>) {
  let arr = hotelsBase.value.slice();

  if (!exclude.has('price')) {
    arr = arr.filter((h) => h.priceTotalRub >= m.value.minTotal && h.priceTotalRub <= m.value.maxTotal);
  }
  if (!exclude.has('distance')) {
    arr = arr.filter((h) => h.distanceKm <= m.value.maxDistanceKm);
  }
  if (!exclude.has('stars')) {
    arr = arr.filter((h) => !!m.value.stars?.[h.stars]);
  }
  if (!exclude.has('types')) {
    arr = arr.filter((h) => !!m.value.types?.[h.type]);
  }
  if (!exclude.has('review')) {
    const min = m.value.reviewScoreMin ?? 0;
    if (min > 0) arr = arr.filter((h) => h.rating >= min);
  }

  const aHotel = selectedKeys(m.value.amenitiesHotel);
  const aRoom = selectedKeys(m.value.amenitiesRoom);
  const placement = selectedKeys(m.value.placement);
  const meals = selectedKeys(m.value.meals);
  const pay = selectedKeys(m.value.paymentAndBooking);
  const rooms = selectedKeys(m.value.rooms);
  const beds = selectedKeys(m.value.bedTypes);

  if (!exclude.has('amenitiesHotel')) arr = arr.filter((h) => matchArray(h.filters?.amenitiesHotel, aHotel, 'and'));
  if (!exclude.has('amenitiesRoom')) arr = arr.filter((h) => matchArray(h.filters?.amenitiesRoom, aRoom, 'and'));
  if (!exclude.has('placement')) arr = arr.filter((h) => matchArray(h.filters?.placement, placement, 'and'));
  if (!exclude.has('paymentAndBooking')) arr = arr.filter((h) => matchArray(h.filters?.paymentAndBooking, pay, 'and'));

  if (!exclude.has('meals')) arr = arr.filter((h) => matchArray(h.filters?.meals, meals, 'or'));
  if (!exclude.has('bedTypes')) arr = arr.filter((h) => matchArray(h.filters?.bedTypes, beds, 'or'));

  if (!exclude.has('rooms') && rooms.length) {
    arr = arr.filter((h) => rooms.includes(String(h.filters?.rooms ?? '')));
  }

  return arr;
}

/** ---------- Types (UI: “ничего не выбрано” = показать всё) ---------- */
const typeItemsBase: Array<{ key: HotelType; label: string }> = [
  { key: 'hotel', label: 'Отели' },
  { key: 'hostel', label: 'Хостелы' },
  { key: 'apartment', label: 'Апартаменты, квартиры' },
  { key: 'aparthotel', label: 'Апарт-отели' },
  { key: 'guest_house', label: 'Гостевые дома' },
  { key: 'villa', label: 'Коттеджи, виллы, бунгало' },
];

const typeCounts = computed(() => {
  const hs = baseForCounts(new Set(['types' as ExcludeKey]));
  const map = new Map<HotelType, number>();
  for (const t of typeItemsBase) map.set(t.key, 0);
  for (const h of hs) map.set(h.type, (map.get(h.type) ?? 0) + 1);
  return map;
});

const typeItemsWithCounts = computed(() =>
  typeItemsBase.map((t) => ({ ...t, count: typeCounts.value.get(t.key) ?? 0 }))
);

const isAnyTypes = computed(() => {
  const vals = Object.values(m.value.types ?? {});
  return vals.length ? vals.every(Boolean) : true;
});

function isTypeChecked(key: HotelType) {
  if (isAnyTypes.value) return false;
  return !!m.value.types?.[key];
}

function toggleType(key: HotelType, e: Event) {
  const checked = (e.target as HTMLInputElement).checked;
  const next: Record<HotelType, boolean> = { ...(m.value.types as any) };

  if (isAnyTypes.value) {
    (Object.keys(next) as HotelType[]).forEach((k) => (next[k] = false));
    next[key] = checked;
    patch({ types: next });
    return;
  }

  next[key] = checked;

  const anySelected = Object.values(next).some(Boolean);
  if (!anySelected) {
    (Object.keys(next) as HotelType[]).forEach((k) => (next[k] = true));
  }
  patch({ types: next });
}

/** ---------- Stars (UI: “ничего не выбрано” = показать всё) ---------- */
const starsRows = computed(() => {
  const hs = baseForCounts(new Set(['stars' as ExcludeKey]));

  const c5 = hs.filter((h) => h.stars === 5).length;
  const c4 = hs.filter((h) => h.stars === 4).length;
  const c3 = hs.filter((h) => h.stars === 3).length;
  const c2 = hs.filter((h) => h.stars === 2).length;
  const c10 = hs.filter((h) => h.stars <= 1).length;

  return [
    { key: '5', count: c5 },
    { key: '4', count: c4 },
    { key: '3', count: c3 },
    { key: '2', count: c2 },
    { key: 'oneOrZero', count: c10 },
  ] as const;
});

const isAnyStars = computed(() => {
  const vals = Object.values(m.value.stars ?? {});
  return vals.length ? vals.every(Boolean) : true;
});

function isStarsRowChecked(key: string) {
  if (isAnyStars.value) return false;
  if (key === 'oneOrZero') return !!m.value.stars?.[1] || !!m.value.stars?.[0];
  const n = Number(key);
  return !!m.value.stars?.[n];
}

function toggleStarsRow(key: string, e: Event) {
  const checked = (e.target as HTMLInputElement).checked;
  const next: Record<number, boolean> = { ...(m.value.stars as any) };

  const setAll = (v: boolean) => {
    for (const k of Object.keys(next)) next[Number(k)] = v;
  };

  if (isAnyStars.value) {
    setAll(false);
    if (key === 'oneOrZero') {
      next[0] = checked;
      next[1] = checked;
    } else {
      next[Number(key)] = checked;
    }
    patch({ stars: next });
    return;
  }

  if (key === 'oneOrZero') {
    next[0] = checked;
    next[1] = checked;
  } else {
    next[Number(key)] = checked;
  }

  const anySelected = Object.values(next).some(Boolean);
  if (!anySelected) setAll(true);

  patch({ stars: next });
}

/** ---------- Review score radio ---------- */
type ReviewScoreValue = 'any' | '9' | '8' | '7' | '6' | '5';

const reviewScore = computed<ReviewScoreValue>(() => {
  const v = m.value.reviewScoreMin ?? 0;
  if (v >= 9) return '9';
  if (v >= 8) return '8';
  if (v >= 7) return '7';
  if (v >= 6) return '6';
  if (v >= 5) return '5';
  return 'any';
});

function setReviewScore(v: ReviewScoreValue) {
  const map: Record<ReviewScoreValue, 0 | 5 | 6 | 7 | 8 | 9> = {
    any: 0, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5,
  };
  patch({ reviewScoreMin: map[v] });
}

const reviewScoreOptionsBase = [
  { value: 'any', label: 'Любая оценка' },
  { value: '9', label: 'Супер: 9+' },
  { value: '8', label: 'Отлично: 8+' },
  { value: '7', label: 'Очень хорошо: 7+' },
  { value: '6', label: 'Хорошо: 6+' },
  { value: '5', label: 'Неплохо: 5+' },
] as const;

const reviewScoreOptionsWithCounts = computed(() => {
  const hs = baseForCounts(new Set(['review' as ExcludeKey]));
  const c9 = hs.filter((h) => h.rating >= 9).length;
  const c8 = hs.filter((h) => h.rating >= 8).length;
  const c7 = hs.filter((h) => h.rating >= 7).length;
  const c6 = hs.filter((h) => h.rating >= 6).length;
  const c5 = hs.filter((h) => h.rating >= 5).length;

  const countMap: Record<string, number> = { '9': c9, '8': c8, '7': c7, '6': c6, '5': c5 };

  return reviewScoreOptionsBase.map((o) => ({
    ...o,
    count: o.value === 'any' ? undefined : countMap[o.value],
  }));
});

/** ---------- Чеклисты: теперь они реально пишут в modelValue ---------- */
const amenitiesHotelState = computed<ChecklistState>({
  get: () => m.value.amenitiesHotel ?? {},
  set: (v) => patch({ amenitiesHotel: v }),
});

const amenitiesRoomState = computed<ChecklistState>({
  get: () => m.value.amenitiesRoom ?? {},
  set: (v) => patch({ amenitiesRoom: v }),
});

const placementState = computed<ChecklistState>({
  get: () => m.value.placement ?? {},
  set: (v) => patch({ placement: v }),
});

const mealsState = computed<ChecklistState>({
  get: () => m.value.meals ?? {},
  set: (v) => patch({ meals: v }),
});

const paymentBookingState = computed<ChecklistState>({
  get: () => m.value.paymentAndBooking ?? {},
  set: (v) => patch({ paymentAndBooking: v }),
});

const numOfRoomsState = computed<ChecklistState>({
  get: () => m.value.rooms ?? {},
  set: (v) => patch({ rooms: v }),
});

const bedTypeState = computed<ChecklistState>({
  get: () => m.value.bedTypes ?? {},
  set: (v) => patch({ bedTypes: v }),
});

/** ---------- Items lists ---------- */
const amenitiesHotelItems: ChecklistItem[] = [
  { key: 'internet', label: 'Бесплатный интернет' },
  { key: 'transfer', label: 'Трансфер' },
  { key: 'parking', label: 'Парковка' },
  { key: 'pool', label: 'Бассейн' },
  { key: 'fitness', label: 'Фитнес' },
  { key: 'bar', label: 'Бар или ресторан' },
  { key: 'conf', label: 'Конференц-зал' },
  { key: 'spa', label: 'Спа-услуги' },
  { key: 'washer', label: 'Стиральная машина' },
  { key: 'ski', label: 'Горнолыжный склон рядом' },
  { key: 'beach', label: 'Пляж рядом' },
  { key: 'jacuzzi', label: 'Джакузи' },
  { key: 'ev', label: 'Зарядка для электромобилей' },
];

const amenitiesRoomItems: ChecklistItem[] = [
  { key: 'ac', label: 'Кондиционер' },
  { key: 'bath', label: 'Ванная комната в номере' },
  { key: 'kitchen', label: 'Кухня' },
  { key: 'balcony', label: 'Балкон' },
];

const placementItems: ChecklistItem[] = [
  { key: 'kids', label: 'Подходит для детей' },
  { key: 'accessible', label: 'Для гостей с ограниченными возможностями' },
  { key: 'pets', label: 'Разрешено с домашними животными' },
  { key: 'smoking', label: 'Можно курить' },
];

const mealsItems: ChecklistItem[] = [
  { key: 'mealsNotIncluded', label: 'Питание не включено' },
  { key: 'breakfastIncluded', label: 'Завтрак включен' },
  { key: 'breakfastAndLunchOrDinner', label: 'Завтрак + обед или ужин включены' },
  { key: 'breakfastAndLunchAndDinner', label: 'Завтрак, обед и ужин включены' },
  { key: 'allInclusive', label: 'Все включено' },
];

const paymentAndBookingItems: ChecklistItem[] = [
  { key: 'noCardRequired', label: 'Для бронирования не нужна карта' },
  { key: 'freeCancellation', label: 'Есть бесплатная отмена' },
  { key: 'payNow', label: 'Оплата сейчас' },
  { key: 'payOnsite', label: 'Оплата на месте' },
];

const numberOfRoomsItems: ChecklistItem[] = [
  { key: '1', label: '1 комната' },
  { key: '2', label: '2 комнаты' },
  { key: '3', label: '3 комнаты' },
  { key: '4', label: '4 комнаты' },
  { key: '5', label: '5 комнат' },
  { key: '6', label: '6 комнат' },
];

const bedTypeItems: ChecklistItem[] = [
  { key: 'doubleBed', label: 'Двуспальная кровать' },
  { key: 'separateBed', label: 'Раздельная кровать' },
];

/** ---------- Live counts for checklist sections ---------- */
const amenitiesHotelItemsWithCounts = computed(() => {
  const hs = baseForCounts(new Set(['amenitiesHotel' as ExcludeKey]));
  const selected = selectedKeys(m.value.amenitiesHotel);

  return amenitiesHotelItems.map((it) => {
    const next = uniq([...selected, it.key]);
    const count = hs.filter((h) => matchArray(h.filters?.amenitiesHotel, next, 'and')).length;
    return { ...it, count };
  });
});

const amenitiesRoomItemsWithCounts = computed(() => {
  const hs = baseForCounts(new Set(['amenitiesRoom' as ExcludeKey]));
  const selected = selectedKeys(m.value.amenitiesRoom);

  return amenitiesRoomItems.map((it) => {
    const next = uniq([...selected, it.key]);
    const count = hs.filter((h) => matchArray(h.filters?.amenitiesRoom, next, 'and')).length;
    return { ...it, count };
  });
});

const placementItemsWithCounts = computed(() => {
  const hs = baseForCounts(new Set(['placement' as ExcludeKey]));
  const selected = selectedKeys(m.value.placement);

  return placementItems.map((it) => {
    const next = uniq([...selected, it.key]);
    const count = hs.filter((h) => matchArray(h.filters?.placement, next, 'and')).length;
    return { ...it, count };
  });
});

const mealsItemsWithCounts = computed(() => {
  const hs = baseForCounts(new Set(['meals' as ExcludeKey]));
  const selected = selectedKeys(m.value.meals);

  return mealsItems.map((it) => {
    const next = uniq([...selected, it.key]);
    const count = hs.filter((h) => matchArray(h.filters?.meals, next, 'or')).length;
    return { ...it, count };
  });
});

const paymentAndBookingItemsWithCounts = computed(() => {
  const hs = baseForCounts(new Set(['paymentAndBooking' as ExcludeKey]));
  const selected = selectedKeys(m.value.paymentAndBooking);

  return paymentAndBookingItems.map((it) => {
    const next = uniq([...selected, it.key]);
    const count = hs.filter((h) => matchArray(h.filters?.paymentAndBooking, next, 'and')).length;
    return { ...it, count };
  });
});

const numberOfRoomsItemsWithCounts = computed(() => {
  const hs = baseForCounts(new Set(['rooms' as ExcludeKey]));
  return numberOfRoomsItems.map((it) => ({
    ...it,
    count: hs.filter((h) => String(h.filters?.rooms ?? '') === it.key).length,
  }));
});

const bedTypeItemsWithCounts = computed(() => {
  const hs = baseForCounts(new Set(['bedTypes' as ExcludeKey]));
  const selected = selectedKeys(m.value.bedTypes);

  return bedTypeItems.map((it) => {
    const next = uniq([...selected, it.key]);
    const count = hs.filter((h) => matchArray(h.filters?.bedTypes, next, 'or')).length;
    return { ...it, count };
  });
});

const favOnly = ref(false);
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-family: PTRootUI, Verdana, sans-serif;
}
.sidebar p {
  margin: 0;
}

/* top search card */
.searchCard {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  padding-block-end: 8px;
  padding-block-start: 8px;
  padding-inline-start: 16px;
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
}

.searchIcon {
  bottom: 12px;
  right: 16px;
  block-size: 16px;
  color: #0e41d2;
  inline-size: 16px;
  position: absolute;
}

.searchTextBox {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  width: 100%;
}

.searchDestination {
  color: #0e41d2;
  font-size: 16px;
  font-weight: 500;
  line-height: 22px;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.16s;
  white-space: nowrap;
}

.searchText {
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  color: var(--bench-text, #2d3137);
}

/* filters card */
.card {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.06);
}
.filtersContainer {
  display: flex;
  flex-direction: column;
  row-gap: 24px;
}

/* favorites */
.favoritesRow {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.favLeft {
  display: flex;
  align-items: center;
  gap: 8px;
}
.heartIcon {
  width: 24px;
  height: 24px;
  background: #d10000;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='white' d='M12 21s-7.2-4.4-10-9.3C-.4 6.9 2.6 3 6.5 3c2.1 0 3.7 1.2 4.5 2.3C11.8 4.2 13.4 3 15.5 3 19.4 3 22.4 6.9 22 11.7 19.2 16.6 12 21 12 21Z'/%3E%3C/svg%3E")
    center / contain no-repeat;
}
.favTitle {
  font-size: 16px;
  font-weight: 500;
  line-height: 22px;
  color: var(--bench-text, #2d3137);
}

/* section titles */
.sectionTitle {
  font-size: 16px;
  line-height: 22px;
  margin-block-end: 12px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
}

/* select */
.selectWrap {
  position: relative;
  width: 100%;
}
.select {
  width: 100%;
  height: 36px;
  border-radius: 12px;
  border: 1px solid #c8c8c8;
  padding: 0 8px 0 12px;
  font-size: 16px;
  font-weight: 500;
  color: var(--bench-text, #2d3137);
  outline: none;
  appearance: none;
  background: var(--bench-surface-elevated, #fff);
  font-family: PTRootUI, Verdana, sans-serif;
}
.selectChevron {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* segmented */
.segmented {
  display: flex;
  background: var(--bench-primary-light, #e5e5e5);
  border-radius: 8px;
  padding: 2px;
  width: 100%;
  margin-block-end: 8px;
}
.segBtn {
  border: none;
  cursor: pointer;
  flex-basis: 50%;
  padding: 4px 14px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 500;
  color: #868686;
  background: transparent;
  text-align: center;
  font-family: PTRootUI, Verdana, sans-serif;
}
.segBtn.active {
  background: var(--bench-surface-elevated, #fff);
  color: var(--bench-text, #2d3137);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* price box */
.priceBox {
  display: flex;
  align-items: center;
  border: 1px solid #c8c8c8;
  border-radius: 12px;
  overflow: hidden;
  height: 36px;
}
.priceCell {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}
.priceDivider {
  width: 1px;
  height: 100%;
  background: #c8c8c8;
}
.priceInput {
  width: 100%;
  height: 100%;
  border: 0;
  outline: 0;
  padding: 0 8px 0 12px;
  font-size: 16px;
  font-weight: 500;
  line-height: 20px;
  color: var(--bench-text, #2d3137);
  background: var(--bench-surface-elevated, #fff);
  font-family: PTRootUI, Verdana, sans-serif;
}
.priceSuffix {
  position: absolute;
  right: 14px;
  font-size: 16px;
  font-weight: 400;
  color: var(--bench-text, #2d3137);
}
.priceSlider {
  margin-top: 14px;
}

/* remove number arrows */
.priceInput::-webkit-outer-spin-button,
.priceInput::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.priceInput[type='number'] {
  -moz-appearance: textfield;
}

/* distance */
.distanceInp {
  width: 100%;
  height: 36px;
  border-radius: 12px;
  border: 1px solid #c8c8c8;
  padding: 0 8px 0 12px;
  font-size: 16px;
  font-weight: 500;
  line-height: 20px;
  color: var(--bench-text, #2d3137);
  outline: none;
  background: var(--bench-surface-elevated, #fff);
  box-sizing: border-box;
  font-family: PTRootUI, Verdana, sans-serif;
}
.distanceSlider {
  margin-top: 12px;
}
.singleRange {
  width: 100%;
  appearance: none;
  height: 6px;
  border-radius: 999px;
  background: #0e41d2;
}
.singleRange::-webkit-slider-thumb {
  appearance: none;
  width: 26px;
  height: 26px;
  background: var(--bench-surface-elevated, #fff);
  border: 6px solid #0e41d2;
  border-radius: 50%;
  cursor: pointer;
  margin-top: -10px;
}
.singleRange::-moz-range-thumb {
  width: 26px;
  height: 26px;
  background: var(--bench-surface-elevated, #fff);
  border: 6px solid #0e41d2;
  border-radius: 50%;
  cursor: pointer;
}

/* switch */
.switch {
  position: relative;
  width: 36px;
  height: 20px;
}
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.slider {
  position: absolute;
  inset: 0;
  background: rgba(45, 49, 55, 0.2);
  border-radius: 999px;
  transition: 0.2s;
}
.slider:before {
  content: "";
  position: absolute;
  height: 16px;
  width: 16px;
  left: 2px;
  top: 2px;
  background: var(--bench-surface-elevated, #fff);
  border-radius: 50%;
  transition: 0.2s;
  box-shadow: 0 2px 6px rgba(0,0,0,0.18);
}
.switch input:checked + .slider {
  background: #0e41d2;
}
.switch input:checked + .slider:before {
  transform: translateX(16px);
}

/* generic list rows (type/stars) */
.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.rowLeft {
  cursor: pointer;
  display: inline-flex;
  gap: 10px;
  min-width: 0;
  flex: 1;
  user-select: none;
  align-items: center;
}
.rowText {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  font-family: PTRootUI, Verdana, sans-serif;
}
.labelText {
  font-size: 14px;
  font-weight: 480;
  line-height: 20px;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}
.count {
  color: #868686;
  font-size: 16px;
  font-weight: 500;
  line-height: 20px;
  margin-inline-start: auto;
  padding-inline-start: 10px;
}

/* checkbox like Отели */
.chk {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1px solid #e5e5e5;
  appearance: none;
  display: grid;
  place-items: center;
  background: var(--bench-surface-elevated, #fff);
  cursor: pointer;
  flex: 0 0 auto;
}
.chk:checked {
  border-color: #0e41d2;
  background: #0e41d2;
}
.chk:checked::after {
  content: '';
  width: 10px;
  height: 6px;
  border: 2px solid #fff;
  border-top: 0;
  border-right: 0;
  transform: rotate(-45deg);
  margin-top: -1px;
}

/* stars */
.starsWrap {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}
.star {
  color: #ff9d00;
  font-size: 20px;
  line-height: 1;
}

/* radio block */
.radioList {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.radioRow {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  user-select: none;
}
.radioInp {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}
.radioUi {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  border: 2px solid #e5e5e5;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}
.radioInp:checked + .radioUi {
  border-color: #0e41d2;
}
.radioInp:checked + .radioUi::after {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #0e41d2;
}
.radioLabel {
  font-size: 16px;
  font-weight: 500;
  line-height: 20px;
  color: var(--bench-text, #2d3137);
}
.radioCount {
  margin-left: auto;
  color: #868686;
  font-size: 16px;
  font-weight: 500;
  line-height: 20px;
}
</style>
