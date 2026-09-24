
<template>
  <div v-if="imageSrc" class="banner-line" :style="{ backgroundColor: color }">
    <v-img    
      v-if="imageSrc"
      :src="imageSrc"
      cover
      height="100%"
      class="w-100"
      style="flex: 1 1 auto; display: block;"
    ></v-img>
  </div>
</template> 

<script>
import { assets } from "@/assets/books-assets.js";
import { shopAssets } from "@/assets/shop-assets.js";
export default {
  props: {
    images: {
      type: Array,
      default: () => []
    },
    color: {
      type: String,
      default: '#000000'
    },
    assets: {
      type: String,
      default: () => "books"
    }
  },
  computed: {
    imageSrc() {
      const list = Array.isArray(this.images) ? this.images.filter(Boolean) : [];
      if (!list.length) return '';
      const idx = Math.floor(Math.random() * list.length);
      const key = list[idx];
      const map = this.assets === "shop" ? shopAssets : assets;
      return map[key] || '';
    }
  }
}
</script>