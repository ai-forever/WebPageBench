import { computed, ref } from 'vue';

export type GuestRoom = {
  id: string;
  adults: number;
  kids: number[];
};

function newRoomId() {
  return typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `room-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function createGuestRoom(adults = 1): GuestRoom {
  return { id: newRoomId(), adults, kids: [] };
}

const rooms = ref<GuestRoom[]>([createGuestRoom(1)]);

export function useHotelGuests() {
  const roomsCount = computed(() => rooms.value.length);
  const guestsCount = computed(() =>
    rooms.value.reduce((sum, room) => sum + room.adults + room.kids.length, 0),
  );
  const childrenCount = computed(() =>
    rooms.value.reduce((sum, room) => sum + room.kids.length, 0),
  );

  function setSingleRoomAdults(adults: number) {
    const n = Math.max(1, Math.min(9, adults));
    rooms.value = [createGuestRoom(n)];
  }

  return {
    rooms,
    roomsCount,
    guestsCount,
    childrenCount,
    setSingleRoomAdults,
  };
}
