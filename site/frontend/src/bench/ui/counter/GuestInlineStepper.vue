<template>
  <FieldShell class="inline-guests">
    <template #label>Гости</template>
    <div class="guests-row">
      <button type="button" class="step-btn" :disabled="adults <= 1" @click="dec">−</button>
      <span class="count">{{ adults }}</span>
      <button type="button" class="step-btn" :disabled="adults >= 6" @click="inc">+</button>
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
const adults = ref(Math.min(6, Math.max(1, guestsCount.value)));

function emitGuests() {
  setSingleRoomAdults(adults.value);
  send(HOTEL_EVENTS.selectGuests, {
    rooms: [{ adults: adults.value, kids: [] }],
    roomsCount: 1,
    guestsCount: adults.value,
  });
}

function inc() {
  adults.value += 1;
  emitGuests();
}

function dec() {
  if (adults.value > 1) {
    adults.value -= 1;
    emitGuests();
  }
}
</script>

<style scoped>
.inline-guests {
  border-radius: 12px;
}

.guests-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.step-btn {
  inline-size: 28px;
  block-size: 28px;
  border: 1px solid #c4c4c4;
  border-radius: 8px;
  background: #fff;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  padding: 0;
}

.step-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.count {
  font-size: 16px;
  font-weight: 600;
  min-inline-size: 20px;
  text-align: center;
}
</style>
