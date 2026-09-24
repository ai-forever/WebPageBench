<template>
  <section v-if="info" class="Section">
    <div class="shell">
      <h3 class="title">{{ info.title ?? 'Дополнительная информация' }}</h3>

      <div class="body">
        <p v-for="(p, i) in info.paragraphs" :key="i" class="paragraph">
          {{ p }}
        </p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type AdditionalInfoBlock = {
  title?: string;
  paragraphs: string[];
};

type HotelWithAdditionalInfo = {
  id: string;
  additionalInfoBlock?: AdditionalInfoBlock;
};

const props = defineProps<{ hotel: HotelWithAdditionalInfo }>();

const info = computed(() => props.hotel.additionalInfoBlock ?? null);
</script>

<style scoped>
.shell {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.06);
  padding: 24px;

  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  font-family: PTRootUI, Verdana, sans-serif;
}

.title {
  color: var(--bench-text, #2d3137);
  font-size: 24px;
  font-weight: 700;
  line-height: 30px;
  margin: 0 0 16px;
  position: relative;
  font-family: PTRootUI, Verdana, sans-serif;
}

.paragraph {
  margin: 0;
  margin-block-end: 8px;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.paragraph:last-child {
  margin-block-end: 0;
}
</style>
