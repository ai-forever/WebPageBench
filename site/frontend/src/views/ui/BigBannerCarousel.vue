
<template>
  <div class="hero">
    <v-carousel cycle hide-delimiter-background show-arrows="hover" class="carousel">
      <v-carousel-item
        v-for="(item, i) in items"
        :key="i"
      >
        <div class="hero-slide">
          <v-img :src="getImageSrc(item.image)" cover class="hero-img"></v-img>
        </div>
      </v-carousel-item>
    </v-carousel>
  </div>
</template>

<script>
import { assets } from "@/assets/books-assets.js";
export default {
  props: {
    items: {
      type: Array,
      default: () => []
    }
  },
  methods: {
    getImageSrc(imagePath) {
      if (!imagePath) return '';
      return assets[imagePath];
    }
  }
}
</script>