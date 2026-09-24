<template>
  <div class="wrapper">
    <article>
      <div class="header">
        <p class="title">Популярные направления</p>
      </div>

      <section>
        <DestinationCard
          v-for="d in visibleDestinations"
          :key="d.cityId"
          :img-src="d.imgSrc"
          :img-alt="d.title"
          :country="d.country"
          :title="d.title"
          @select="openDestination(d)"
        />
      </section>

      <button v-if="canToggle" type="button" @click="toggleMore">
        {{ allShown ? 'Скрыть' : 'Показать еще' }}
        <svg class="PopularDestinations-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
          <path fill="#0E41D2" d="M3.17,9.29A5,5,0,0,1,8.7,3.06L7.8,4a.51.51,0,0,0,.3.86L12,5.25a.5.5,0,0,0,.55-.56L12.16.76a.51.51,0,0,0-.86-.3L10.24,1.51a1,1,0,0,0-.43-.27A7,7,0,0,0,1.24,9.81a1.07,1.07,0,0,0,.26.45,1,1,0,0,0,1,.26A1,1,0,0,0,3.17,9.29Z"></path>
          <path fill="#0E41D2" d="M14.76,6.19a1,1,0,0,0-1.93.52A5,5,0,0,1,7.3,12.94l.9-.9a.51.51,0,0,0-.3-.86L4,10.75a.5.5,0,0,0-.55.56l.43,3.93a.51.51,0,0,0,.86.3l1-1h0a1.07,1.07,0,0,0,.45.26,7,7,0,0,0,8.57-8.57Z"></path>
        </svg>
      </button>
    </article>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import DestinationCard from './PopularDestinationCard.vue';
import { useAllDestinations } from '@/hotels/composable/useAllDestinations';
import { pushBenchRoute } from '@/common/benchNavigation';
import { HOTEL_EVENTS, toLocalISODate, useHotelTrackEvent } from '@/hotels/composable/useHotelTrackEvent';
import { useHotelGuests } from '@/hotels/composable/useHotelGuests';

const PAGE = 6;
const COVER_IMAGES = [
  '/hotels/cdn/ef594d2137aaf189177f98326b9a0d2029a39f24.jpeg',
  '/hotels/cdn/219f01d8b0b9d1fabb6e6913933d48504bbcbd95.jpeg',
  '/hotels/cdn/410bec70fb6298b5bff63750525bb1d240971cce.jpeg',
  '/hotels/cdn/67bb68dfae0afd82d542a749d4fe99ddb6a61293.jpeg',
  '/hotels/cdn/59b319125c0a10c633e946d8d6831228a41c6835.jpeg',
  '/hotels/cdn/9047dd1b26fe06f80170c3ef610ee76ffa0fe083.jpeg',
  '/hotels/cdn/76bf9c378952d5d020ea85244e4f38e5f05e28e1.JPEG.jpeg',
  '/hotels/cdn/8fa34482247d9552c484d3d1c07da79b84aee40f.JPEG.jpeg',
  '/hotels/cdn/8d980dce47150c75201ef566e3f8cbfefe41cfc1.JPEG.jpeg',
];

type DestinationCardModel = {
  cityId: string;
  datasetId: string;
  label: string;
  cityName: string;
  countryName: string;
  country: string;
  title: string;
  imgSrc: string;
};

const router = useRouter();
const route = useRoute();
const { send } = useHotelTrackEvent();
const { roomsCount, guestsCount, childrenCount } = useHotelGuests();
const { destinationOptions, cityDatasetMap } = useAllDestinations();

const visibleCount = ref(PAGE);

const destinations = computed<DestinationCardModel[]>(() => {
  return destinationOptions.value.map((opt, i) => ({
    cityId: opt.cityId,
    datasetId: cityDatasetMap.value[opt.cityId] || '',
    label: opt.label,
    cityName: opt.cityName,
    countryName: opt.countryName,
    country: opt.countryName,
    title: `Отели ${opt.cityName}`,
    imgSrc: COVER_IMAGES[i % COVER_IMAGES.length],
  }));
});

const visibleDestinations = computed(() => destinations.value.slice(0, visibleCount.value));
const canToggle = computed(() => destinations.value.length > PAGE);
const allShown = computed(() => visibleCount.value >= destinations.value.length);

function toggleMore() {
  if (allShown.value) {
    visibleCount.value = PAGE;
    return;
  }
  visibleCount.value = Math.min(visibleCount.value + PAGE, destinations.value.length);
}

function defaultDates() {
  const checkIn = new Date();
  checkIn.setHours(0, 0, 0, 0);
  checkIn.setDate(checkIn.getDate() + 1);
  const checkOut = new Date(checkIn);
  checkOut.setDate(checkOut.getDate() + 4);
  return { checkIn, checkOut };
}

function openDestination(d: DestinationCardModel) {
  if (!d.datasetId) return;
  send(HOTEL_EVENTS.selectCity, {
    cityId: d.cityId,
    label: d.label,
    cityName: d.cityName,
    countryName: d.countryName,
  });
  const { checkIn, checkOut } = defaultDates();
  pushBenchRoute(router, {
    name: 'bench_hotel_search',
    stateId: 'state_hotels_search',
    trackId: route.params.track_id,
    query: {
      dataset: d.datasetId,
      cityId: d.cityId,
      dest: d.label,
      checkIn: toLocalISODate(checkIn),
      checkOut: toLocalISODate(checkOut),
      rooms: String(roomsCount.value),
      guests: String(guestsCount.value),
      children: String(childrenCount.value),
    },
  });
}
</script>

<style scoped>
section {
  display: grid;
  grid-gap: 10px 20px;
  grid-template-columns: 1fr 1fr 1fr;
}

.PopularDestinations-icon {
  margin-left: 16px;
}

button {
  margin: 0 auto;
  cursor: pointer;

  width: 100%;

  background: none;
  border: 0;

  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 12px !important;
  line-height: 21px !important;

  font-family: 'PTRootUI', Verdana, sans-serif;
  color: #0e41d2;
}

.header {
  margin-bottom: 16px;
  align-items: baseline;
  display: flex;
}

.title {
  align-items: center;
  display: flex;
  font-family: 'Spoof';
  font-size: 24px;
  font-weight: 500;
  line-height: 32px;

  color: #292f37;
}

.wrapper {
  padding-bottom: 64px;
}
</style>
