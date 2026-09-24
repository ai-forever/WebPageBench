<!-- TODO: Поправить потом попап на карте -->
<template>
  <section v-if="geo" class="geoBlock">
    <div class="shell">
      <div class="header">
        <h3 class="hTitle">{{ geo.title ?? 'Расположение' }}</h3>
        <p class="hDesc">{{ geo.address }}</p>
      </div>

      <div ref="mapWrapEl" class="mapWrap">
        <div ref="mapEl" class="map" />

        <!-- top right -->
        <div class="mapTopRight">
          <button class="mapPrimaryBtn" type="button" @click="emit('show-nearby')">
            Смотреть отели рядом
          </button>

          <button class="mapIconBtn" type="button" aria-label="expand" @click="toggleFullscreen">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20">
              <path
                fill="#2d3137"
                d="M2.8 18.3L7.3 14A.8.8 0 1 0 6 12.7l-4.4 4.5v-3a.8.8 0 1 0-1.7 0v5c0 .4.4.8.8.8h5a.8.8 0 1 0 0-1.7h-3zm15.5-1.1L14 12.7a.8.8 0 1 0-1.2 1.2l4.5 4.4h-3a.8.8 0 1 0 0 1.7h5c.4 0 .8-.4.8-.8v-5a.8.8 0 1 0-1.7 0v3zM17.2 1.7L12.7 6A.8.8 0 1 0 14 7.3l4.4-4.5v3a.8.8 0 1 0 1.7 0v-5a.8.8 0 0 0-.8-.8h-5a.8.8 0 1 0 0 1.7h3zM1.7 2.8L6 7.3A.8.8 0 1 0 7.3 6L2.8 1.7h3a.8.8 0 1 0 0-1.7h-5a.8.8 0 0 0-.8.8v5a.8.8 0 1 0 1.7 0v-3z"
              />
            </svg>
          </button>
        </div>

        <!-- right controls -->
        <div class="mapControls">
          <div class="zoomBox">
            <button class="zoomBtn" type="button" aria-label="zoom-in" @click="zoomIn">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">
                <path fill="#2d3137" d="M9 7h6a1 1 0 0 1 0 2H9v6a1 1 0 0 1-2 0V9H1a1 1 0 0 1 0-2h6V1a1 1 0 0 1 2 0v6z" />
              </svg>
            </button>
            <button class="zoomBtn" type="button" aria-label="zoom-out" @click="zoomOut">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">
                <rect fill="#2d3137" width="16" height="2" y="7" rx="1" />
              </svg>
            </button>
          </div>

          <button class="locBtn" type="button" aria-label="recenter" @click="recenter">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 21 26" width="20" height="20">
              <g fill="none" fill-rule="evenodd">
                <path fill="#2d3137" d="M17.925 17.925c4.1-4.1 4.1-10.75 0-14.85s-10.75-4.1-14.85 0-4.1 10.75 0 14.85l7.425 7.258 7.425-7.258z" />
                <circle cx="10.357" cy="10.357" r="5.357" fill="#ffffff" />
              </g>
            </svg>
          </button>
        </div>
      </div>

      <!-- POI columns -->
      <div class="poiGrid">
        <div v-for="g in poiGroups" :key="g.id" class="poiCol">
          <div class="poiTitle" role="button" tabindex="0">
            {{ g.title }}
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor" class="poiArrow">
              <path
                fill-rule="nonzero"
                d="M10.908 14.623l6.139-6.14c.5-.499.5-1.315 0-1.815l-.172-.174a1.29 1.29 0 0 0-1.817 0L10 11.553l-5.06-5.06a1.288 1.288 0 0 0-1.814 0l-.173.175c-.5.5-.5 1.316 0 1.816l6.14 6.139a1.288 1.288 0 0 0 1.815 0"
              />
            </svg>
          </div>

          <ul class="PoisList">
            <li
              v-for="(p, i) in g.items"
              :key="p.name + '-' + i"
              class="PoisItem"
              :class="poiClass(p)"
              role="button"
              tabindex="0"
            >
              <span class="PoisName">{{ p.name }}</span>
              <span class="PoisName">&nbsp;•&nbsp;</span>
              <span class="PoisDistance">{{ p.distance }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

type PoiType =
  | 'HISTORICAL_POI'
  | 'CHURCH'
  | 'MUSEUM'
  | 'PARK'
  | 'NATURE'
  | 'ZOOS_AND_AQUARIUMS'
  | 'BUSINESS_CENTER'
  | 'AIRPORT'
  | 'RAILWAY_STATION'
  | string;

type PoiItem = { type: PoiType; name: string; distance: string };

type GeoMap = {
  lat?: number;           // <-- стало опциональным
  lng?: number;           // <-- стало опциональным
  zoom?: number;
  query?: string;         // <-- опционально для поиска
  tileUrlTemplate?: string;
  tileAttribution?: string;
};

type GeoBlock = {
  title?: string;
  address: string;
  map: GeoMap;
  poiGroups: Array<{ id: string; title: string; items: PoiItem[] }>;
};

type HotelWithGeo = {
  id: string;
  name: string;
  stars?: number;
  rating?: number;
  imageUrl?: string;
  geoBlock?: GeoBlock;
};

const props = defineProps<{ hotel: HotelWithGeo }>();
const emit = defineEmits<{ (e: 'show-nearby'): void }>();

const geo = computed(() => props.hotel.geoBlock ?? null);
const poiGroups = computed(() => geo.value?.poiGroups ?? []);

const mapEl = ref<HTMLDivElement | null>(null);
const mapWrapEl = ref<HTMLDivElement | null>(null);

let map: any= null;
let marker: any= null;

const resolvedCenter = ref<{ lat: number; lng: number } | null>(null);
const mapError = ref<string | null>(null);

let geocodeAbort: AbortController | null = null;

function buildMarkerHtml() {
  return `
    <div class="MainMarker_marker">
      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="15" viewBox="0 0 18 22">
        <path stroke="none" d="M15.367 2.663c3.412 3.405 3.522 9.041.247 12.589-.04.043-2.244 2.292-6.614 6.748l-6.432-6.557C-.809 12-.862 6.363 2.448 2.853c.061-.064.123-.128.185-.19 3.558-3.55 9.176-3.55 12.734 0z"></path>
        <circle fill="#ffffff" stroke="none" cx="9" cy="9" r="4"></circle>
        <circle stroke-width="2" cx="9" cy="9" r="1"></circle>
      </svg>
    </div>
  `;
}

function buildPopupHtml() {
  const stars = Math.max(0, Math.min(5, props.hotel.stars ?? 0));
  const rating = props.hotel.rating != null ? String(props.hotel.rating).replace('.', ',') : '';
  const img = props.hotel.imageUrl ?? '/hotels/cdn/island.png';

  const starSpans = new Array(stars).fill(0).map(() => `<span class="PopupStar"></span>`).join('');

  return `
    <div class="PopupCard" role="button" tabindex="0">
      <img class="PopupImg" src="${img}" alt="hotel" />
      <div class="PopupBody">
        <div class="PopupStars" style="--star-size: 8px">${starSpans}</div>
        <div class="PopupName">${props.hotel.name}</div>
        ${rating ? `<div class="PopupRating"><span class="PopupBadge">${rating}</span></div>` : ''}
      </div>
    </div>
  `;
}

/**
 * 1) если lat/lng есть — используем
 * 2) иначе — пробуем geocode по query/address
 * 3) кешируем в localStorage
 */
async function resolveCoords(): Promise<void> {
  mapError.value = null;
  resolvedCenter.value = null;

  const g = geo.value;
  if (!g) return;

  const lat = g.map.lat;
  const lng = g.map.lng;

  // есть координаты — супер
  if (typeof lat === 'number' && Number.isFinite(lat) && typeof lng === 'number' && Number.isFinite(lng)) {
    resolvedCenter.value = { lat, lng };
    return;
  }

  // иначе — геокодинг
  const query =
    g.map.query?.trim()
    || g.address?.trim()
    || `${props.hotel.name}`.trim();

  if (!query) {
    mapError.value = 'Нет адреса для поиска координат';
    return;
  }

  const cacheKey = `geo:v1:${props.hotel.id}:${query}`;
  const cached = readGeoCache(cacheKey);
  if (cached) {
    resolvedCenter.value = cached;
    return;
  }

  // abort предыдущий запрос (если переключили отель)
  geocodeAbort?.abort();
  geocodeAbort = new AbortController();

  try {
    const url =
      `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}&accept-language=ru`;

    const res = await fetch(url, {
      method: 'GET',
      signal: geocodeAbort.signal,
      headers: {
        // Номинатим иногда лучше отвечает с Accept, UA из браузера мы не зададим
        'Accept': 'application/json'
      }
    });

    if (!res.ok) {
      mapError.value = `Geocode error: HTTP ${res.status}`;
      return;
    }

    const data = (await res.json()) as Array<{ lat: string; lon: string }>;
    const first = data?.[0];
    if (!first?.lat || !first?.lon) {
      mapError.value = 'Не удалось найти координаты по адресу';
      return;
    }

    const latNum = Number(first.lat);
    const lngNum = Number(first.lon);

    if (!Number.isFinite(latNum) || !Number.isFinite(lngNum)) {
      mapError.value = 'Geocode вернул некорректные координаты';
      return;
    }

    const coords = { lat: latNum, lng: lngNum };
    resolvedCenter.value = coords;
    writeGeoCache(cacheKey, coords);
  } catch (e: any) {
    if (e?.name === 'AbortError') return;
    mapError.value = 'Ошибка геокодинга';
  }
}

function readGeoCache(key: string): { lat: number; lng: number } | null {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { lat: number; lng: number; ts: number };
    // TTL: 90 дней (можешь поменять)
    const maxAgeMs = 90 * 24 * 60 * 60 * 1000;
    if (!parsed?.ts || Date.now() - parsed.ts > maxAgeMs) return null;
    if (!Number.isFinite(parsed.lat) || !Number.isFinite(parsed.lng)) return null;
    return { lat: parsed.lat, lng: parsed.lng };
  } catch {
    return null;
  }
}

