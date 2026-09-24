<template>
  <div class="logo">
    <RouterLink :to="homeTo">
      <img class="logo-img" alt="" src="/hotels/logo.svg" />
    </RouterLink>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { RouterLink, useRoute } from "vue-router";

const route = useRoute();

const homeTo = computed(() => ({
  name: 'bench_hotel_main',
  params: {
    track_id: route.params.track_id,
    state_id: 'state_hotels_main',
  },
}));
</script>

<style scoped>
.logo {
  margin: 0 16px;

  block-size: 40px;
  max-inline-size: 250px;

  flex: 0 1 auto;
}

.logo-img {
  block-size: 100%;
  max-inline-size: 100%;
  object-fit: contain;
  vertical-align: top;

  display: block;
  height: auto;
  max-width: 100%;

  overflow-clip-margin: content-box;
  overflow: clip;
}
</style>
