<template>
  <div class="bench-hotels">
    <header>
      <HotelsHeader />
    </header>

    <main class="hotels-main">
      <slot />
    </main>
</div>
</template>

<script setup>
import '@/hotels/assets/main.css';
import HotelsHeader from '@/hotels/components/Header/AppHeader.vue';
</script>

<style scoped>
.hotels-main {
  background-color: var(--bench-surface, #f0f3f7);
  min-height: calc(100vh - 120px);
}

.bench-hotels :deep(p) {
  padding-bottom: 0;
  text-indent: 0;
}
</style>