function writeGeoCache(key: string, coords: { lat: number; lng: number }) {
  try {
    localStorage.setItem(key, JSON.stringify({ ...coords, ts: Date.now() }));
  } catch {
    // ignore
  }
}

function initMap() {
  if (!geo.value || !mapEl.value) return;
  if (!resolvedCenter.value) return;

  const { zoom = 14, tileUrlTemplate, tileAttribution } = geo.value.map;
  const { lat, lng } = resolvedCenter.value;

  map = L.map(mapEl.value, {
    zoomControl: false,
    attributionControl: true
  }).setView([lat, lng], zoom);

  L.tileLayer(tileUrlTemplate ?? 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: tileAttribution ?? '© Участники OpenStreetMap',
    maxZoom: 19
  }).addTo(map);

  const icon = L.divIcon({
    className: 'MainMarker',
    html: buildMarkerHtml(),
    iconSize: [40, 50],
    iconAnchor: [20, 25]
  });

  marker = L.marker([lat, lng], { icon }).addTo(map);

  const popup = L.popup({
    closeButton: false,
    autoClose: false,
    closeOnClick: false,
    className: 'HotelPopup',
    offset: L.point(0, -10)
  }).setContent(buildPopupHtml());

  marker.bindPopup(popup).openPopup();

  // на всякий случай, если карта была скрыта/появилась
  setTimeout(() => map?.invalidateSize(), 0);
}

