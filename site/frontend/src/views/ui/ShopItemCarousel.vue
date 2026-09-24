
<template>
  <div class="section">
    <div class="section-title">{{ title }}</div>
    <v-carousel height="340" hide-delimiter-background show-arrows="hover" cycle>
      <v-carousel-item v-for="(group, gIndex) in groupedItems" :key="gIndex">
        <v-row>
          <v-col v-for="(item, iIndex) in group" :key="iIndex" cols="2">
            <v-card class="product product-card" elevation="0" @click="onItemClick(item)" role="button">
              <div class="thumb">
                <book-cover :item="item" />
                <div v-if="item.is_sales_hit" class="hit-badge">Хит продаж</div>
                <div v-if="item.discount_percent" class="discount-badge">-{{ item.discount_percent }}%</div>
                <v-btn class="favorite" variant="text" size="medium" @click.stop="onFavoriteClick(item)">
                  <v-icon size="18" :color="isItemFavorite(item) ? 'red' : ''">{{ isItemFavorite(item) ? 'mdi-heart' : 'mdi-heart-outline' }}</v-icon>
                </v-btn>
              </div>
              <v-card-title class="name">{{ item.name || item.title }}</v-card-title>
              <v-card-subtitle class="author">{{ item.author }}</v-card-subtitle>
              <v-card-text class="meta">
                <div class="formats">
                  <v-icon v-if="item.is_audiobook" size="18">mdi-headphones</v-icon>
                  <v-icon size="18">mdi-book-open-variant</v-icon>
                </div>
                <div class="rating">
                  <v-icon size="16" color="warning">mdi-star</v-icon>
                  <span class="rating-value">{{ formatRating(item.rating) }}</span>
                  <span class="votes">{{ item.number_of_votes }}</span>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-carousel-item>
    </v-carousel>
  </div>
</template>

<script>
import { pushBenchRoute } from "@/common/benchNavigation";
import { _logActivity } from "@/common/trackHelper";
import { getCurrentUsername, isBooksFavorite, toggleBooksFavorite } from "@/utils/localCache.js";
import BookCover from "../bench/books/BookCover.vue";

export default {
  components: { BookCover },
  props: {
    title: {
      type: String,
      default: ''
    },
    items: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      favoritesUpdate: 0
    };
  },
  computed: {
    groupedItems() {
      const groupSize = 6;
      const groups = [];
      for (let i = 0; i < this.items.length; i += groupSize) {
        groups.push(this.items.slice(i, i + groupSize));
      }
      return groups;
    }
  },
  methods: {
    formatRating(value) {
      if (value === null || value === undefined || isNaN(Number(value))) return '';
      return Number(value).toFixed(1);
    },
    onItemClick(item) {
      if (!item) return;
      const toView = item.to_view_type || item.to_type || 'bench_books_item';
      const toState = item.to_state || item.kv_id || (item.id ? `item_${item.id}` : undefined);
      if (toState) {
        pushBenchRoute(this.$router, {
          name: toView,
          stateId: toState,
          trackId: this.$route.params.track_id,
        });
      }
    },
    isItemFavorite(item) {
      // Force reactivity update
      this.favoritesUpdate;

      if (!item) return false;
      const itemId = item.to_state || item.kv_id || (item.id ? `item_${item.id}` : null);
      if (!itemId) return false;

      const username = getCurrentUsername() || 'guest';
      return isBooksFavorite(username, itemId);
    },
    onFavoriteClick(item) {
      if (!item) return;

      const itemId = item.to_state || item.kv_id || (item.id ? `item_${item.id}` : null);
      if (!itemId) return;

      const username = getCurrentUsername() || 'guest';
      const wasAlreadyFavorite = isBooksFavorite(username, itemId);
      toggleBooksFavorite(username, itemId);
      this.favoritesUpdate++;

      const nestedPrices = item.prices;
      const price = nestedPrices && nestedPrices.final_price != null
        ? nestedPrices.final_price
        : (item.price != null ? item.price : null);
      const genres = (item.genres) || [];
      const mainGenre = genres.length > 0 && genres[0].name ? genres[0].name : null;

      _logActivity(this, {
        type: wasAlreadyFavorite ? 'remove_favorites' : 'add_favorites',
        item_id: itemId,
        title: item.name || item.title || null,
        author: item.author || null,
        price: price,
        is_audiobook: item.is_audiobook === true,
        genre: mainGenre
      });
    }
  }
}
</script>