<template>
  <div
    class="hotelStars"
    :style="{ '--star-size': `${sizePx}px` }"
    :aria-label="ariaLabel"
    role="img"
  >
    <span
      v-for="i in count"
      :key="i"
      class="hotelStar"
      aria-hidden="true"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    stars: number;        // 0..5 (или 2..5 как у тебя)
    size?: number;        // размер звездочки в px
    max?: number;         // максимум звезд (по умолчанию 5)
  }>(),
  {
    size: 10,
    max: 5,
  },
);

function clampInt(n: number, min: number, max: number) {
  const x = Number.isFinite(n) ? Math.round(n) : min;
  return Math.max(min, Math.min(max, x));
}

const count = computed(() => clampInt(props.stars, 0, props.max));
const sizePx = computed(() => Math.max(6, Math.round(props.size))); // чуть защитимся от слишком маленьких
const ariaLabel = computed(() => `${count.value} звёзд`);
</script>

<style scoped>
.hotelStars {
  --star-size: 10px;
  display: flex;
  column-gap: calc(var(--star-size) / 10);
  align-items: center;
}

.hotelStar {
  display: inline-flex;
  inline-size: var(--star-size);
  block-size: var(--star-size);
  background-image: url(/hotels/cdn/star.0c35dc2a.svg);
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}
</style>
