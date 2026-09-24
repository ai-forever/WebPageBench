<!-- HotelReviews.vue -->
<template>
  <div v-if="block" class="HotelReviews">
    <!-- TOP RATING (как Rating_rating__tVvPz) -->
    <div class="RatingTop">
      <div class="RatingTotal">
        <div class="BadgeWrap">
          <TotalRatingBadge :value="block.ratingSummary.value" size="l" />
        </div>

        <p class="RatingDesc">{{ category }}</p>

        <p class="RatingLine">
          {{ formatText(block.ratingSummary.basedOnText, { TOTAL: block.ratingSummary.totalReviews }) }}
        </p>

        <p class="RatingLine">
          {{
            formatText(block.ratingSummary.localLanguageText, {
              LOCAL: block.ratingSummary.localLanguageReviews,
            })
          }}
        </p>
      </div>

      <ul class="DetailedList">
        <li v-for="(it, idx) in block.detailedScores" :key="it.label + idx" class="DetailedItem">
          <div class="Range">
            <div class="RangeBg"></div>
            <div class="RangeVal" :style="{ width: rangeWidth(it.value), backgroundColor: rangeColor }"></div>
          </div>

          <div class="DetailedText">
            <p class="DetailedLabel">{{ it.label }}</p>
            <p v-if="it.value !== undefined" class="DetailedValue">{{ toComma(it.value) }}</p>
          </div>
        </li>
      </ul>

      <div class="TripAdvisor" v-if="block.tripadvisor?.href">
        <a class="TaLink" :href="block.tripadvisor.href" target="_blank" rel="noreferrer">
          <p class="TaTitle">{{ block.tripadvisor.label ?? 'TripAdvisor' }}</p>
          <div class="TaContent">
            <img class="TaLogo" :src="TA_LOGO" alt="TripAdvisor" mention="lazy" decoding="async" />
            <p class="TaReviews">{{ block.tripadvisor.reviews }} отзывов</p>
          </div>
        </a>
      </div>
    </div>

    <!-- SORT (как на скрине) -->
    <div ref="sortRoot" class="SortWrap">
      <button
        class="SortControl"
        type="button"
        :class="{ SortControl_open: sortOpen }"
        aria-haspopup="listbox"
        :aria-expanded="sortOpen"
        @click="toggleSort"
      >
        <div>

          <span class="SortLabel">Сортировка отзывов</span>
          
          <span class="SortValueRow">
            <span class="SortValue">{{ selectedSortLabel }}</span>
            
            <svg class="SortChevron" :class="{ SortChevron_open: sortOpen }" width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
              <path
              fill-rule="nonzero"
              d="M10.908 14.623l6.139-6.14c.5-.499.5-1.315 0-1.815l-.172-.174a1.29 1.29 0 0 0-1.817 0L10 11.553l-5.06-5.06a1.288 1.288 0 0 0-1.814 0l-.173.175c-.5.5-.5 1.316 0 1.816l6.14 6.139a1.288 1.288 0 0 0 1.815 0"
              />
            </svg>
          </span>
        </div>
      </button>

      <div v-if="sortOpen" class="SortMenu" role="listbox">
        <button
          v-for="opt in SORT_OPTIONS"
          :key="opt.value"
          class="SortOption"
          type="button"
          role="option"
          :aria-selected="opt.value === sortValue"
          :class="{ SortOption_active: opt.value === sortValue }"
          @click="selectSort(opt.value)"
        >
          <span class="SortValue">{{ opt.label }}</span>

          <svg v-if="opt.value === sortValue" class="SortCheck" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path
              fill-rule="nonzero"
              d="M7.7 13.6 4.4 10.3a1 1 0 0 1 1.4-1.4l1.9 1.9 6.5-6.5a1 1 0 0 1 1.4 1.4l-7.2 7.2a1 1 0 0 1-1.4 0Z"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- REVIEWS LIST -->
    <ul class="ReviewList">
      <li v-for="r in visibleReviews" :key="r.id" class="ReviewCard">
        <!-- HEADER ROW -->
        <div class="ReviewHeader ReviewHeaderLeft">
          <span class="UserName">{{ r.author }}</span>
          <div v-if="r.countryCode" class="UserFlag" :class="`UserFlag_${r.countryCode.toLowerCase()}`"></div>
        </div>

        <div class="ReviewHeader ReviewHeaderRight">
          <img class="TaLogoSmall" :src="TA_LOGO_SMALL" alt="TripAdvisor" loading="lazy" decoding="async" />
        </div>

        <!-- BODY ROW -->
        <div class="ReviewMeta">
          <p v-if="r.tripType" class="UserMeta UserMetaTrip">{{ r.tripType }}</p>
          <p v-if="r.date" class="UserMeta">{{ r.date }}</p>
        </div>

        <div class="ReviewBody">
          <p class="ReviewTitle">{{ r.title }}</p>

          <p class="ReviewText" :class="{ ReviewText_clamped: !expanded[r.id] }">
            {{ r.text }}
          </p>

          <button v-if="isLong(r.text)" class="SpoilerBtn" type="button" @click="toggle(r.id)">
            <svg
              width="16"
              height="16"
              viewBox="0 0 20 20"
              fill="currentColor"
              class="SpoilerArrow"
              :class="{ SpoilerArrow_open: expanded[r.id] }"
            >
              <path
                fill-rule="nonzero"
                d="M10.908 14.623l6.139-6.14c.5-.499.5-1.315 0-1.815l-.172-.174a1.29 1.29 0 0 0-1.817 0L10 11.553l-5.06-5.06a1.288 1.288 0 0 0-1.814 0l-.173.175c-.5.5-.5 1.316 0 1.816l6.14 6.139a1.288 1.288 0 0 0 1.815 0"
              />
            </svg>
            {{ expanded[r.id] ? 'Свернуть отзыв' : 'Развернуть отзыв' }}
          </button>
        </div>
      </li>
    </ul>

    <!-- Pagination button (как в оригинале) -->
    <div class="Pagination_wrapper">
      <a class="Button Button_size_s Button_view_light Pagination_nextPageButton" :href="block?.moreLink?.href" target="_blank" rel="noreferrer">
        <span class="Button_content">
          {{ formatText(block?.moreLink?.text || '', { N: block?.moreLink?.remaining || 0 }) }}
        </span>
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, onMounted, onBeforeUnmount } from 'vue';
import TotalRatingBadge from './TotalRatingBadge.vue';

