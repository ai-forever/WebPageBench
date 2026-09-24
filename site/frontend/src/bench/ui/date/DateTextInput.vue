<template>
  <div class="bench-date-text">
    <FieldShell class="cell">
      <template #label>Заезд</template>
      <input
        v-model="startText"
        class="date-text-input"
        type="text"
        inputmode="numeric"
        placeholder="ДД.ММ.ГГГГ"
        @input="commitStart"
        @blur="commitStart"
        @keydown.enter="commitStart"
      />
    </FieldShell>
    <FieldShell class="cell">
      <template #label>Выезд</template>
      <input
        v-model="endText"
        class="date-text-input"
        type="text"
        inputmode="numeric"
        placeholder="ДД.ММ.ГГГГ"
        @input="commitEnd"
        @blur="commitEnd"
        @keydown.enter="commitEnd"
      />
    </FieldShell>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import FieldShell from '@/hotels/components/Home/FieldShell.vue';
import { HOTEL_EVENTS, toLocalISODate, useHotelTrackEvent } from '@/hotels/composable/useHotelTrackEvent';

const { send } = useHotelTrackEvent();

const props = defineProps<{
  start?: Date | string | null;
  end?: Date | string | null;
}>();

const emit = defineEmits<{
  (e: 'update:start', v: Date | null): void;
  (e: 'update:end', v: Date | null): void;
}>();

function formatRu(d: Date | null): string {
  if (!d) return '';
  const dd = String(d.getDate()).padStart(2, '0');
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  return `${dd}.${mm}.${d.getFullYear()}`;
}

function fromParts(year: string, month: string, day: string): Date | null {
  const y = Number(year);
  const mo = Number(month);
  const d = Number(day);
  if (!Number.isFinite(y) || y < 2000 || mo < 1 || mo > 12 || d < 1 || d > 31) return null;
  const dt = new Date(y, mo - 1, d);
  dt.setFullYear(y);
  if (dt.getFullYear() !== y || dt.getMonth() !== mo - 1 || dt.getDate() !== d) return null;
  return dt;
}

function parseRu(text: string): Date | null {
  const s = text.trim();
  let m = s.match(/^(\d{1,2})[./](\d{1,2})[./](\d{4})$/);
  if (m) return fromParts(m[3], m[2], m[1]);
  m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) return fromParts(m[1], m[2], m[3]);
  m = s.match(/^(\d{2})(\d{2})(\d{4})$/);
  if (m) return fromParts(m[3], m[2], m[1]);
  return null;
}

function toDate(v: Date | string | null | undefined): Date | null {
  if (!v) return null;
  if (v instanceof Date) return isNaN(v.getTime()) ? null : v;
  return parseRu(v);
}

const startText = ref(formatRu(toDate(props.start)));
const endText = ref(formatRu(toDate(props.end)));
const lastStartIso = ref('');
const lastEndIso = ref('');

watch(() => props.start, (v) => { startText.value = formatRu(toDate(v)); });
watch(() => props.end, (v) => { endText.value = formatRu(toDate(v)); });

function commitStart() {
  const d = parseRu(startText.value);
  if (!d) return;
  const iso = toLocalISODate(d);
  if (lastStartIso.value === iso) return;
  lastStartIso.value = iso;
  emit('update:start', d);
  send(HOTEL_EVENTS.selectStartDate, { date: iso });
}

function commitEnd() {
  const d = parseRu(endText.value);
  if (!d) return;
  const iso = toLocalISODate(d);
  if (lastEndIso.value === iso) return;
  lastEndIso.value = iso;
  emit('update:end', d);
  send(HOTEL_EVENTS.selectEndDate, { date: iso });
}
</script>

<style scoped>
.bench-date-text {
  display: inline-flex;
  inline-size: 100%;
  gap: 0;
}

.cell {
  flex: 1 1 0;
  min-inline-size: 100px;
}

.cell:first-child {
  border-start-start-radius: 12px;
  border-end-start-radius: 12px;
}

.cell:last-child {
  border-start-end-radius: 12px;
  border-end-end-radius: 12px;
}

.date-text-input {
  inline-size: 100%;
  border: none;
  outline: none;
  font-size: 16px;
  font-weight: 500;
  color: #2d3137;
  background: transparent;
  font-family: PTRootUI, sans-serif;
}
</style>