function destroyMap() {
  map?.remove();
  map = null;
  marker = null;
}

function recenter() {
  if (!map || !resolvedCenter.value) return;
  const z = geo.value?.map.zoom ?? map.getZoom();
  map.setView([resolvedCenter.value.lat, resolvedCenter.value.lng], z, { animate: true });
  marker?.openPopup();
}

function zoomIn() {
  map?.zoomIn();
}
function zoomOut() {
  map?.zoomOut();
}

async function toggleFullscreen() {
  const el = mapWrapEl.value;
  if (!el) return;

  const doc: any = document;
  if (doc.fullscreenElement) {
    await doc.exitFullscreen?.();
  } else {
    await (el as any).requestFullscreen?.();
  }
  setTimeout(() => map?.invalidateSize(), 150);
}

async function bootstrap() {
  destroyMap();
  await resolveCoords();
  initMap();
}

onMounted(() => {
  bootstrap();
});

onBeforeUnmount(() => {
  geocodeAbort?.abort();
  destroyMap();
});

watch(
  () => props.hotel.id,
  () => {
    bootstrap();
  }
);

function poiClass(p: PoiItem) {
  const t = p.type;

  const mapTypeToClass: Record<string, string> = {
    HISTORICAL_POI: 'Pois_poi_HISTORICAL_POI__d9O9B',
    CHURCH: 'Pois_poi_CHURCH__rtBlu',
    MUSEUM: 'Pois_poi_MUSEUM__bbwlF',
    PARK: 'Pois_poi_NATURE__park',
    NATURE: 'Pois_poi_NATURE__park',
    AIRPORT: 'Pois_poi_AIRPORT__1AwXL',
    RAILWAY_STATION: 'Pois_poi_RAILWAY_STATION__0Ba1u',
    ZOOS_AND_AQUARIUMS: 'Pois_poi_ZOOS_AND_AQUARIUMS__4m4lC',
    BUSINESS_CENTER: 'Pois_poi_BUSINESS_CENTER__T0Z4D'
  };

  return mapTypeToClass[t] ?? '';
}
</script>


