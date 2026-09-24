<template>
    <div class="bench-books">
        <div class="logo-line">
            <div class="container">
                <v-img
                    v-if="imageSrc"
                    :src="imageSrc"
                    :width="'auto'"
                    class="logo-line-img"
                    contain
                ></v-img>
            </div>
        </div>
    </div>
</template>

<script>
import { assets } from "@/assets/books-assets.js";
export default {
  props: {
    image: {
      type: String,
      default: ''
    }
  },
  computed: {
    imageSrc() {
      if (!this.image) return '';
      return assets[this.image];
    }
  }
}
</script>

