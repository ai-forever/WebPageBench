<template>
  <FieldShell>
    <template #label>Гости</template>
    <select class="compact-select" :value="guests" @change="onChange">
      <option v-for="n in 6" :key="n" :value="n">{{ n }} {{ guestLabel(n) }}</option>
    </select>
  </FieldShell>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import FieldShell from '@/hotels/components/Home/FieldShell.vue';
import { HOTEL_EVENTS, useHotelTrackEvent } from '@/hotels/composable/useHotelTrackEvent';
import { useHotelGuests } from '@/hotels/composable/useHotelGuests';

const { send } = useHotelTrackEvent();
const { guestsCount, setSingleRoomAdults } = useHotelGuests();
const guests = ref(Math.min(6, Math.max(1, guestsCount.value)));

function guestLabel(n: number) {
  if (n === 1) return 'гость';
  if (n >= 2 && n <= 4) return 'гостя';
  return 'гостей';
}

function onChange(e: Event) {
  const n = Number((e.target as HTMLSelectElement).value);
  guests.value = n;
  setSingleRoomAdults(n);
  send(HOTEL_EVENTS.selectGuests, {
    rooms: [{ adults: n, kids: [] }],
    roomsCount: 1,
    guestsCount: n,
  });
}
</script>

<style scoped>
.compact-select {
  inline-size: 100%;
  border: none;
  outline: none;
  font-size: 16px;
  font-weight: 500;
  background: transparent;
  cursor: pointer;
}
</style>
