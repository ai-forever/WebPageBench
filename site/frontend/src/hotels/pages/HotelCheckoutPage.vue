<template>
  <div class="page hotel-checkout">
    <div class="container">
      <div class="breadcrumbs">
        <button class="crumbLink" type="button" @click="goBack">
          Назад к отелю
        </button>
      </div>

      <div v-if="loading" class="state">Загрузка…</div>
      <div v-else-if="error" class="state err">Ошибка: {{ error }}</div>
      <div v-else-if="!hotel || !bookingLines.length" class="state err">
        Не удалось собрать бронь. Вернитесь к отелю и выберите номер.
      </div>

      <template v-else-if="confirmed">
        <section class="card bookingSuccess">
          <h1 class="checkout-title">Бронь подтверждена</h1>
          <p class="successLead">{{ hotel.name }} · {{ roomsWord }}</p>
          <p class="bookingNumber">Номер брони: {{ bookingNumber }}</p>
          <p class="metaLine">{{ datesText }}</p>
          <p class="metaLine">{{ guestsText }}</p>
          <p class="successPrice">{{ rubleCurrency(totalRub) }}</p>
          <button class="bookBtn confirmBookBtn" type="button" @click="goBack">
            К отелю
          </button>
        </section>
      </template>

      <template v-else>
        <h1 class="checkout-title">Бронирование</h1>

        <section class="card">
          <h2 class="cardTitle">{{ hotel.name }}</h2>
          <p class="metaLine">{{ datesText }}</p>
          <p class="metaLine">{{ guestsText }}</p>

          <article
            v-for="(line, idx) in bookingLines"
            :key="line.rateId + '-' + idx"
            class="roomLine"
          >
            <img
              v-if="line.roomImageUrl"
              class="roomImg"
              :src="line.roomImageUrl"
              :alt="line.roomGroupName"
            />
            <div class="roomInfo">
              <p class="roomName">{{ line.roomGroupName }}</p>
              <p class="roomMeta">{{ line.bedText }}</p>
              <p class="roomMeta">{{ line.mealText }}</p>
              <p class="roomMeta">{{ line.cancellationText }}</p>
              <p class="roomQtySummary">{{ line.quantity }} {{ roomWord(line.quantity) }}</p>
            </div>
            <div class="roomPrice">
              <p class="price">{{ rubleCurrency(line.priceRub * line.quantity) }}</p>
              <p v-if="line.quantity > 1" class="priceHint">
                {{ rubleCurrency(line.priceRub) }} × {{ line.quantity }}
              </p>
            </div>
          </article>
        </section>

        <section class="card">
          <h2 class="cardTitle">Гость</h2>
          <label class="field">
            <span>Имя и фамилия</span>
            <input v-model="guestName" class="guestInput" type="text" autocomplete="name" />
          </label>
          <label class="field">
            <span>Email</span>
            <input v-model="guestEmail" class="guestInput" type="email" autocomplete="email" />
          </label>
          <label class="field">
            <span>Телефон</span>
            <input v-model="guestPhone" class="guestInput" type="tel" autocomplete="tel" />
          </label>
        </section>

        <section class="card summary">
          <div class="sumRow">
            <span>Итого</span>
            <strong>{{ rubleCurrency(totalRub) }}</strong>
          </div>
          <button class="bookBtn confirmBookBtn" type="button" @click="confirmBooking">
            Подтвердить бронь
          </button>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useStore } from 'vuex';

import { useSearchDataset } from '../composable/useSearchDataset';
import { useHotelBooking, type HotelBookingLine } from '../composable/useHotelBooking';
import { rubleCurrency } from '../utils/rubleCurrency';
import { pushBenchRoute } from '@/common/benchNavigation';
import { getBenchPersonalInfo } from '@/common/benchPersonalInfo.js';

const route = useRoute();
const router = useRouter();
const store = useStore();
const booking = useHotelBooking();

const datasetId = computed(() => String(route.query.dataset ?? 'ch'));
const hotelId = computed(() => String(route.query.hotelId ?? ''));
const ds = useSearchDataset(datasetId);
const loading = computed(() => ds.loading.value);
const error = computed(() => ds.error.value);

const hotel = computed(() => {
  const all = ds.dataset.value?.hotels ?? [];
  const id = hotelId.value;
  if (!id) return null;
  return all.find((h: any) => h.id === id) ?? null;
});

const confirmed = ref(false);
const bookingNumber = ref('');

const guestName = ref('');
const guestEmail = ref('');
const guestPhone = ref('');

watch(
  () => store.getters.trackConfig,
  (cfg) => {
    const personal = getBenchPersonalInfo(cfg);
    const login = cfg?.test_data?.login_data || {};
    if (!guestName.value && personal.fullName && personal.fullName !== 'Пользователь') {
      guestName.value = personal.fullName;
    }
    if (!guestEmail.value) {
      guestEmail.value = personal.email || login.email || login.login || '';
    }
    if (!guestPhone.value) {
      guestPhone.value = personal.phone || login.phone || '';
    }
  },
  { immediate: true },
);

function pluralRu(n: number, one: string, few: string, many: string) {
  const n10 = n % 10;
  const n100 = n % 100;
  if (n10 === 1 && n100 !== 11) return one;
  if (n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14)) return few;
  return many;
}

function roomWord(n: number) {
  return pluralRu(n, 'номер', 'номера', 'номеров');
}

function parseQty(v: unknown) {
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? Math.min(9, Math.round(n)) : 1;
}

