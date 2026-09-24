<template>
  <div class="card">
    <div class="body">
      <div class="cols">
        <!-- Check-in -->
        <div class="col">
          <p class="label">Заезд</p>
          <div class="row">
            <button class="link" type="button" @click="onChange">
              {{ checkInText }}
            </button>
            <p class="time">с {{ checkInTime }}</p>
          </div>
        </div>

        <!-- Check-out -->
        <div class="col">
          <p class="label">Выезд</p>
          <div class="row">
            <button class="link" type="button" @click="onChange">
              {{ checkOutText }}
            </button>
            <p class="time">до {{ checkOutTime }}</p>
          </div>
        </div>
      </div>

      <!-- большая кнопка справа (как на скрине) -->
      <button class="btnLight btnXs btnWideRight" type="button" @click="onChange">
        Изменить
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const props = withDefaults(defineProps<{
  /** Если true — даты/время читаем из URL (?checkIn=YYYY-MM-DD&checkOut=YYYY-MM-DD) */
  fromUrl?: boolean;

  /** Можно передать явно */
  checkIn?: Date | string | null;
  checkOut?: Date | string | null;

  /** Время заезда/выезда */
  checkInTime?: string;   // "14:00"
  checkOutTime?: string;  // "11:00"
}>(), {
  fromUrl: true,
  checkIn: null,
  checkOut: null,
  checkInTime: '14:00',
  checkOutTime: '11:00',
});

const emit = defineEmits<{
  (e: 'change'): void;
}>();

const route = useRoute();

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

function toDate(v: unknown): Date | null {
  if (!v) return null;
  if (v instanceof Date) return Number.isNaN(v.getTime()) ? null : v;
  if (typeof v === 'string') return parseLocalISODate(v) ?? new Date(v);
  return null;
}

const checkInDate = computed(() => {
  if (props.fromUrl) return parseLocalISODate(route.query.checkIn);
  return toDate(props.checkIn);
});

const checkOutDate = computed(() => {
  if (props.fromUrl) return parseLocalISODate(route.query.checkOut);
  return toDate(props.checkOut);
});

function fmtDate(d: Date) {
  // "09 февр 2026, пн" (как на скрине)
  const day = new Intl.DateTimeFormat('ru-RU', { day: '2-digit' }).format(d);
  const mon = new Intl.DateTimeFormat('ru-RU', { month: 'short' }).format(d).replace('.', '');
  const year = new Intl.DateTimeFormat('ru-RU', { year: 'numeric' }).format(d);
  const wk = new Intl.DateTimeFormat('ru-RU', { weekday: 'short' }).format(d).replace('.', '');
  return `${day} ${mon} ${year}, ${wk}`;
}

const checkInText = computed(() => checkInDate.value ? fmtDate(checkInDate.value) : 'Дата не указана');
const checkOutText = computed(() => checkOutDate.value ? fmtDate(checkOutDate.value) : 'Дата не указана');

const checkInTime = computed(() => props.checkInTime || '14:00');
const checkOutTime = computed(() => props.checkOutTime || '11:00');

function onChange() {
  emit('change');
}
</script>

<style scoped>
.card {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  box-shadow: 0 12px 20px rgba(0,0,0,0.06);
  padding: 16px 24px;
  font-family: PTRootUI, Verdana, sans-serif;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.title {
  margin: 0;
  font-size: 16px;
  line-height: 22px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
}

.body {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.cols {
  display: flex;
  gap: 48px;
  min-inline-size: 0;

  font-size: 16px;
  font-weight: 700;
  line-height: 20px;
}

.col {
  min-inline-size: 0;
}

.label {
  line-height: 18px;
  margin-block-end: 4px;
  font-size: 16px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-inline-size: 0;
}

.link {
  border: 0;
  background: none;
  padding: 0;
  cursor: pointer;
  color: #0e41d2;
  font-size: 16px;
  line-height: 20px;
  font-weight: 700;
  font-family: PTRootUI, Verdana, sans-serif;
  text-align: left;
  white-space: nowrap;
}

.time {
  margin: 0;
  color: #868686;
  font-size: 16px;
  line-height: 20px;
  font-weight: 600;
  white-space: nowrap;
}

/* button styles (light, like Отели) */
.btnLight {
  border: 1px solid transparent;
  background-color: var(--bench-primary-light, rgb(230, 235, 245));
  color: var(--bench-primary, #0e41d2);
  border-radius: 12px;
  cursor: pointer;
  border: 1px solid #0000;
  font-family: PTRootUI, Verdana, sans-serif;
  font-weight: 600;
  font-size: 16px;
  line-height: 20px;
  block-size: 36px !important;
  padding: 0 8px;
  transition: background-color .16s ease, box-shadow .16s ease;
}

.btnLight:hover {
  /* box-shadow: 0 6px 16px rgba(14, 65, 210, 0.14); */
}

.btnXxs {
  height: 28px;
  padding: 0 10px;
  font-size: 12px;
  line-height: 16px;
}

.btnXs {
  height: 36px;
  padding: 0 14px;
  font-size: 16px;
  line-height: 18px;
}

.btnWideRight {
  flex-shrink: 0;
  min-inline-size: 120px;
}

@media (max-width: 900px) {
  .body {
    flex-direction: column;
    align-items: stretch;
  }
  .cols {
    justify-content: space-between;
    gap: 16px;
  }
  .link {
    font-size: 18px;
    line-height: 24px;
  }
  .time {
    font-size: 14px;
    line-height: 18px;
  }
  .btnWideRight {
    min-inline-size: 100%;
  }
}
</style>
