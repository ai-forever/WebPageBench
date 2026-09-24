<template>
  <FieldShell auto-height>
    <template #label>Гости</template>
    <div class="pillRow">
      <button
        v-for="n in maxGuests"
        :key="n"
        type="button"
        class="pill"
        :class="{ active: selected === n }"
        @click="pick(n)"
      >
        {{ n }}
      </button>
    </div>
  </FieldShell>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import FieldShell from '@/hotels/components/Home/FieldShell.vue';
import { HOTEL_EVENTS, useHotelTrackEvent } from '@/hotels/composable/useHotelTrackEvent';
import { useHotelGuests } from '@/hotels/composable/useHotelGuests';

const { send } = useHotelTrackEvent();
const { guestsCount, setSingleRoomAdults } = useHotelGuests();
const maxGuests = 6;
const selected = ref(Math.min(maxGuests, Math.max(1, guestsCount.value)));

function pick(n: number) {
  selected.value = n;
  setSingleRoomAdults(n);
  send(HOTEL_EVENTS.selectGuests, {
    rooms: [{ adults: n, kids: [] }],
    roomsCount: 1,
    guestsCount: n,
  });
}
</script>

<style scoped>
.pillRow {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pill {
  min-inline-size: 32px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  line-height: 1;
}

.pill.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}
</style>
