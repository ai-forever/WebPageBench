<template>
  <div class="hotelRating" :class="{ badgeFirst }">
    <!-- badge -->
    <div class="badge" :style="{ '--badge-color': color }">
      <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 43 60" aria-hidden="true">
        <path
          :fill="color"
          d="M0 6a6 6 0 0 1 6-6h31a6 6 0 0 1 6 6v50.573a3 3 0 0 1-3.695 2.918l-17.573-4.187a1 1 0 0 0-.464 0L3.695 59.491A3 3 0 0 1 0 56.573V6Z"
        />
      </svg>

      <span class="value">{{ ratingText }}</span>
    </div>

    <!-- text -->
    <div class="text">
      <div class="category">{{ category }}</div>

      <div class="reviewsLine">
        <component
          :is="reviewsAsLink ? 'button' : 'span'"
          class="reviews"
          :class="{ reviewsLink: reviewsAsLink }"
          type="button"
        >
          {{ reviewsText }} отзывов
        </component>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    rating: number;   // 0..10
    reviews: number;  // count

    /** в блоке "Отзывы" на отеле — бейдж слева, текст справа */
    badgeFirst?: boolean;

    /** сделать "329 отзывов" синим (как ссылка) */
    reviewsAsLink?: boolean;

    /** разделитель дробной части: на островке обычно "7,6" */
    decimalSeparator?: ',' | '.';
  }>(),
  {
    badgeFirst: false,
    reviewsAsLink: false,
    decimalSeparator: ',',
  },
);

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

const ratingClamped = computed(() => clamp(Number(props.rating) || 0, 0, 10));

const ratingText = computed(() => {
  const raw = ratingClamped.value.toFixed(1).replace('.0', '');
  return props.decimalSeparator === ',' ? raw.replace('.', ',') : raw;
});

const reviewsText = computed(() => String(Number(props.reviews) || 0));

const category = computed(() => {
  const r = ratingClamped.value;
  if (r >= 9.0) return 'Превосходно';
  if (r >= 8.0) return 'Очень хорошо';
  if (r >= 7.0) return 'Хорошо';
  if (r >= 6.0) return 'Неплохо';
  return 'Плохо';
});

const color = computed(() => {
  const r = ratingClamped.value;
  const hue = (r / 10) * 120; // 0 red -> 120 green
  return `hsl(${hue} 78% 45%)`;
});
</script>

<style scoped>
.hotelRating {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* по умолчанию как раньше: текст слева, бейдж справа */
.hotelRating:not(.badgeFirst) {
  flex-direction: row-reverse;
}
.hotelRating:not(.badgeFirst) .text {
  text-align: end;
}

/* вариант для блока "Отзывы": бейдж слева */
.hotelRating.badgeFirst .text {
  text-align: start;
}

.text {
  display: flex;
  flex-direction: column;
  font-family: PTRootUI, Verdana, sans-serif;
}

.category {
  font-size: 16px;
  font-weight: 700;
  line-height: 22px;
  color: var(--bench-text, #2d3137);
}

.reviewsLine.badgeFirst {
  display: flex;
  justify-content: flex-end;
}

.reviews {
  color: #868686;
  font-size: 12px;
  font-weight: 480;
  line-height: 16px;
}

/* “как ссылка” */
.reviewsLink {
  border: 0;
  background: none;
  padding: 0;
  cursor: pointer;
  color: #0e41d2;
  font-weight: 500;
  font-family: PTRootUI, Verdana, sans-serif;
}

.badge {
  block-size: 48px;
  inline-size: 35px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding-block-start: 4px;
  color: #fff;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
  flex-shrink: 0;
}

.icon {
  inset: 0;
  position: absolute;
  inline-size: 100%;
  block-size: 100%;
  overflow: hidden;
}

.value {
  position: relative;
  z-index: 1;
  margin-block-end: 7px;
  font-size: 16px;
  color: #fff;
  font-weight: 700;
  line-height: 16px;
}
</style>
