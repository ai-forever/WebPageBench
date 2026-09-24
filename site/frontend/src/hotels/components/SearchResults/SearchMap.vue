<template>
  <div class="map">
    <div ref="el" class="mapCanvas"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue';
import L from 'leaflet';
// Важно: CSS Leaflet должен быть подключен ГДЕ-ТО 1 раз в проекте
// либо тут, либо в main.ts: import 'leaflet/dist/leaflet.css';
import 'leaflet/dist/leaflet.css';

const props = defineProps<{
  city?: string;
  country?: string;
  query?: string; // "Цюрих, Швейцария"
  zoom?: number;
  markerOffsetY?: number; // пиксели: насколько поднять маркер вверх (например 140-220)
}>();

const el = ref<HTMLDivElement | null>(null);

let map: L.Map | null = null;
let marker: L.Marker | null = null;

const zoom = computed(() => props.zoom ?? 12);
const markerOffsetY = computed(() => props.markerOffsetY ?? 180);

const q = computed(() => {
  if (props.query?.trim()) return props.query.trim();
  const parts = [props.city, props.country].filter(Boolean).map((x) => String(x).trim());
  return parts.join(', ');
});

// фикс дефолтной иконки маркера (часто ломается в Vite)
const defaultIcon = L.icon({
  iconUrl: '/hotels/cdn/marker-icon.png',
  shadowUrl: '/hotels/cdn/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const geocodeCache = new Map<string, { lat: number; lon: number } | null>();

async function geocode(place: string): Promise<{ lat: number; lon: number } | null> {
  const key = place.trim().toLowerCase();
  if (!key) return null;

  if (geocodeCache.has(key)) return geocodeCache.get(key)!;

  const url =
    'https://nominatim.openstreetmap.org/search' +
    `?format=json&limit=1&q=${encodeURIComponent(place)}`;

  const r = await fetch(url, {
    headers: { 'Accept-Language': 'ru' },
    // чуть “чище” для браузера
    referrerPolicy: 'no-referrer-when-downgrade',
  });

  if (!r.ok) {
    geocodeCache.set(key, null);
    return null;
  }

  const data = (await r.json()) as Array<{ lat: string; lon: string }>;
  if (!data?.length) {
    geocodeCache.set(key, null);
    return null;
  }

  const coords = { lat: Number(data[0].lat), lon: Number(data[0].lon) };
  geocodeCache.set(key, coords);
  return coords;
}

/**
 * Делаем так, чтобы маркер был НЕ по центру, а выше.
 * Для этого центр карты сдвигаем “вниз” на markerOffsetY пикселей.
 */
function getCenterWithYOffset(lat: number, lon: number) {
  if (!map) return L.latLng(lat, lon);

  const ll = L.latLng(lat, lon);
  const px = map.project(ll, zoom.value); // world pixels
  const shifted = px.add([0, markerOffsetY.value]); // центр “ниже”, маркер “выше”
  return map.unproject(shifted, zoom.value);
}

async function initOrUpdate() {
  const place = q.value;
  if (!place || !el.value) return;

  const coords = await geocode(place);
  if (!coords) return;

  await nextTick();

  // first init
  if (!map) {
    map = L.map(el.value, {
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);

    marker = L.marker([coords.lat, coords.lon], { icon: defaultIcon }).addTo(map);
    marker.bindPopup(place);

    // центр с offset, чтобы маркер был выше
    const center = getCenterWithYOffset(coords.lat, coords.lon);
    map.setView(center, zoom.value, { animate: false });

    // важно после первого рендера/изменений размеров
    requestAnimationFrame(() => map?.invalidateSize());
    return;
  }

  // update
  const center = getCenterWithYOffset(coords.lat, coords.lon);
  map.setView(center, zoom.value, { animate: false });

  if (marker) {
    marker.setLatLng([coords.lat, coords.lon]);
    marker.setPopupContent(place);
  } else {
    marker = L.marker([coords.lat, coords.lon], { icon: defaultIcon }).addTo(map);
    marker.bindPopup(place);
  }

  requestAnimationFrame(() => map?.invalidateSize());
}

onMounted(() => {
  initOrUpdate();
});

watch([q, zoom, markerOffsetY], () => {
  initOrUpdate();
});

onBeforeUnmount(() => {
  map?.remove();
  map = null;
  marker = null;
});
</script>

<style scoped>
.map {
  position: sticky;
  top: 16px;
  height: calc(100vh - 32px);
  border-radius: 16px;
  background: var(--bench-surface-elevated, #fff);
  overflow: hidden;
}

.mapCanvas {
  height: 100%;
  width: 100%;
}
</style>
