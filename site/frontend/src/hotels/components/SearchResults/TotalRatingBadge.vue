<template>
  <div class="Badge" :class="`Badge--${size}`" :style="{ '--badge-color': color }">
    <svg class="Badge__icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 46 60" aria-hidden="true">
      <path
        :fill="color"
        d="M3 0h40v50.79a2 2 0 0 1-2.2 1.99l-17.6-1.763a1.996 1.996 0 0 0-.4 0L5.2 52.78A2 2 0 0 1 3 50.79V0Z"
      />
    </svg>

    <span class="Badge__value">{{ ratingText }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    value: number; // 0..10
    size?: 'm' | 'l';
    decimalSeparator?: ',' | '.';
  }>(),
  { size: 'l', decimalSeparator: ',' },
);

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

const v = computed(() => clamp(Number(props.value) || 0, 0, 10));

const ratingText = computed(() => {
  const raw = v.value.toFixed(1).replace('.0', '');
  return props.decimalSeparator === ',' ? raw.replace('.', ',') : raw;
});

const color = computed(() => {
  const hue = (v.value / 10) * 120; // 0 red -> 120 green
  return `hsl(${hue} 78% 45%)`;
});
</script>

<style scoped>
.Badge {
  position: relative;
  display: flex;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  text-align: center;
  filter: drop-shadow(0 3px 3px var(--badge-color));
  flex-shrink: 0;
}

.Badge__icon {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.Badge__value {
  position: relative;
  z-index: 1;
  margin-block-end: 8px;
  color: #fff;
}

.Badge--l {
  inline-size: 64px;
  block-size: 83px;
  font-size: 22px;
  padding-block-start: 16px;
}

.Badge--m {
  inline-size: 50px;
  block-size: 68px;
  font-size: 18px;
  padding-block-start: 14px;
}
</style>
