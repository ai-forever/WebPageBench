<template>
  <div ref="anchorRef" class="singlePopup">
    <FieldShell as="button" clickable type="button" class="singleCell" @click="toggle">
      <template #label>Даты поездки</template>
      <div class="value">{{ rangeText }}</div>
    </FieldShell>

    <Teleport to="body">
      <div v-if="isOpen" class="overlay" @mousedown.self="close">
        <div ref="popupRef" class="popup" :style="{ top: `${pos.top}px`, left: `${pos.left}px` }" @mousedown.stop>
          <DateRangeCalendar
            :start="start"
            :end="end"
            :min-date="minDate"
            :months-ahead="monthsAhead"
            active-field="start"
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
import DateRangeCalendar from '@/hotels/components/DateRangePicker/DateRangeCalendar.vue';
import FieldShell from '@/hotels/components/Home/FieldShell.vue';
import { HOTEL_EVENTS, toLocalISODate, useHotelTrackEvent } from '@/hotels/composable/useHotelTrackEvent';

const { send } = useHotelTrackEvent();

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

function toDate(v: Date | string | null | undefined): Date | null {
  if (!v) return null;
  if (v instanceof Date) return isNaN(v.getTime()) ? null : v;
  const d = new Date(v);
  return isNaN(d.getTime()) ? null : d;
}

const internalStart = ref<Date | null>(toDate(props.start));
const internalEnd = ref<Date | null>(toDate(props.end));
watch(() => props.start, (v) => { internalStart.value = toDate(v); });
watch(() => props.end, (v) => { internalEnd.value = toDate(v); });

const start = computed(() => internalStart.value);
const end = computed(() => internalEnd.value);
const monthsAhead = computed(() => props.monthsAhead ?? 24);
const minDate = computed(() => toDate(props.minDate) || new Date());

const fmt = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' });
const rangeText = computed(() => {
  if (start.value && end.value) {
    return `${fmt.format(start.value)} — ${fmt.format(end.value)}`;
  }
  if (start.value) return `${fmt.format(start.value)} — …`;
  return 'Выберите даты';
});

const isOpen = ref(false);
const anchorRef = ref<HTMLElement | null>(null);
const popupRef = ref<HTMLElement | null>(null);
const pos = ref({ top: 0, left: 0 });

function computePos() {
  const a = anchorRef.value;
  const p = popupRef.value;
  if (!a || !p) return;
  const rect = a.getBoundingClientRect();
  const popupWidth = Math.min(500, window.innerWidth - 24);
  const popupHeight = Math.min(500, window.innerHeight - 24);
  let left = Math.max(12, rect.left);
  if (left + popupWidth > window.innerWidth - 12) {
    left = Math.max(12, window.innerWidth - popupWidth - 12);
  }
  let top = rect.bottom + 8;
  if (top + popupHeight > window.innerHeight - 12) {
    top = Math.max(12, rect.top - popupHeight - 8);
  }
  pos.value = { top, left };
}

async function toggle() {
  isOpen.value = !isOpen.value;
  if (isOpen.value) {
    await nextTick();
    computePos();
  }
}

function close() {
  isOpen.value = false;
}

function setStart(d: Date | null) {
  internalStart.value = d;
  emit('update:start', d);
  if (d) send(HOTEL_EVENTS.selectStartDate, { date: toLocalISODate(d) });
}

function setEnd(d: Date | null) {
  internalEnd.value = d;
  emit('update:end', d);
  if (d) send(HOTEL_EVENTS.selectEndDate, { date: toLocalISODate(d) });
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') close();
}

onMounted(() => window.addEventListener('keydown', onKey));
onBeforeUnmount(() => window.removeEventListener('keydown', onKey));
</script>

<style scoped>
.singlePopup {
  inline-size: 100%;
}

.singleCell {
  border-radius: 12px;
  inline-size: 100%;
}

.value {
  font-size: 16px;
  font-weight: 500;
  color: #2d3137;
}

.overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
}

.popup {
  position: absolute;
  inline-size: min(500px, calc(100vw - 24px));
  max-block-size: min(500px, calc(100vh - 24px));
  overflow: auto;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
}
</style>
