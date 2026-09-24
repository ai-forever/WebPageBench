import { useRoute } from 'vue-router';
import { useStore } from 'vuex';

import { SEND_EVENT } from '@/store/actions.type';

export const HOTEL_EVENTS = {
  selectCity: 'bench_hotel_select_city',
  selectHotel: 'bench_hotel_select_hotel',
  selectStartDate: 'bench_hotel_select_start_date',
  selectEndDate: 'bench_hotel_select_end_date',
  selectGuests: 'bench_hotel_select_guests',
  selectRoom: 'bench_hotel_select_room',
} as const;

export function toLocalISODate(d: Date): string {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  const yyyy = x.getFullYear();
  const mm = String(x.getMonth() + 1).padStart(2, '0');
  const dd = String(x.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

export function useHotelTrackEvent() {
  const route = useRoute();
  const store = useStore();

  function send(eventName: string, payload: Record<string, unknown>) {
    const trackId = route.params.track_id;
    if (!trackId || typeof trackId !== 'string') return;

    const body = {
      ...payload,
      state_id: route.params.state_id,
    };

    void store.dispatch(SEND_EVENT, {
      trackId,
      eventName,
      eventData: JSON.stringify(body),
    });
  }

  return { send };
}