type DetailedScore = { label: string; value?: number };

type Review = {
  id: string;
  source: 'tripadvisor';
  author: string;
  countryCode?: string; // "ru" | "ee" etc
  tripType?: string;
  date?: string; // "октябрь 2018 г."
  rating?: number; // 0..5
  title: string;
  text: string;
};

type ReviewsBlock = {
  title: string;
  ratingSummary: {
    value: number;
    totalReviews: number;
    localLanguageReviews: number;
    basedOnText: string;
    localLanguageText: string;
  };
  detailedScores: DetailedScore[];
  tripadvisor?: { label?: string; reviews: number; href: string };
  reviews: Review[];
  moreLink?: { href: string; remaining: number; text: string };
  ui?: { showCount?: number };
};

type Hotel = { id: string; reviewsBlock?: ReviewsBlock };

const props = defineProps<{ hotel: Hotel }>();

const block = computed(() => props.hotel.reviewsBlock ?? null);

const expanded = reactive<Record<string, boolean>>({});

const showCount = computed(() => {
  const n = Number(block.value?.ui?.showCount);
  if (!Number.isFinite(n)) return 3;
  return Math.max(1, Math.min(10, Math.floor(n)));
});

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

/** ---------- SORT ---------- */
type SortValue = 'useful' | 'new' | 'high' | 'low';

const SORT_OPTIONS: Array<{ value: SortValue; label: string }> = [
  { value: 'useful', label: 'Сначала полезные' },
  { value: 'new', label: 'Сначала новые' },
  { value: 'high', label: 'Сначала высокая оценка' },
  { value: 'low', label: 'Сначала низкая оценка' },
];

const sortValue = ref<SortValue>('useful');
const sortOpen = ref(false);
const sortRoot = ref<HTMLElement | null>(null);

const selectedSortLabel = computed(() => SORT_OPTIONS.find((x) => x.value === sortValue.value)?.label ?? 'Сначала полезные');

