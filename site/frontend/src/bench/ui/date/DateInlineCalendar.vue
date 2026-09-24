<template>
  <div class="bench-date-inline">
    <div class="inline-head">Даты поездки</div>
    <div class="inline-calendar">
      <DateRangeCalendar
        :start="startDate"
        :end="endDate"
        :min-date="minDateObj"
        :months-ahead="24"
        active-field="start"
        @update:start="onStart"
        @update:end="onEnd"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import DateRangeCalendar from '@/hotels/components/DateRangePicker/DateRangeCalendar.vue';
import { HOTEL_EVENTS, toLocalISODate, useHotelTrackEvent } from '@/hotels/composable/useHotelTrackEvent';

const { send } = useHotelTrackEvent();

const props = defineProps<{
  start?: Date | string | null;
  end?: Date | string | null;
  minDate?: Date | string | null;
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

const startDate = ref<Date | null>(toDate(props.start));
const endDate = ref<Date | null>(toDate(props.end));

watch(() => props.start, (v) => { startDate.value = toDate(v); });
watch(() => props.end, (v) => { endDate.value = toDate(v); });

const minDateObj = computed(() => {
  const d = toDate(props.minDate);
  return d || new Date();
});

function onStart(d: Date | null) {
  startDate.value = d;
  emit('update:start', d);
  if (d) send(HOTEL_EVENTS.selectStartDate, { date: toLocalISODate(d) });
}

function onEnd(d: Date | null) {
  endDate.value = d;
  emit('update:end', d);
  if (d) send(HOTEL_EVENTS.selectEndDate, { date: toLocalISODate(d) });
}
</script>

<style scoped>
.bench-date-inline {
  inline-size: 100%;
  max-inline-size: 100%;
  box-sizing: border-box;
}

.inline-head {
  font-size: 12px;
  line-height: 16px;
  color: rgba(45, 49, 55, 0.85);
  margin-block-end: 6px;
}

.inline-calendar {
  border: 1px solid rgba(41, 47, 55, 0.12);
  border-radius: 12px;
  background: #fff;
  padding: 8px;
  height: min(360px, 55vh);
  min-block-size: 280px;
  overflow: hidden;
  box-sizing: border-box;
}
</style>
