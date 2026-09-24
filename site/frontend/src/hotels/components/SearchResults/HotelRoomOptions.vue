<template>
  <section class="roomOptions">
    <div class="shell">
      <div class="header">
        <h3 class="hTitle">{{ titleText }}</h3>
        <p class="hDesc">На {{ nightsText }} ноч{{ nightsSuffix }}, для {{ adultsText }} взрослых{{ roomsHint }}</p>

        <div class="filters">
          <button class="filterPill" type="button">
            Кровати
          </button>
          <button class="filterPill" type="button">
            Питание
          </button>
          <button class="filterPill" type="button">
            Оплата
          </button>
          <button class="filterPill" type="button">
            Условия отмены
          </button>
        </div>
      </div>

      <div class="groups">
        <div
          v-for="g in groups"
          :key="g.id"
          class="groupRow"
        >
          <!-- LEFT: room card -->
          <div class="roomCard">
            <div v-if="g.alert" class="roomAlert">
              {{ g.alert }}
            </div>

            <div class="roomMedia" role="button" tabindex="0">
              <img class="roomImg" :src="g.imageUrl" :alt="g.name" loading="eager" />
              <div class="imgCount">
                <!-- <span class="camIcon" aria-hidden="true"></span> -->
                <p class="imgCountText">
                  {{ g.imageCount }} {{ galleryCtaText }}
                </p>
              </div>
            </div>

            <div class="roomInfo">
              <div style="margin-block-end: 8px;">
                <p class="roomName" role="button" tabindex="0">{{ g.name }}</p>
                <p class="roomSub" role="button" tabindex="0">{{ g.nameAdditional }}</p>
              </div>

              <div class="roomAmenities">
                <div
                  v-for="(a, i) in shownAmenities(g.amenities)"
                  :key="a.key + '-' + i"
                  class="amenityChip"
                >
                  <div class="amenityIcon" :class="'ic-' + a.key" aria-hidden="true"></div>
                  <p class="amenityLabel">{{ a.label }}</p>
                </div>
              </div>

              <div class="moreLink">Ещё</div>
            </div>
          </div>

          <!-- RIGHT: rates -->
          <div class="ratesWrap">
            <div class="ratesContainer">
              <div v-for="r in g.rates" :key="r.id" class="rateCard">
                <div>
                <!-- bed -->
                <div class="rateRow">
                  <div style="display: flex; gap: 8px;">

                    <span class="rateIcon ic-bed" aria-hidden="true"></span>
                    <div class="rowText">
                      {{ r.bedText }}
                    </div>
                  </div>

                  <svg class="HintIcon" fill="none" height="22" viewBox="0 0 22 22" width="22"><rect x="3" y="3" width="16" height="16" rx="4"></rect><path d="M11 6c-.555 0-1.004.459-1.004 1.025 0 .566.45 1.025 1.004 1.025.555 0 1.005-.46 1.005-1.025C12.005 6.459 11.555 6 11 6ZM10.265 13.831H9V15h4v-1.169h-1.265V9.155H9v1.17h1.265v3.506Z"></path></svg>
                </div>

                <!-- meal -->
                <div class="rateRow">
                  <div style="display: flex; gap: 8px;">
                    <span class="rateIcon ic-meal" :class="{ feature: r.meal?.isFeature }" aria-hidden="true"></span>
                    <div class="rowText" :class="{ feature: r.meal?.isFeature }">
                      {{ r.meal?.text }}
                    </div>
                  </div>

                  <svg class="HintIcon" fill="none" height="22" viewBox="0 0 22 22" width="22"><rect x="3" y="3" width="16" height="16" rx="4"></rect><path d="M11 6c-.555 0-1.004.459-1.004 1.025 0 .566.45 1.025 1.004 1.025.555 0 1.005-.46 1.005-1.025C12.005 6.459 11.555 6 11 6ZM10.265 13.831H9V15h4v-1.169h-1.265V9.155H9v1.17h1.265v3.506Z"></path></svg>
                </div>

                <!-- cancellation -->
                <div class="rateRow">
                  <div style="display: flex; gap: 8px;">
                    <span class="rateIcon ic-cancel" :class="{ feature: r.cancellation?.isFeature }" aria-hidden="true"></span>
                    <p class="rowText" :class="{ feature: r.cancellation?.isFeature }">
                      {{ r.cancellation?.text }}
                    </p>
                  </div>

                  <svg class="HintIcon" fill="none" height="22" viewBox="0 0 22 22" width="22"><rect x="3" y="3" width="16" height="16" rx="4"></rect><path d="M11 6c-.555 0-1.004.459-1.004 1.025 0 .566.45 1.025 1.004 1.025.555 0 1.005-.46 1.005-1.025C12.005 6.459 11.555 6 11 6ZM10.265 13.831H9V15h4v-1.169h-1.265V9.155H9v1.17h1.265v3.506Z"></path></svg>
                </div>

                <!-- payment -->
                <div class="rateRow">
                  <div style="display: flex; gap: 8px;">
                    <span class="rateIcon ic-pay" aria-hidden="true"></span>
                    <div>
                      <p class="rowText">
                        {{ r.payment?.title }}
                      </p>
                      <p v-if="r.payment?.subText" class="subText">{{ r.payment.subText }}</p>
                    </div>
                  </div>

                  <svg class="HintIcon" fill="none" height="22" viewBox="0 0 22 22" width="22"><rect x="3" y="3" width="16" height="16" rx="4"></rect><path d="M11 6c-.555 0-1.004.459-1.004 1.025 0 .566.45 1.025 1.004 1.025.555 0 1.005-.46 1.005-1.025C12.005 6.459 11.555 6 11 6ZM10.265 13.831H9V15h4v-1.169h-1.265V9.155H9v1.17h1.265v3.506Z"></path></svg>

                </div>

                <!-- warnings (optional) -->
                <div v-if="r.warnings?.length" class="rateRow">
                  <div style="display: flex; gap: 8px;">
                    <span class="rateIcon ic-bad" aria-hidden="true"></span>
                    <p class="rowText bad">
                      {{ r.warnings[0] }}
                    </p>
                  </div>
                </div>

                </div>

                <!-- price -->
                <div class="priceBlock">
                  <p v-if="r.deal" class="deal">{{ r.deal }}</p>

                  <div class="priceTop">
                    <p class="price">{{ formatRub(r.priceRub) }}</p>
                    <svg class="HintIcon" fill="none" height="22" viewBox="0 0 22 22" width="22"><rect x="3" y="3" width="16" height="16" rx="4"></rect><path d="M11 6c-.555 0-1.004.459-1.004 1.025 0 .566.45 1.025 1.004 1.025.555 0 1.005-.46 1.005-1.025C12.005 6.459 11.555 6 11 6ZM10.265 13.831H9V15h4v-1.169h-1.265V9.155H9v1.17h1.265v3.506Z"></path></svg>
                  </div>

                  <div>
                    <p class="meta">{{ r.guestsAndNightsText }}</p>
                    <p class="taxes">{{ r.taxesText }}</p>
                  </div>
                </div>

                <!-- book -->
                <div class="bookWrap">
                  <div class="roomQty" :data-rate-id="r.id">
                    <button
                      class="roomQtyMinus"
                      type="button"
                      :disabled="qtyFor(r.id) <= 1"
                      @click="changeQty(r.id, -1)"
                    >
                      −
                    </button>
                    <span class="roomQtyValue">{{ qtyFor(r.id) }} {{ roomWord(qtyFor(r.id)) }}</span>
                    <button
                      class="roomQtyPlus"
                      type="button"
                      :disabled="qtyFor(r.id) >= 9"
                      @click="changeQty(r.id, 1)"
                    >
                      +
                    </button>
                  </div>
                  <button class="bookBtn" type="button" @click="onSelectRoom(g, r)">
                    Забронировать
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { HOTEL_EVENTS, useHotelTrackEvent } from '@/hotels/composable/useHotelTrackEvent';
import { useHotelBooking } from '@/hotels/composable/useHotelBooking';
import { pushBenchRoute } from '@/common/benchNavigation';

