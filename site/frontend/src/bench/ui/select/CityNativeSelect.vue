<template>
  <FieldShell>
    <template #label>Направление</template>
    <select
      class="native-select"
      :value="selectedId"
      @change="onChange"
    >
      <option value="" disabled>Выберите город</option>
      <option
        v-for="opt in options"
        :key="opt.cityId"
        :value="opt.cityId"
      >
        {{ opt.cityName }}, {{ opt.countryName }}
      </option>
    </select>
  </FieldShell>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import FieldShell from '@/hotels/components/Home/FieldShell.vue';
import type { DestinationOption } from '@/hotels/services/searchDataset';
import { HOTEL_EVENTS, useHotelTrackEvent } from '@/hotels/composable/useHotelTrackEvent';

const { send } = useHotelTrackEvent();

const props = defineProps<{
  modelValue: DestinationOption | null;
  options: DestinationOption[];
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', v: DestinationOption | null): void;
}>();

const selectedId = computed(() => props.modelValue?.cityId ?? '');

function onChange(e: Event) {
  const id = (e.target as HTMLSelectElement).value;
  const opt = props.options.find((o) => o.cityId === id) || null;
  if (opt) {
    send(HOTEL_EVENTS.selectCity, {
      cityId: opt.cityId,
      label: opt.label,
      cityName: opt.cityName,
      countryName: opt.countryName,
    });
  }
  emit('update:modelValue', opt);
}
</script>

<style scoped>
.native-select {
  inline-size: 100%;
  border: none;
  outline: none;
  font-size: 16px;
  font-weight: 500;
  color: #2d3137;
  background: transparent;
  cursor: pointer;
  font-family: PTRootUI, sans-serif;
  padding-block: 2px;
}
</style>
