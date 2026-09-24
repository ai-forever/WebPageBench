<template>
  <div class="searchFormWrapper">
    <div class="tabs">
      <SearchTabs />

      <div class="tabsContent">
        <div class="searchForm">
          <!-- Destination -->
          <div class="control controlDestination">
            <BenchCitySelect
              v-model="destination"
              :options="destinationOptions"
              :loading="loading"
              :error="error"
              :limit="20"
            />
          </div>

          <!-- Dates -->
          <div class="control controlDates">
            <BenchHotelDateField v-model:start="checkIn" v-model:end="checkOut" />
          </div>

          <!-- Guests -->
          <div class="control controlGuests">
            <BenchGuestCounter />
          </div>

          <!-- Submit -->
          <div class="control controlSubmit">
            <button class="searchButton" type="button" :disabled="!canSearch" @click="onSearch">
              <span class="searchButtonText">Найти</span>
            </button>
          </div>

          <!-- Radios -->
          <TripTypeRadios />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import SearchTabs from './SearchTabs.vue';
import TripTypeRadios from './TripTypeRadios.vue';
import BenchCitySelect from '@/bench/ui/BenchCitySelect.vue';
import BenchGuestCounter from '@/bench/ui/BenchGuestCounter.vue';
import BenchHotelDateField from '@/bench/ui/BenchHotelDateField.vue';

import type { DestinationOption } from '@/hotels/services/searchDataset';
import { useAllDestinations } from '@/hotels/composable/useAllDestinations';
import { pushBenchRoute } from '@/common/benchNavigation';
import { useHotelGuests } from '@/hotels/composable/useHotelGuests';

const router = useRouter();
const route = useRoute();

const { destinationOptions, cityDatasetMap, loading, error } = useAllDestinations();

const destination = ref<DestinationOption | null>(null);
const checkIn = ref<Date | null>(null);
const checkOut = ref<Date | null>(null);
const { roomsCount, guestsCount, childrenCount } = useHotelGuests();

function toISODate(d: Date) {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  const yyyy = x.getFullYear();
  const mm = String(x.getMonth() + 1).padStart(2, '0');
  const dd = String(x.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

const selectedDatasetId = computed(() => {
  const id = destination.value?.cityId;
  if (!id) return null;
  return cityDatasetMap.value[id] ?? null;
});

const canSearch = computed(() => {
  return !!destination.value && !!checkIn.value && !!checkOut.value && !loading.value && !!selectedDatasetId.value;
});

function onSearch() {
  if (!canSearch.value) return;

  pushBenchRoute(router, {
    name: 'bench_hotel_search',
    stateId: 'state_hotels_search',
    trackId: route.params.track_id,
    query: {
      dataset: selectedDatasetId.value!,
      cityId: destination.value!.cityId,
      dest: destination.value!.label,
      checkIn: toISODate(checkIn.value!),
      checkOut: toISODate(checkOut.value!),
      rooms: String(roomsCount.value),
      guests: String(guestsCount.value),
      children: String(childrenCount.value),
    },
  });
}
</script>

<style scoped>
.controlGuests {
  position: relative;
}

.searchFormWrapper {
  max-width: 1040px;
  box-sizing: border-box;
  margin-left: auto;
  margin-right: auto;
  padding: 0 20px;
}

.tabs {
  position: relative;
  z-index: 10;
}

.tabs:has(.bench-date-inline) {
  z-index: 1;
}

.tabsContent {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  padding: 10px;
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.08);
  box-sizing: border-box;
  line-height: 18px;
}

.searchForm {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: flex-start;
  gap: 0;
}

.control {
  box-sizing: border-box;
  margin: 10px;
  flex: 1 1 160px;
  min-inline-size: 0;
}

.controlDestination {
  flex: 2 1 220px;
}
.controlDates {
  flex: 1.5 1 200px;
}

.searchForm:has(.bench-date-inline) .controlDates {
  flex: 1 1 100%;
  min-inline-size: calc(100% - 20px);
  order: 8;
}
.controlGuests {
  flex: 1 1 160px;
}
.controlSubmit {
  flex: 0 1 140px;
  min-inline-size: 120px;
}

.searchButton {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  background: #0e41d2;
  color: #ffffff;
  font-size: 20px;
  padding: 0 12px;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid transparent;
}
.searchButton:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.searchButtonText {
  display: inline-block;
  transform: translateY(-1px);
  font-size: 16px;
  line-height: 20px;
  font-weight: 500;
  font-family: PTRootUI, sans-serif;
}
</style>
