<template>
  <div class="amenity-container" :title="titleText" aria-label="Удобства">
    <span
      v-for="a in shown"
      :key="a"
      class="amenity"
      :style="{ backgroundImage: `url(${iconUrl(a)})` }"
      :title="label(a)"
      aria-hidden="true"
    />
    <span v-if="hiddenCount > 0" class="more" :title="moreTitle">
      +{{ hiddenCount }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Amenity } from '../../services/searchDataset';

const props = withDefaults(
  defineProps<{
    amenities: Amenity[];
    limit?: number; // сколько иконок показывать (остальные в "+N")
  }>(),
  { limit: 5 },
);

const BASE = '/hotels/cdn';

const ICONS: Record<Amenity, string> = {
  wifi: `${BASE}/internet.b8e3abca.svg`,
  parking: `${BASE}/parking.43614c6c.svg`,
  breakfast: `${BASE}/meal.27c89335.svg`,
  pets: `${BASE}/pets.383546b8.svg`,          // если вдруг 404 — скажи, подставлю актуальное имя
  accessible: `${BASE}/disabled-support.cc65e41d.svg`, // если вдруг 404 — скажи, подставлю актуальное имя
  airConditioning: `${BASE}/air-conditioning.ce1a9abe.svg`,
};

const LABELS: Record<Amenity, string> = {
  wifi: 'Wi-Fi',
  parking: 'Парковка',
  breakfast: 'Завтрак',
  pets: 'Можно с питомцами',
  accessible: 'Доступная среда',
  airConditioning: 'Кондиционер'
};

function iconUrl(a: Amenity) {
  return ICONS[a] ?? ICONS.wifi;
}
function label(a: Amenity) {
  return LABELS[a] ?? a;
}

const normalized = computed<Amenity[]>(() => {
  // убираем дубликаты, сохраняем порядок
  const set = new Set<Amenity>();
  const res: Amenity[] = [];
  for (const a of props.amenities ?? []) {
    if (!set.has(a)) {
      set.add(a);
      res.push(a);
    }
  }
  return res;
});

const shown = computed(() => normalized.value.slice(0, props.limit));
const hiddenCount = computed(() => Math.max(0, normalized.value.length - shown.value.length));

const titleText = computed(() => normalized.value.map((a) => label(a)).join(', '));
const moreTitle = computed(() => normalized.value.slice(props.limit).map((a) => label(a)).join(', '));
</script>

<style scoped>
.amenity-container {
  display: flex;
  gap: 4px;
  justify-content: flex-end;
  align-items: center;
}

.amenity {
  background-position: 50%;
  background-repeat: no-repeat;
  background-size: contain;
  block-size: 16px;
  inline-size: 16px;
  display: inline-block;
  opacity: 0.95;
}

.more {
  font-size: 12px;
  font-weight: 700;
  color: rgba(45, 49, 55, 0.65);
  font-family: PTRootUI, sans-serif;
  padding: 0 6px;
  height: 16px;
  display: inline-flex;
  align-items: center;
  border-radius: 8px;
  background: var(--bench-primary-light, rgba(0, 0, 0, 0.06));
}
</style>