const { send } = useHotelTrackEvent();
const { setBooking } = useHotelBooking();

type AmenityKey =
  | 'square'
  | 'private_bathroom'
  | 'wifi'
  | 'coffee'
  | 'tv'
  | 'towels';

type RoomAmenity = { key: AmenityKey; label: string };

type MealInfo = { text: string; isFeature?: boolean };
type CancellationInfo = { text: string; isFeature?: boolean };
type PaymentInfo = { title: string; subText?: string };

type RateOption = {
  id: string;
  bedText: string;
  meal: MealInfo;
  cancellation: CancellationInfo;
  payment: PaymentInfo;
  warnings?: string[];
  deal?: string;
  priceRub: number;
  guestsAndNightsText: string;
  taxesText: string;
  bookUrl: string;
};

type RoomGroup = {
  id: string;
  name: string;
  nameAdditional: string;
  alert?: string;
  imageUrl: string;
  imageCount: number;
  amenities: RoomAmenity[];
  rates: RateOption[];
};

type HotelWithRooms = {
  id: string;
  name?: string;
  nights?: number;
  roomOptions?: {
    availabilityTitle?: string;
    galleryCtaText?: string;
    groups: RoomGroup[];
  };
};

const props = defineProps<{
  hotel: HotelWithRooms;
}>();