<style scoped>
.shell {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  box-shadow: 0 12px 20px rgba(0,0,0,0.06);
  font-family: PTRootUI, Verdana, sans-serif;
}

.header {
  padding: 24px 24px 0;
}

.hTitle {
  margin: 0;
  font-size: 24px;
  line-height: 30px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.hDesc {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

/* MAP */
.mapWrap {
  margin: 14px 24px 0;
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  background: var(--bench-primary-light, #f4f4f4);
  height: 340px;
}

.map {
  width: 100%;
  height: 100%;
}

/* top right overlay */
.mapTopRight {
  position: absolute;
  top: 14px;
  right: 14px;
  display: flex;
  gap: 10px;
  align-items: center;
  z-index: 500;
}

.mapPrimaryBtn {
  height: 36px;
  padding: 0 14px;
  border-radius: 12px;
  border: 0;
  background: #0e41d2;
  color: #fff;
  font-size: 14px;
  line-height: 18px;
  font-weight: 800;
  cursor: pointer;
  font-family: PTRootUI, Verdana, sans-serif;
}

.mapIconBtn {
  width: 40px;
  height: 36px;
  border-radius: 12px;
  border: 0;
  background: var(--bench-surface-elevated, #fff);
  cursor: pointer;
  display: grid;
  place-items: center;
}

/* right controls */
.mapControls {
  position: absolute;
  right: 14px;
  top: 88px;
  z-index: 500;
  display: grid;
  gap: 10px;
}

.zoomBox {
  border-radius: 12px;
  overflow: hidden;
  background: var(--bench-surface-elevated, #fff);
  box-shadow: 0 6px 14px rgba(0,0,0,0.10);
}

.zoomBtn {
  width: 44px;
  height: 44px;
  border: 0;
  background: var(--bench-surface-elevated, #fff);
  cursor: pointer;
  display: grid;
  place-items: center;
}

.zoomBtn + .zoomBtn {
  border-top: 1px solid rgba(45,49,55,0.12);
}

.locBtn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: 0;
  background: var(--bench-surface-elevated, #fff);
  cursor: pointer;
  display: grid;
  place-items: center;
  box-shadow: 0 6px 14px rgba(0,0,0,0.10);
}

/* POI GRID */
.poiGrid {
  display: flex;
  /* grid-template-columns: repeat(4, minmax(0, 1fr)); */
  justify-content: space-between;
  gap: 6px;
  padding: 28px 24px 24px;
}

.poiTitle {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--bench-text, #2d3137);
  font-size: 16px;
  line-height: 20px;
  font-weight: 800;
  font-family: PTRootUI, Verdana, sans-serif;
  margin-bottom: 6px;
}

.poiArrow {
  opacity: 0.8;
}

/* reuse styles like your "Что есть рядом" */
.PoisList {
  list-style: none;
  padding: 0;
  margin: 0;
  max-inline-size: 325px;
}

.PoisItem {
  display: flex;
  font-size: 14px;
  font-weight: 500;
  /* justify-content: space-; */
  line-height: 20px;
  max-inline-size: 100%;
  margin: 8px 0 6px;
  /* padding-block-end: 4px;
  padding-block-start: 4px; */
  padding-inline-start: 20px;
  position: relative;
  font-family: PTRootUI, Verdana, sans-serif;
}

.PoisItem::before {
  background-image: url(/hotels/cdn/default-dark.0cf44b86_d10b0eba_1.svg);
  background-position: 0 0;
  background-repeat: no-repeat;
  background-size: contain;
  block-size: 100%;
  inline-size: 16px;
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
}

/* icons by type (ты говорил — если чего нет, добавишь) */
.Pois_poi_HISTORICAL_POI__d9O9B::before {
  background-image: url(/hotels/cdn/historical-places-of-interest.d2fd1030.svg);
}
.Pois_poi_CHURCH__rtBlu::before {
  background-image: url(/hotels/cdn/churches-and-cathedrals.21384bf7.svg);
}
.Pois_poi_MUSEUM__bbwlF::before {
  background-image: url(/hotels/cdn/museums.f2922b1d.svg);
}
.Pois_poi_NATURE__park::before {
  background-image: url(/hotels/cdn/nature-and-parks.8a4d71d7.svg);
}
.Pois_poi_AIRPORT__1AwXL::before {
  background-image: url(/hotels/cdn/avia.4f0c60b9.svg);
}
.Pois_poi_RAILWAY_STATION__0Ba1u::before {
  background-image: url(/hotels/cdn/train.f8eb2a02.svg);
}
.Pois_poi_ZOOS_AND_AQUARIUMS__4m4lC::before {
  background-image: url(/hotels/cdn/zoos-and-aquariums.f1574a2e.svg);
}
.Pois_poi_BUSINESS_CENTER__T0Z4D::before {
  background-image: url(/hotels/cdn/extra-services.7bf34de9.svg);
}

.PoisName {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  /* padding-inline-end: 10px; */
  font-size: 14px;
  font-weight: 480;
  line-height: 20px;
  color: #0e41d2;
  font-family: PTRootUI, Verdana, sans-serif;
}

.PoisDistance {
  flex-shrink: 0;
  /* padding: 2px 7px; */
  /* border-radius: 100px; */
  /* background: #f4f4f4; */
  /* color: rgba(45, 49, 55, 0.75); */
  display: inline-flex;
  color: #0e41d2;
  font-size: 14px;
  /* margin-inline-start: 4px; */
  white-space: nowrap;
  line-height: 20px;
  font-weight: 500;
  font-family: PTRootUI, Verdana, sans-serif;
}

/* Leaflet tweaks */
:global(.leaflet-control-attribution) {
  font-family: PTRootUI, Verdana, sans-serif;
  font-size: 12px;
  color: rgba(45,49,55,0.75);
}

/* marker + popup (минимально похоже на скрин) */
:global(.MainMarker svg path) {
  fill: #0e41d2;
}
:global(.MainMarker svg circle:last-child) {
  stroke: #0e41d2;
}

:global(.HotelPopup .leaflet-popup-content-wrapper) {
  border-radius: 16px;
  box-shadow: 0 10px 18px rgba(0,0,0,0.18);
  overflow: hidden;
}

:global(.HotelPopup .leaflet-popup-content) {
  margin: 0;
}

:global(.PopupCard) {
  width: 210px;
  height: 80px;
  display: flex;
  background: var(--bench-surface-elevated, #fff);
}

:global(.PopupImg) {
  width: 88px;
  height: 88px;
  object-fit: cover;
}

:global(.PopupBody) {
  padding: 10px 10px 10px 10px;
  display: grid;
  align-content: start;
  gap: 4px;
}

:global(.PopupStars) {
  display: flex;
  gap: 2px;
}

:global(.PopupStar) {
  width: var(--star-size);
  height: var(--star-size);
  background-image: url(/hotels/cdn/star.0c35dc2a.svg);
  background-size: contain;
  background-repeat: no-repeat;
}

:global(.PopupName) {
  font-family: PTRootUI, Verdana, sans-serif;
  font-size: 14px;
  line-height: 16px;
  font-weight: 800;
  color: var(--bench-text, #2d3137);
  max-width: 112px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:global(.PopupBadge) {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 10px;
  background: #91d30a;
  color: #fff;
  font-size: 12px;
  font-weight: 900;
  line-height: 14px;
}

/* responsive */
@media (max-width: 1100px) {
  .poiGrid {
    grid-template-columns: 1fr 1fr;
  }
}
@media (max-width: 720px) {
  .poiGrid {
    grid-template-columns: 1fr;
  }
}
</style>