const reconstructedLines = computed<HotelBookingLine[]>(() => {
  const h = hotel.value as any;
  if (!h) return [];
  const groupId = String(route.query.roomGroupId ?? '');
  const rateId = String(route.query.rateId ?? '');
  const qty = parseQty(route.query.qty);
  const groups = h.roomOptions?.groups ?? [];
  const group = groups.find((g: any) => g.id === groupId) || groups[0];
  if (!group) return [];
  const rate = (group.rates ?? []).find((r: any) => r.id === rateId) || group.rates?.[0];
  if (!rate) return [];
  return [{
    hotelId: h.id,
    hotelName: h.name,
    roomGroupId: group.id,
    roomGroupName: group.name,
    roomImageUrl: group.imageUrl,
    rateId: rate.id,
    bedText: rate.bedText,
    mealText: rate.meal?.text ?? '',
    cancellationText: rate.cancellation?.text ?? '',
    priceRub: Number(rate.priceRub) || 0,
    quantity: qty,
  }];
});

const bookingLines = computed<HotelBookingLine[]>(() => {
  if (booking.lines.value.length) return booking.lines.value;
  return reconstructedLines.value;
});

const totalRub = computed(() =>
  bookingLines.value.reduce((sum, line) => sum + line.priceRub * line.quantity, 0),
);

const roomsCount = computed(() =>
  bookingLines.value.reduce((sum, line) => sum + line.quantity, 0),
);

const roomsWord = computed(() => `${roomsCount.value} ${roomWord(roomsCount.value)}`);

function formatRu(d: Date) {
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }).format(d);
}

function parseLocalISODate(v: unknown): Date | null {
  if (!v || typeof v !== 'string') return null;
  const m = v.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return null;
  const dt = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return Number.isNaN(dt.getTime()) ? null : dt;
}

const datesText = computed(() => {
  const ci = parseLocalISODate(route.query.checkIn);
  const co = parseLocalISODate(route.query.checkOut);
  if (!ci || !co) return 'Даты не указаны';
  return `${formatRu(ci)} — ${formatRu(co)}`;
});

const guestsText = computed(() => {
  const guests = Number(route.query.guests ?? 2);
  const rooms = roomsCount.value || Number(route.query.rooms ?? 1);
  const gWord = pluralRu(guests, 'гость', 'гостя', 'гостей');
  return `${rooms} ${roomWord(rooms)}, ${guests} ${gWord}`;
});

function confirmBooking() {
  const suffix = String(route.query.rateId || hotelId.value || 'room').slice(-6).toUpperCase();
  bookingNumber.value = `HTL-${Date.now().toString(36).toUpperCase()}-${suffix}`;
  confirmed.value = true;
}

function goBack() {
  const q = { ...route.query };
  delete (q as any).rateId;
  delete (q as any).roomGroupId;
  delete (q as any).qty;

  pushBenchRoute(router, {
    name: 'bench_hotel_hotel',
    stateId: 'state_hotels_hotel',
    trackId: route.params.track_id,
    query: q,
  });
}
</script>

<style scoped>
.page {
  background: var(--bench-surface, #f4f4f4);
  min-height: 100vh;
}

.container {
  max-width: 760px;
  margin: 0 auto;
  font-family: PTRootUI, Verdana, sans-serif;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 12px 0 32px;
}

.breadcrumbs {
  display: flex;
}

.crumbLink {
  border: 0;
  background: var(--bench-surface-elevated, #fff);
  padding: 8px 12px;
  line-height: 18px;
  cursor: pointer;
  color: var(--bench-text, #2d3137);
  font-weight: 500;
  font-size: 16px;
  display: flex;
  border-radius: 12px;
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
  margin-inline-end: 4px;
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

.checkout-title {
  margin: 0;
  font-size: 24px;
  line-height: 30px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
}

.card {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.06);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cardTitle {
  margin: 0;
  font-size: 18px;
  line-height: 24px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
}

.metaLine {
  margin: 0;
  font-size: 14px;
  color: rgba(45, 49, 55, 0.75);
}

.roomLine {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: start;
  padding-top: 12px;
  border-top: 1px solid #e5e5e5;
}

.roomImg {
  width: 96px;
  height: 72px;
  object-fit: cover;
  border-radius: 12px;
}

.roomName {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
}

.roomMeta,
.roomQtySummary,
.priceHint {
  margin: 4px 0 0;
  font-size: 13px;
  color: rgba(45, 49, 55, 0.7);
}

.price {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: var(--bench-text, #2d3137);
  text-align: right;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(45, 49, 55, 0.7);
}

.guestInput {
  height: 44px;
  border: 1px solid #c8c8c8;
  border-radius: 12px;
  padding: 0 12px;
  font-size: 16px;
  font-family: PTRootUI, Verdana, sans-serif;
  color: var(--bench-text, #2d3137);
  background: var(--bench-surface-elevated, #fff);
}

.sumRow {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 18px;
  color: var(--bench-text, #2d3137);
}

.bookBtn {
  margin-top: 8px;
  height: 48px;
  border: 0;
  border-radius: 12px;
  background: #0e41d2;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  font-family: PTRootUI, Verdana, sans-serif;
}

.successLead,
.bookingNumber {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--bench-text, #2d3137);
}

.successPrice {
  margin: 8px 0 0;
  font-size: 22px;
  font-weight: 800;
  color: var(--bench-text, #2d3137);
}
</style>
