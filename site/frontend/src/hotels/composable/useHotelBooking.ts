import { computed, ref } from 'vue';

export type HotelBookingLine = {
  hotelId: string;
  hotelName: string;
  roomGroupId: string;
  roomGroupName: string;
  roomImageUrl?: string;
  rateId: string;
  bedText: string;
  mealText: string;
  cancellationText: string;
  priceRub: number;
  quantity: number;
};

const lines = ref<HotelBookingLine[]>([]);

export function useHotelBooking() {
  const totalRub = computed(() =>
    lines.value.reduce((sum, line) => sum + line.priceRub * line.quantity, 0),
  );
  const roomsTotal = computed(() =>
    lines.value.reduce((sum, line) => sum + line.quantity, 0),
  );

  function setBooking(next: HotelBookingLine[]) {
    lines.value = next;
  }

  function clear() {
    lines.value = [];
  }

  return { lines, totalRub, roomsTotal, setBooking, clear };
}