function toggleSort() {
  sortOpen.value = !sortOpen.value;
}

function selectSort(v: SortValue) {
  sortValue.value = v;
  sortOpen.value = false;
}

function parseRuMonthYear(s?: string) {
  const str = String(s ?? '').toLowerCase();
  const m = str.match(/([а-яё]+)\s+(\d{4})/i);
  if (!m) return { y: 0, mo: 0 };
  const month = m[1];
  const year = Number(m[2]) || 0;

  const months: Record<string, number> = {
    январь: 1,
    февраль: 2,
    март: 3,
    апрель: 4,
    май: 5,
    июнь: 6,
    июль: 7,
    август: 8,
    сентябрь: 9,
    октябрь: 10,
    ноябрь: 11,
    декабрь: 12,
  };

  return { y: year, mo: months[month] ?? 0 };
}

const sortedReviews = computed(() => {
  const all = (block.value?.reviews ?? []).slice();

  if (sortValue.value === 'useful') return all;

  if (sortValue.value === 'new') {
    return all.sort((a, b) => {
      const A = parseRuMonthYear(a.date);
      const B = parseRuMonthYear(b.date);
      return B.y !== A.y ? B.y - A.y : B.mo - A.mo;
    });
  }

  if (sortValue.value === 'high') {
    return all.sort((a, b) => (Number(b.rating) || 0) - (Number(a.rating) || 0));
  }

  // low
  return all.sort((a, b) => (Number(a.rating) || 0) - (Number(b.rating) || 0));
});

const visibleReviews = computed(() => sortedReviews.value.slice(0, showCount.value));

const showMoreButton = computed(() => {
  const allLen = (block.value?.reviews ?? []).length;
  return allLen > showCount.value;
});

function isLong(text: string) {
  return String(text ?? '').length > 220;
}

function toggle(id: string) {
  expanded[id] = !expanded[id];
}

/** close sort menu on outside click */
function onDocClick(e: MouseEvent) {
  if (!sortOpen.value) return;
  const root = sortRoot.value;
  if (!root) return;
  const target = e.target as Node | null;
  if (target && !root.contains(target)) sortOpen.value = false;
}

onMounted(() => document.addEventListener('click', onDocClick));
onBeforeUnmount(() => document.removeEventListener('click', onDocClick));

/** ---------- TOP RATING HELPERS ---------- */
const category = computed(() => {
  const r = clamp(Number(block.value?.ratingSummary?.value) || 0, 0, 10);
  if (r >= 9.0) return 'Превосходно';
  if (r >= 8.0) return 'Очень хорошо';
  if (r >= 7.0) return 'Очень хорошо'; // как на скрине при 7,6
  if (r >= 6.0) return 'Неплохо';
  return 'Плохо';
});

const rangeColor = computed(() => {
  const r = clamp(Number(block.value?.ratingSummary?.value) || 0, 0, 10);
  const hue = (r / 10) * 120;
  return `hsl(${hue} 78% 45%)`;
});

function rangeWidth(v?: number) {
  const n = Number(v);
  if (!Number.isFinite(n) || n <= 0) return '0%';
  return `${clamp(n, 0, 10) * 10}%`;
}

function toComma(v: number) {
  const s = (Number(v) || 0).toFixed(1).replace('.0', '');
  return s.replace('.', ',');
}

function formatText(tpl: string, vars: Record<string, string | number>) {
  let s = String(tpl ?? '');
  // @ts-ignore
  for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, String(v));
  return s;
}

const TA_LOGO = '/hotels/cdn/LogoTA_40.3d63d865.svg';
const TA_LOGO_SMALL = '/hotels/cdn/LogoTA_50.b8f3c223.svg';
</script>