const route = useRoute();
const router = useRouter();
const qtyByRate = ref<Record<string, number>>({});

function parseLocalISODate(v: unknown): Date | null {
  if (!v || typeof v !== 'string') return null;
  const m = v.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return null;
  const dt = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return Number.isNaN(dt.getTime()) ? null : dt;
}

function parsePositiveInt(v: unknown): number | null {
  if (v == null || v === '') return null;
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? n : null;
}

const nightsFromUrl = computed(() => {
  const ci = parseLocalISODate(route.query.checkIn);
  const co = parseLocalISODate(route.query.checkOut);
  if (!ci || !co) return null;
  const diff = Math.round((co.getTime() - ci.getTime()) / 86400000);
  return diff > 0 ? diff : null;
});

const adultsFromUrl = computed(() => {
  return parsePositiveInt(route.query.guests) ?? parsePositiveInt(route.query.adults);
});

const roomsFromUrl = computed(() => parsePositiveInt(route.query.rooms) ?? 1);

const groups = computed(() => props.hotel.roomOptions?.groups ?? []);

const titleText = computed(() => props.hotel.roomOptions?.availabilityTitle ?? 'Доступные варианты');
const galleryCtaText = computed(() => props.hotel.roomOptions?.galleryCtaText ?? 'фото');

const nightsText = computed(() => nightsFromUrl.value ?? props.hotel.nights ?? 5);
const adultsText = computed(() => adultsFromUrl.value ?? 2);

const roomsHint = computed(() => {
  const n = roomsFromUrl.value;
  if (n <= 1) return '';
  return `, ${n} ${roomWord(n)}`;
});

const nightsSuffix = computed(() => {
  const n = nightsText.value;
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod100 >= 11 && mod100 <= 14) return 'ей';
  if (mod10 === 1) return 'ь';
  if (mod10 >= 2 && mod10 <= 4) return 'и';
  return 'ей';
});

function shownAmenities(amenities: RoomAmenity[]) {
  return amenities.slice(0, 6);
}

function formatRub(v: number) {
  return new Intl.NumberFormat('ru-RU').format(v) + ' ₽';
}

