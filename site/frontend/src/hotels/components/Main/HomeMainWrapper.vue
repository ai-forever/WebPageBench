<template>
  <div class="homepageMainWrapper">
    <!-- пустые врапперы можно оставить (как в оригинале) -->
    <div class="homepageCollectionsWrapper"></div>
    <div class="homepageHistoryWrapper"></div>

    <div class="homepageBlogWrapper">
      <HomeBlogSection />
    </div>

    <HomeEmailCollectorSection />
    <Features />
    <MobileApp />
    <PopularDestination />
  </div>
</template>

<script setup>
import HomeBlogSection from './HomeBlogSection.vue';
import HomeEmailCollectorSection from '@/hotels/components/EmailCollector/HomeEmailCollectorSection.vue'
import Features from '../Features/Features.vue'
import MobileApp from '../MobileApp/MobileApp.vue';
import PopularDestination from '../PopularDestination/PopularDestination.vue';
</script>

<style scoped>
.homepageMainWrapper {
  padding: 0;
  /* background-color: ; */
}

@media (min-width: 1075px) {
  .homepageMainWrapper {
    max-width: 1040px;
    box-sizing: border-box;
    padding: 0 20px;
    margin-left: auto;
    margin-right: auto;
  }
}

/* общий отступ секций как в оригинале:
   margin-bottom: 64px у всех wrapper’ов, но у некоторых только если не пустые.
   Здесь оставляем только для blog wrapper — остальные пока пустые. */
.homepageBlogWrapper {
  margin-bottom: 64px;
  overflow: hidden;
}
</style>
