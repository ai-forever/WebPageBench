<template>
  <div class="card-wrapper" role="button" tabindex="0" @click="$emit('select')" @keydown.enter="$emit('select')">
    <div class="image-wrap">
      <img :alt="imgAltComputed" :src="imgSrc" />
    </div>

    <div class="title-wrapper">
      <p>{{ country }}</p>
      <span class="dest-link">{{ title }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type Props = {
  imgSrc: string
  imgAlt?: string
  country: string
  title: string
}

const props = defineProps<Props>()
defineEmits<{ select: [] }>()

const imgAltComputed = computed(() => props.imgAlt ?? props.title)
</script>

<style scoped>
p {
  color: #868686;
  font-size: 12px !important;

    line-height: 1.231;
    font-family: 'PTRootUI', Verdana, sans-serif;
    font-weight: 480;
}

.dest-link {
  cursor: pointer;

  font-size: 15px;
  word-wrap: break-word;

  align-items: center;
  color: #0e41d2;
  display: inline-flex;
  font-size: 16px;
  font-weight: 500;
  line-height: inherit;
  text-decoration: none;
  transition: color 0.16s ease;
}

.title-wrapper {
  left: 0;
  right: 0;

  background-color: var(--bench-surface-elevated, #fff);
  padding: 16px 20px;

  bottom: 0;
  display: flex;
  flex-direction: column;
  position: absolute;
  z-index: 2;
}

img {
  border-bottom-left-radius: 20px;
  border-bottom-right-radius: 20px;

  background-color: #c8c8c8;
  background-position: 50% 50%;
  background-repeat: no-repeat;
  background-size: cover;

  display: block;
  height: 220px;
  object-fit: cover;
  position: relative;
  transition: transform 0.3s ease-out;
  width: 100%;
  z-index: 1;

  max-width: 100%;
}

.card-wrapper {
  border-radius: 16px;
  margin-bottom: 15px !important;

  display: flex;
  height: 220px;
  overflow: hidden;
  position: relative;
  transition: box-shadow 0.3s ease;
  cursor: pointer;
}

.image-wrap {
  width: 100%;
  height: 220px;
  overflow: hidden;
}

.image-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease-out;
}

.card-wrapper:hover .image-wrap img {
  transform: scale(1.05);
}
</style>
