<template>
  <div class="gallery">
    <div class="galleryWrapper">
      <div class="galleryGrid">
        <div
          v-for="(src, i) in shown"
          :key="src + '-' + i"
          class="galleryImage"
          :class="slotClass(i)"
        >
          <picture>
            <img :src="src" alt="" loading="lazy" />
          </picture>

          <!-- Overlay ONLY on last visible tile, if there are more images -->
          <div v-if="showMoreOverlay && i === shown.length - 1" class="moreImages">
            <span>+{{ moreCount }} фото</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{ images: string[] }>();

// Под твой grid-template-areas: a,b,c,e,f,d,g (7 тайлов)
// (a занимает 2x2, остальные — по 1 ячейке)
const MAX_VISIBLE = 7;

console.log(props.images)

// Берём первые 7 для отображения в сетке
const shown = computed(() => (props.images ?? []).slice(0, MAX_VISIBLE));

const moreCount = computed(() => Math.max(0, (props.images?.length ?? 0) - shown.value.length));
const showMoreOverlay = computed(() => moreCount.value > 0);

// Индекс -> grid-area слот
// i=0 -> a (у тебя и так через :first-child, но пусть будет и классом — не мешает)
// i=1 -> b
// i=2 -> c
// i=3 -> e
// i=4 -> f
// i=5 -> d
// i=6 -> g
const SLOT_ORDER = ['a', 'b', 'c', 'e', 'f', 'd', 'g'] as const;

function slotClass(i: number) {
  const slot = SLOT_ORDER[i] ?? 'x';
  return `slot-${slot}`;
}
</script>

<style scoped>
span {
  color: #fff;
  font-size: 20px;
  font-weight: 700;
  line-height: 24px;
  font-family: PTRootUI, Verdana, sans-serif;
}

img {
  object-fit: cover;
  block-size: 100%;
  inline-size: 100%;
  border-style: none;
  display: block;
  max-inline-size: 100%;
}

.moreImages {
  bottom: 0;
  top: 0;
  right: 0;
  left: 0;

  align-items: center;
  background-color: #00000080;
  color: #FFF;
  display: flex;
  font-size: 20px;
  font-weight: 700;
  justify-content: center;
  line-height: 24px;
  position: absolute;
}

.gallery {
  align-items: center;
  background-color: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  display: flex;
  inline-size: 100%;
  justify-content: center;
}

.galleryImage {
  border-radius: 6px;
  cursor: pointer;
  overflow: hidden;
  position: relative;
}

.galleryWrapper {
  block-size: 400px;
  box-sizing: border-box;
}

.galleryGrid {
  block-size: 100%;
  border-radius: 12px;
  display: grid;
  grid-gap: 4px;
  grid-template-areas:
      "a a b c e"
      "a a f d g";
  inline-size: 100%;
  overflow: hidden;
}

/* ✅ grid-area слоты */
.slot-a { grid-area: a; }
.slot-b { grid-area: b; }
.slot-c { grid-area: c; }
.slot-d { grid-area: d; }
.slot-e { grid-area: e; }
.slot-f { grid-area: f; }
.slot-g { grid-area: g; }

/* Можно оставить твоё правило, оно не мешает */
.galleryImage:first-child {
  grid-area: a;
}

@media (max-width: 920px) {
  .gallery { grid-template-columns: 1fr; }
  .mainImg { height: 260px; }
  .grid { grid-auto-rows: 120px; }
  .thumb { height: 120px; }
}
</style>