<style scoped>
.HotelReviews {
  font-family: PTRootUI, Verdana, sans-serif;
  background-color: var(--bench-surface-elevated, #fff);
  border-radius: 16px !important;
  padding-block-end: 40px;
}

/* TOP rating block divider exactly as you pasted */
.RatingTop {
  border-block-end: 1px solid #e5e5e5;
  display: flex;
  gap: 18px;
  margin-block-end: 16px;
  padding: 12px 24px 16px;
  background: var(--bench-surface-elevated, #fff);
  border-top-left-radius: 16px !important;
  border-top-right-radius: 16px !important;
}

/* left summary */
.RatingTotal {
  position: relative;
  padding-inline-start: 76px;
  margin-inline-end: 24px;
}

.BadgeWrap {
  position: absolute;
  top: -20px;
  left: 0;
}

.RatingDesc {
  margin: 0 0 6px;
  color: var(--bench-text, #2d3137);
  font-size: 18px;
  font-weight: 700;
  line-height: 22px;
  max-inline-size: 180px;
}

.RatingLine {
  margin: 0;
  color: #868686;
  font-size: 12px;
  font-weight: 480;
  line-height: 14px;
  max-inline-size: 100px;
}

/* detailed list */
.DetailedList {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  column-gap: 28px;
  flex-grow: 1;
  font-size: 12px;
}

.DetailedItem {
  margin-block-start: 8px;
  margin-block-end: 5px;
  display: flex;
  flex-direction: column;
}

.Range {
  position: relative;
  height: 4px;
}
.RangeBg {
  position: absolute;
  inset: 0;
  border-radius: 4px;
  background: #e9e9e9;
}
.RangeVal {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: 4px;
  width: 0%;
}

.DetailedText {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.DetailedLabel,
.DetailedValue {
  margin: 0;
  color: var(--bench-text, #2d3137);
  font-size: 12px;
  font-weight: 500;
  line-height: 16px;
}

/* TA block */
.TripAdvisor {
  border-inline-start: 1px solid #e5e5e5;
  flex-shrink: 0;
  padding-inline-start: 20px;
}

.TaLink {
  text-decoration: none;
  color: inherit;
  display: grid;
  gap: 8px;
}

.TaTitle {
  margin: 0;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
}

.TaContent {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.TaLogo {
  height: 20px;
}

.TaReviews {
  margin: 0;
  color: #868686;
  font-size: 12px;
  font-weight: 480;
}

/* REVIEWS LIST */
.ReviewList {
  margin: 0 24px;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 18px;
}

/* Card grid: 2 cols x 2 rows */
.ReviewCard {
  display: grid;
  grid-template-columns: 320px 1fr;
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  overflow: hidden;
  margin-block-end: 40px;
}

/* header row */
.ReviewHeader {
  background: var(--bench-primary-light, #f4f4f4);
  display: flex;
  align-items: center;
  block-size: 48px;
  padding: 16px 20px;
}

.ReviewHeaderLeft {
  gap: 8px;
  border-radius: 12px 0 0 12px;
}

.ReviewHeaderRight {
  border-inline-start: 1px solid #e5e5e5;
  gap: 14px;
  justify-content: flex-start;
  border-radius: 0 12px 12px 0;
}

/* left meta col (row 2) */
.ReviewMeta {
  padding: 16px 20px 12px;
}

.UserName {
  color: var(--bench-text, #2d3137);
  font-size: 16px;
  font-weight: 700;
  line-height: 19px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* flag as svg background (как у тебя) */
.UserFlag {
  background-repeat: no-repeat;
  background-size: contain;
  block-size: 12px;
  border-radius: 2px;
  flex-shrink: 0;
  inline-size: 18px;
}

/* минимум: ru, ee (добавишь при желании) */
.UserFlag_ru {
  background-image: url(/hotels/cdn/ru.095a6d30_475a82d4_1.svg);
}

.UserMeta {
  margin: 0 0 12px;
  color: #868686;
  font-size: 12px;
  font-weight: 480;
  line-height: 16px;
}

.UserMetaTrip {
  color: var(--bench-text, #2d3137);
}

/* right body col (row 2) */
.ReviewBody {
  border-inline-start: 1px solid #e5e5e5;
  padding: 16px 20px 0;
  word-break: break-word;
}

.ReviewTitle {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 700;
  line-height: 20px;
  color: var(--bench-text, #2d3137);
}

.ReviewText {
  margin: 0;
  color: var(--bench-text, #2d3137);
  font-size: 14px;
  font-weight: 400;
  line-height: 20px;
}

.ReviewText_clamped {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* TA header inside review */
.TaLogoSmall {
  height: 22px;
  width: auto;
}

.TaBubbles {
  display: flex;
  align-items: center;
  gap: 8px;
}
.TaBubble {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: #d8d8d8;
}
.TaBubble_on {
  background: #25ac03;
}

/* spoiler button like original */
.SpoilerBtn {
  margin-top: 14px;
  border: 0;
  background: none;
  color: #0e41d2;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  font-family: PTRootUI, Verdana, sans-serif;
}

.SpoilerArrow {
  transition: transform 0.3s ease;
}
.SpoilerArrow_open {
  transform: rotate(180deg);
}

/* Pagination button (как в оригинале) */
.Pagination_wrapper:not(:empty) {
  display: flex;
  flex-direction: column;
  margin-inline-start: 40px;
  margin-inline-end: 40px;
  margin-block-start: 22px;
}

.Pagination_nextPageButton {
  inline-size: 100%;
}

/* “Button” стили */
.Button {
  align-items: center;
  background-color: var(--bench-primary-light, rgb(237, 242, 252));
  border: 1px solid #0000;
  border-radius: var(--t-button-radius, 12px);
  box-sizing: border-box;
  color: #0e41d2;
  cursor: pointer;
  display: inline-flex;
  font-weight: 500;
  justify-content: center;
  min-inline-size: 40px;
  position: relative;
  text-decoration: none;
  transition: background-color 0.16s ease, color 0.16s ease, box-shadow 0.16s ease;
  user-select: none;
}

.Button_view_light {
  background-color: var(--bench-primary-light, rgb(237, 242, 252));
  color: var(--bench-primary, #0e41d2);
}

.Button_size_s {
  block-size: var(--t-compsize-sm, 40px);
  min-inline-size: var(--t-compsize-sm, 40px);
  padding: 0 var(--t-spacing-md, 12px);
  font-size: var(--t-fontsize-md, 16px);
  line-height: 20px;
}

.Button_content {
  padding: 0 var(--t-spacing-xs, 4px);
}

/* ---------- SORT STYLES (только добавил, остальное не трогал) ---------- */
.SortWrap {
  position: relative;
  margin: 0 24px 18px;
  max-inline-size: 250px;
}

.SortControl {
  /* inline-size: 100%; */
  min-inline-size: 250px;
  block-size: 48px;
  border: 1px solid #c8c8c8;
  border-radius: 16px;
  background: var(--bench-surface-elevated, #fff);
  /* padding: 12px 16px; */
  cursor: pointer;
  text-align: start;
  padding: 0 12px;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  justify-content: center;
  inline-size: 86%;
  /* gap: 6px;s */
  transition: box-shadow 0.16s ease, border-color 0.16s ease;
}

.SortControl_open {
  box-shadow: 0 0 0 3px rgba(14, 65, 210, 0.18);
  border-color: rgba(14, 65, 210, 0.55);
}

.SortLabel {
  color: #868686;
  font-size: 12px;
  font-weight: 480;
  line-height: 14px;
  margin: 0;
}

.SortValueRow {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  block-size: 20px;
}

.SortValue {
  color: var(--bench-text, #2d3137);
  font-size: 16px;
  font-weight: 500;
  line-height: 20px;
}

.SortChevron {
  color: #868686;
  transition: transform 0.16s ease;
}
.SortChevron_open {
  transform: rotate(180deg);
}

.SortMenu {
  position: absolute;
  inset: calc(100% + 10px) 0 auto 0;
  background: var(--bench-surface-elevated, #fff);
  border-radius: 18px;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  z-index: 10;
}

.SortOption {
  inline-size: 100%;
  border: 0;
  background: var(--bench-surface-elevated, #fff);
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 16px;
  font-weight: 700;
  line-height: 20px;
  color: var(--bench-text, #2d3137);
  text-align: start;
}

.SortOption_active {
  background: rgba(14, 65, 210, 0.08);
}

.SortCheck {
  color: var(--bench-text, #2d3137);
}

/* responsive */
@media (max-width: 980px) {
  .RatingTop {
    flex-direction: column;
  }

  .ReviewCard {
    grid-template-columns: 1fr;
    grid-template-rows: 48px 48px auto auto;
  }

  .ReviewHeaderRight,
  .ReviewBody {
    border-inline-start: 0;
  }
}
</style>