function roomWord(n: number) {
  const n10 = n % 10;
  const n100 = n % 100;
  if (n10 === 1 && n100 !== 11) return 'номер';
  if (n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14)) return 'номера';
  return 'номеров';
}

function qtyFor(rateId: string) {
  return qtyByRate.value[rateId] ?? roomsFromUrl.value;
}

function changeQty(rateId: string, delta: number) {
  const next = Math.min(9, Math.max(1, qtyFor(rateId) + delta));
  qtyByRate.value = { ...qtyByRate.value, [rateId]: next };
}

function onSelectRoom(g: RoomGroup, r: RateOption) {
  const quantity = qtyFor(r.id);
  send(HOTEL_EVENTS.selectRoom, {
    hotelId: props.hotel.id,
    roomGroupId: g.id,
    roomGroupName: g.name,
    rateId: r.id,
    bedText: r.bedText,
    priceRub: r.priceRub,
    quantity,
    roomsCount: quantity,
    bookUrl: r.bookUrl,
  });
  setBooking([{
    hotelId: props.hotel.id,
    hotelName: props.hotel.name ?? '',
    roomGroupId: g.id,
    roomGroupName: g.name,
    roomImageUrl: g.imageUrl,
    rateId: r.id,
    bedText: r.bedText,
    mealText: r.meal?.text ?? '',
    cancellationText: r.cancellation?.text ?? '',
    priceRub: r.priceRub,
    quantity,
  }]);
  pushBenchRoute(router, {
    name: 'bench_hotel_checkout',
    stateId: 'state_hotels_checkout',
    trackId: route.params.track_id,
    query: {
      ...route.query,
      hotelId: props.hotel.id,
      roomGroupId: g.id,
      rateId: r.id,
      qty: String(quantity),
    },
  });
}
</script>

<style scoped>
.roomOptions {
  width: 100%;
}

.shell {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  box-shadow: 0 12px 20px rgba(0,0,0,0.06);
  font-family: PTRootUI, Verdana, sans-serif;
}

