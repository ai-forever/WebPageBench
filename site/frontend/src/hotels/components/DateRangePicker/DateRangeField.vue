<template>
  <div ref="anchorRef" class="drf">
    <div class="wrap">
      <FieldShell as="button" clickable class="cell left" type="button" @click="openPopup('start')">
        <template #label>Заезд</template>
        <div class="value">{{ startText }}</div>
      </FieldShell>

      <FieldShell as="button" clickable class="cell right" type="button" @click="openPopup('end')">
        <template #label>Выезд</template>
        <div class="value">{{ endText }}</div>
      </FieldShell>
    </div>

    <Teleport to="body">
      <div v-if="isOpen" class="overlay" @mousedown.self="close">
        <div
          ref="popupRef"
          class="popup"
          :style="{ top: `${pos.top}px`, left: `${pos.left}px` }"
          @mousedown.stop
        >
          <DateRangeCalendar
            :start="start"
            :end="end"
            :min-date="minDate"
            :months-ahead="monthsAhead"
            :active-field="activeField"
            @update:start="setStart"
            @update:end="setEnd"
            @done="close"
          />
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import DateRangeCalendar from './DateRangeCalendar.vue';
import FieldShell from '../Home/FieldShell.vue';
import { HOTEL_EVENTS, toLocalISODate, useHotelTrackEvent } from '@/hotels/composable/useHotelTrackEvent';

const { send } = useHotelTrackEvent();

type ActiveField = 'start' | 'end';

const props = defineProps<{
  start?: Date | string | null;
  end?: Date | string | null;
  minDate?: Date | string | null;
  monthsAhead?: number;
}>();

const emit = defineEmits<{
  (e: 'update:start', v: Date | null): void;
  (e: 'update:end', v: Date | null): void;
}>();

const monthsAhead = computed(() => props.monthsAhead ?? 24);

function toDate(v: Date | string | null | undefined): Date | null {
  if (!v) return null;
  if (v instanceof Date) return isNaN(v.getTime()) ? null : v;
  const d = new Date(v);
  return isNaN(d.getTime()) ? null : d;
}
function startOfDay(d: Date) {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x;
}

const internalStart = ref<Date | null>(toDate(props.start));
const internalEnd = ref<Date | null>(toDate(props.end));

watch(
  () => props.start,
  (v) => (internalStart.value = toDate(v)),
);
watch(
  () => props.end,
  (v) => (internalEnd.value = toDate(v)),
);

const start = computed(() => internalStart.value);
const end = computed(() => internalEnd.value);

const minDate = computed(() => {
  const d = toDate(props.minDate);
  return d ? startOfDay(d) : startOfDay(new Date());
});

const fmt = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' });
const startText = computed(() => (start.value ? fmt.format(start.value) : 'Выберите дату'));
const endText = computed(() => (end.value ? fmt.format(end.value) : 'Выберите дату'));

const isOpen = ref(false);
const activeField = ref<ActiveField>('start');

const anchorRef = ref<HTMLElement | null>(null);
const popupRef = ref<HTMLElement | null>(null);
const pos = ref({ top: 0, left: 0 });

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

function computePos() {
  const a = anchorRef.value;
  const p = popupRef.value;
  if (!a || !p) return;

  const rect = a.getBoundingClientRect();
  const popupRect = p.getBoundingClientRect();

  const margin = 12;
  const top = rect.bottom + 8;

  // по умолчанию слева по полю
  let left = rect.left;

  // clamp в пределах экрана
  const maxLeft = window.innerWidth - popupRect.width - margin;
  left = clamp(left, margin, Math.max(margin, maxLeft));

  pos.value = { top: Math.round(top), left: Math.round(left) };
}

async function openPopup(field: ActiveField) {
  activeField.value = field;
  isOpen.value = true;
  await nextTick();
  computePos();
}

function close() {
  isOpen.value = false;
}

function setStart(d: Date | null) {
  internalStart.value = d;
  emit('update:start', d);
  if (d) {
    send(HOTEL_EVENTS.selectStartDate, { date: toLocalISODate(d) });
  }
}
function setEnd(d: Date | null) {
  internalEnd.value = d;
  emit('update:end', d);
  if (d) {
    send(HOTEL_EVENTS.selectEndDate, { date: toLocalISODate(d) });
  }
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') close();
}
function onResizeScroll() {
  if (isOpen.value) computePos();
}

onMounted(() => {
  window.addEventListener('keydown', onKey);
  window.addEventListener('resize', onResizeScroll);
  window.addEventListener('scroll', onResizeScroll, true);
});
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey);
  window.removeEventListener('resize', onResizeScroll);
  window.removeEventListener('scroll', onResizeScroll, true);
});
</script>

<style scoped>
.drf {
  position: relative;
}

.wrap {
  display: inline-flex;
  inline-size: 100%;
  align-items: flex-start;
}

.cell + .cell {
  margin-inline-start: -1px;
}

.cell {
  flex: 1 1 0;
  min-inline-size: 100px;
  position: relative;

  border-radius: 0 !important;
}

.left {
  border-start-start-radius: 12px !important;
  border-end-start-radius: 12px !important;
}

.right {
  border-start-end-radius: 12px !important;
  border-end-end-radius: 12px !important;
}
.cell:hover,
.cell:focus-within {
  z-index: 2;
}

.value {
  font-size: 16px;
  line-height: 20px;
  font-weight: 500;
  color: var(--bench-text, #2d3137);
  white-space: nowrap;
  font-family: PTRootUI;
}

.overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
}

.popup {
  position: absolute;
  width: 500px;
  height: 500px;
}
</style>
