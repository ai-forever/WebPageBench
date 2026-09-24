<template>
  <div class="wrap" :style="vars">
    <div class="track" />

    <input
      class="range rangeLeft"
      type="range"
      :min="min"
      :max="max"
      :step="step"
      :value="value.min"
      @input="onMin"
    />

    <input
      class="range rangeRight"
      type="range"
      :min="min"
      :max="max"
      :step="step"
      :value="value.max"
      @input="onMax"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  min: number;
  max: number;
  step?: number;
  modelValue: { min: number; max: number };
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', v: { min: number; max: number }): void;
}>();

const step = computed(() => props.step ?? 100);

const value = computed(() => props.modelValue);

function clamp(v: number) {
  return Math.max(props.min, Math.min(props.max, v));
}

function onMin(e: Event) {
  const nextMin = clamp(Number((e.target as HTMLInputElement).value));
  const nextMax = Math.max(nextMin, value.value.max);
  emit('update:modelValue', { min: nextMin, max: nextMax });
}

function onMax(e: Event) {
  const nextMax = clamp(Number((e.target as HTMLInputElement).value));
  const nextMin = Math.min(nextMax, value.value.min);
  emit('update:modelValue', { min: nextMin, max: nextMax });
}

const vars = computed(() => {
  const span = props.max - props.min || 1;
  const p1 = ((value.value.min - props.min) / span) * 100;
  const p2 = ((value.value.max - props.min) / span) * 100;
  return {
    '--p1': `${p1}%`,
    '--p2': `${p2}%`,
  } as Record<string, string>;
});
</script>

<style scoped>
.wrap {
  position: relative;
  height: 28px; /* чтобы thumb был по центру */
  display: flex;
  align-items: center;
}

/* сама линия с выделением диапазона */
.track {
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(
    to right,
    rgba(45, 49, 55, 0.14) 0%,
    rgba(45, 49, 55, 0.14) var(--p1),
    #0e41d2 var(--p1),
    #0e41d2 var(--p2),
    rgba(45, 49, 55, 0.14) var(--p2),
    rgba(45, 49, 55, 0.14) 100%
  );
}

.range {
  position: absolute;
  left: 0;
  right: 0;
  width: 100%;
  height: 28px;
  background: transparent;
  appearance: none;
  margin: 0;
}

/* делаем трек input прозрачным, чтобы работала наша .track */
.range::-webkit-slider-runnable-track {
  height: 6px;
  background: transparent;
}
.range::-moz-range-track {
  height: 6px;
  background: transparent;
}

/* thumb */
.range::-webkit-slider-thumb {
  appearance: none;
  width: 26px;
  height: 26px;
  background: var(--bench-surface-elevated, #fff);
  border: 6px solid #0e41d2;
  border-radius: 50%;
  cursor: pointer;
  margin-top: -10px; /* центрируем относительно трека 6px */
}
.range::-moz-range-thumb {
  width: 26px;
  height: 26px;
  background: var(--bench-surface-elevated, #fff);
  border: 6px solid #0e41d2;
  border-radius: 50%;
  cursor: pointer;
}

/* чтобы “правый” thumb нормально перекрывал левый */
.rangeLeft {
  z-index: 2;
}
.rangeRight {
  z-index: 3;
}
</style>