.header {
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  padding: 24px;
  background-color: var(--bench-surface-elevated, #fff);
  border-block-end: 1px solid #e5e5e5;
}

.hTitle {
  margin: 0;
  font-size: 24px;
  line-height: 30px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.hDesc {
  margin: 4px 0 0;
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
  margin-block-start: 8px;
}

.filters {
  column-gap: 12px;
  display: flex;
  flex-wrap: wrap;
  row-gap: 6px;
  margin-block-start: 12px;
}

.filterPill {
  height: 32px;
  padding: 0 12px;
  position: relative;
  width: auto;
  border-radius: 12px;
  font-size: 14px;
  border: 1px solid #c8c8c8;
  background: var(--bench-surface-elevated, #fff);
  color: var(--bench-text, #2d3137);
  line-height: 16px;
  font-weight: 600;
  cursor: pointer;
  padding-inline-start: 12px;
  padding-inline-end: 8px;
  padding-right: 28px;
  font-family: PTRootUI, Verdana, sans-serif;
}

.filterPill::after {
  content: "";
  position: absolute;
  right: 10px;
  top: 40%;
  block-size: 8px;
  inline-size: 13px;
  background-repeat: no-repeat;
  background-size: cover;
  block-size: 8px;
  inline-size: 13px;
  pointer-events: none;
  /* chevron */
  background-image: url("/hotels/cdn/dropdownIndicator.c532a644.svg");
}

.groups {
  background-color: var(--bench-surface-elevated, #fff);
  position: relative;
}

.groups:last-child {
  border-bottom-left-radius: 16px !important;
  border-bottom-right-radius: 16px !important;
}

.groupRow {
  display: flex;
  padding: 24px;
  border-block-start: 1px solid #e5e5e5;
}

.roomCard {
  /* background: var(--bench-surface-elevated, #fff); */
  /* border-radius: 16px; */
  /* overflow: hidden; */
  inline-size: 226px;
  padding-block-end: 20px;
}

.roomAlert {
  margin-block-end: 12px;
  padding: 12px;
  border-radius: 16px;
  background: var(--bench-primary-light, rgb(252, 234, 234));
  --shadow-color: #ce2121;
  color: #ce2121;
  font-size: 14px;
  line-height: 18px;
  font-weight: 700;
  font-family: PTRootUI, Verdana, sans-serif;
}

.roomMedia {
  block-size: 132px;
  cursor: pointer;
  display: flex;
  inline-size: 226px;
  margin-block-end: 16px;

  /* margin: 8px; */
  border-radius: 14px;
  overflow: hidden;
  position: relative;
  cursor: pointer;
}

.roomImg {
  display: block;
  width: 100%;
  height: 180px;
  object-fit: cover;
}

.imgCount {
  align-items: center;
  background-color: #464a4f;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  padding: 7px 12px;
  position: absolute;

  bottom: 8px;
  right: 8px;
}

.imgCountText {
  color: #FFF;
  font-size: 14px;
  line-height: 16px;
  padding-inline-start: 20px;
  position: relative;
  font-family: PTRootUI, Verdana, sans-serif;
}

.imgCountText::before {
  top: 0;
  left: 0;

  background-image: url(/hotels/cdn/gallery.e46c495b.svg);
  background-size: contain;
  block-size: 16px;
  content: "";
  inline-size: 16px;
  position: absolute;
}

.camIcon {
  width: 14px;
  height: 14px;
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24'%3E%3Cpath fill='white' d='M9 4l1.5 2H20a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4.5L10 4h-1zM12 9a4 4 0 1 0 0 8a4 4 0 0 0 0-8z'/%3E%3C/svg%3E");
}

.roomInfo {
  /* padding: 6px 12px 12px; */
}

.roomName {
  margin: 0;
  font-size: 20px;
  line-height: 24px;
  font-weight: 800;
  color: var(--bench-text, #2d3137);
  cursor: pointer;
  font-family: PTRootUI, Verdana, sans-serif;
}

.roomSub {
  font-size: 16px;
  line-height: 20px;
  font-weight: 400;
  color: var(--bench-text, #2d3137);
  cursor: pointer;
  font-family: PTRootUI, Verdana, sans-serif;
}

.roomAmenities {
  display: flex;
  flex-wrap: wrap;
}

/* .roomAmenities {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 8px;
} */

.amenityChip {
  background-color: var(--bench-primary-light, #F4f4f4);
  block-size: 28px;
  border-radius: 8px;
  box-sizing: border-box;
  cursor: pointer;
  display: flex;
  flex-shrink: 0;
  margin-block-end: 8px;
  margin-block-start: 0;
  margin-inline-end: 8px;
  margin-inline-start: 0;
  padding: 4px 8px;
}

/* .amenityChip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 999px;
  background: rgba(45,49,55,0.06);
  max-width: 100%;
} */

.amenityIcon {
  width: 16px;
  height: 16px;
  opacity: 0.85;
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
}

/* простые иконки через data-uri, чтобы не зависеть от ассетов */
.ic-square { background-image: url("/hotels/cdn/square.ab57bbbb.svg"); }
.ic-private_bathroom { background-image: url("/hotels/cdn/bath.c1d4458d.svg"); }
.ic-wifi { background-image: url("/hotels/cdn/internet.b8e3abca_a0e44ed8_1.svg"); }
.ic-coffee { background-image: url("/hotels/cdn/tea.fde63893.svg"); }
.ic-tv { background-image: url("/hotels/cdn/tv.3c977110.svg"); }
.ic-towels { background-image: url("/hotels/cdn/towel.960c1496.svg"); }

.rateIcon.ic-meal,
.rateIcon.ic-cancel {
  background-image: none !important;

  -webkit-mask-position: center;
  mask-position: center;

  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;

  -webkit-mask-size: contain;
  mask-size: contain;

  background-color: var(--bench-text, #2d3137); /* дефолт */
}

/* Подставляем конкретные маски */
.rateIcon.ic-meal {
  -webkit-mask-image: url("/hotels/cdn/meal.418dda29.svg");
  mask-image: url("/hotels/cdn/meal.418dda29.svg");
}

.rateIcon.ic-cancel {
  -webkit-mask-image: url("/hotels/cdn/cancellation.398c95fa.svg");
  mask-image: url("/hotels/cdn/cancellation.398c95fa.svg");
}

/* Когда ты добавляешь class feature на span — меняем цвет фона */
.rateIcon.feature {
  background-color: #008900;
}

.amenityLabel {
  color: var(--bench-text, #2d3137);
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  margin-inline-start: 4px;
  max-inline-size: 182px;
  overflow: hidden;
  text-overflow: ellipsis;
  text-wrap: nowrap;
}

.moreLink {
  color: #0e41d2;
  cursor: pointer;
  font-size: 13px;
  line-height: 16px;
  transition: color .16s;
}

.ratesWrap {
  /* background: rgba(45,49,55,0.05);
  border-radius: 16px;
  padding: 12px; */
  /* align-self: flex-start;
  flex: 1;
  min-inline-size: 0;
  position: relative; */
}

/* .ratesWrap::before {
  left: 0;
  border-bottom-right-radius: 8px;
  border-top-right-radius: 8px;
  top: 0;
  bottom: 0;
  transform: scaleX(-1);

  background: linear-gradient(270deg, #0000000d, #0000 38.77%);
  content: "";
  inline-size: 70px;
  opacity: 0;
  pointer-events: none;
  position: absolute;
  transition: opacity .3s;
  z-index: 1;
} */

.ratesContainer {
  overflow-x: scroll;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
  --rate-inline-size: 226px;
  --rate-inline-gap: 12px;

  display: flex;
  gap: 12px;
  margin-inline-start: 12px;
  padding-block-end: 12px;
  padding-block-start: 12px;
  /* pointer-events: none; */
  /* position: absolute; */

  background: var(--bench-primary-light, #F4f4f4);
  border-radius: 8px;
  border-spacing: 12px 0;
}

.rateCard {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  /* align-items: stretch; */
  justify-content: space-between;
}

.rateCard:first-child {
  margin-inline-start: 12px;
}

.rateCard:last-child {
  margin-inline-end: 12px;
}

.rateRow {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding-block-start: 8px;
  padding-block-end: 8px;
  padding-inline-end: 12px;
  padding-inline-start: 12px;
  inline-size: 226px;
  border-bottom: 1px solid #c8c8c8;
}

.rateRow:first-child {
  padding-block-start: 16px !important;
}

.rowLeft {
  display: flex;
  gap: 10px;
  min-width: 0;
  align-items: flex-start;
}

.rateIcon {
  display: inline-block;
  width: 16px !important;
  height: 16px !important;
  margin-top: 2px;
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
  opacity: 0.9;
}

/* rate icons */
.ic-bed { background-image: url("/hotels/cdn/single.d9e132c3.svg"); }
.ic-meal { background-image: url("/hotels/cdn/meal.418dda29.svg"); }
.ic-cancel { background-image: url("/hotels/cdn/cancellation.398c95fa.svg"); }
.ic-pay { background-image: url("/hotels/cdn/payment.2db08cdd.svg"); }
.ic-bad { background-image: url("/hotels/cdn/default-amenity-bad.d0b9fbc4.svg"); opacity: 1; }

.rowText {
  font-size: 14px;
  font-weight: 480;
  line-height: 18px;
  position: relative;
  font-family: PTRootUI, Verdana, sans-serif;
  color: var(--bench-text, #2d3137);
}


.rowText.feature {
  color: #008900;
  font-weight: 700;
}

.ic-cancel.feature {
  color: #008900;
  font-weight: 700;
}

.payText {
  display: grid;
  gap: 2px;
}

.payTitle {
  font-weight: 700;
}

.subText {
  margin: 0;
  font-size: 14px;
  line-height: 18px;
  font-weight: 500;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.rowText.bad {
  color: #d70000;
  font-weight: 700;
}

.hintBtn {
  border: 0;
  background: none;
  padding: 0;
  cursor: pointer;
  flex-shrink: 0;
  opacity: 0.7;
}

.hintIcon {
  width: 18px;
  height: 18px;
  display: inline-block;
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 22 22'%3E%3Crect x='3' y='3' width='16' height='16' rx='4' fill='none' stroke='%232d3137' stroke-width='1.4'/%3E%3Cpath d='M11 6c-.55 0-1 .46-1 1.03c0 .57.45 1.02 1 1.02c.56 0 1-.45 1-1.02C12 6.46 11.56 6 11 6Zm-1.2 7.8H9V15h4v-1.2h-1.2V9.2H9v1.2h.8v3.4Z' fill='%232d3137'/%3E%3C/svg%3E");
}

.HintIcon {
  display: block;
  flex-shrink: 0;
  --icon-color: #868686;
  --bg-color: var(--bench-text, #2d3137);
  --bg-opacity: 0.04;
}

:deep(.HintIcon rect) {
  fill: var(--bg-color);
  opacity: var(--bg-opacity);
  transition: fill .16s ease, opacity .16s ease;
}

:deep(.HintIcon path) {
  fill: var(--icon-color);
  transition: fill .16s ease, opacity .16s ease;
}

.priceBlock {
  padding-block-start: 28px;
  padding-inline-end: 12px;
  padding-inline-start: 12px;

  inline-size: 226px;
  block-size: 109px;

  scroll-margin-inline-start: 12px;
  scroll-snap-align: start;
  display: flex;
  flex-direction: column;
  /* align-items: flex-end; */
  justify-content: flex-end;
  /* gap: 4px; */
}

.deal {
  margin: 0;
  display: inline-block;
  width: fit-content;
  padding: 2px 8px;
  border-radius: 4px;
  background: #53af2433;;
  color: #3f9e10;
  font-size: 13px;
  line-height: 16px;
  font-weight: 800;
  margin-block-end: 6px;
}

.priceTop {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.price {
  margin: 0;
  font-size: 18px;
  line-height: 22px;
  font-weight: 900;
  color: var(--bench-text, #2d3137);
}

.meta {
  margin: 0;
  font-size: 12px;
  line-height: 14px;
  color: rgba(45,49,55,0.75);
  font-weight: 600;
}

.taxes {
  margin: 0;
  font-size: 12px;
  line-height: 16px;
  color: rgba(45,49,55,0.75);
  font-weight: 600;
}

.bookWrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 10px 8px 12px;
}

.roomQty {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.roomQtyMinus,
.roomQtyPlus {
  width: 32px;
  height: 32px;
  border: 1px solid #c8c8c8;
  border-radius: 8px;
  background: var(--bench-surface-elevated, #fff);
  color: var(--bench-text, #2d3137);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  padding: 0;
}

.roomQtyMinus:disabled,
.roomQtyPlus:disabled {
  opacity: 0.35;
  cursor: default;
}

.roomQtyValue {
  font-size: 14px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.bookBtn {
  height: 40px;
  border: 0;
  width: 100%;
  border-radius: 12px;
  background: #0e41d2;
  color: #fff;
  text-decoration: none;
  font-size: 16px;
  line-height: 18px;
  font-weight: 800;
  display: grid;
  place-items: center;
  cursor: pointer;
  font-family: PTRootUI, Verdana, sans-serif;
}

@media (max-width: 1100px) {
  .groupRow {
    grid-template-columns: 1fr;
  }
  .ratesGrid {
    grid-template-columns: repeat(3, 260px);
    overflow-x: auto;
    padding-bottom: 4px;
  }
}
</style>
