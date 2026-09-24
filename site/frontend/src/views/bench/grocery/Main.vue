<template>
  <div v-if="configLoaded" class="bench-grocery">
    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isUserLoggedIn"
      :prefill-query="searchQuery"
    />

    <menu-bar :items="(common.menu_bar && common.menu_bar.items) || []" />

    <div v-if="!contentReady" class="loading-container">
      <v-progress-circular indeterminate color="primary" :size="64"></v-progress-circular>
    </div>

    <div v-if="contentReady">
      <div v-if="searchQuery && searchQuery.length >= 3" class="grid search-grid">
        <h2 class="section-title">Результаты поиска: «{{ searchQuery }}»</h2>
        <div v-if="searchResults.length === 0" class="no-results">
          Ничего не найдено по запросу «{{ searchQuery }}»
        </div>
        <div v-else-if="kvStoreLoaded" class="cards grocery-cards">
          <grocery-item
            v-for="(item, i) in searchResults"
            :key="'s' + i"
            :item="item"
            @open="openProductPreview"
            @basket-changed="loadBasket"
          />
        </div>
      </div>

      <template v-else>
        <div
          v-for="(section, sIdx) in gridSections"
          :key="'grid-' + sIdx"
          class="grid"
        >
          <h2 v-if="section.title" class="section-title">{{ section.title }}</h2>
          <div v-if="kvStoreLoaded" class="cards grocery-cards">
            <grocery-item
              v-for="(item, i) in section.items.filter((it) => it.item_id)"
              :key="'g' + sIdx + '-' + i"
              :item="item"
              @open="openProductPreview"
              @basket-changed="loadBasket"
            />
          </div>
          <div v-else-if="configLoaded" class="section">
            <v-row class="skeleton-grid">
              <v-col v-for="n in 10" :key="n" cols="2">
                <v-skeleton-loader type="image, article" elevation="0"></v-skeleton-loader>
              </v-col>
            </v-row>
          </div>
        </div>
      </template>
</div>

    <grocery-product-modal
      v-model="productPreviewOpen"
      :item="previewItem"
      :quantity="previewQuantity"
      :maxed="previewMaxed"
      :recommendations="previewRecommendations"
      @add="incrementItem"
      @remove="decrementItem"
      @select-product="onPreviewSelectProduct"
    />
  </div>
</template>

<script>
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import { GET_TRACK_CONFIG, GET_KV_STORE } from '@/store/actions.type';
import { StateDelayMixin } from '@/common/stateDelayMixin.js';
import { ensureBenchDomainMerged } from '@/common/benchNavigation';
import { isUnifiedBench } from '@/common/benchTheme';
import {
  getGroceryBasket,
  getGroceryCurrentUser,
  incrementGroceryBasketItem,
  applyDefaultMockLoginFromTrackConfig,
  isGroceryLoggedIn,
  syncGrocerySessionFromTrackConfig } from '@/utils/localCache.js';
import SearchBar from '../../ui/SearchBar.vue';
import MenuBar from '../../ui/MenuBar.vue';
import GroceryItem from './components/GroceryItem.vue';
import GroceryProductModal from './components/GroceryProductModal.vue';

export default defineComponent({
  name: 'GroceryMain',
  mixins: [StateDelayMixin],
  components: {
    SearchBar,
    MenuBar, GroceryItem,
    GroceryProductModal },
  data() {
    return {
      isUserLoggedIn: false,
      searchQuery: '',
      basket: {},
      kvStoreReady: false,
      productPreviewOpen: false,
      previewItem: null };
  },
  computed: {
    ...mapGetters(['trackConfig', 'kvStore']),
    configLoaded() {
      const cfg = this.trackConfig;
      if (!cfg || !Object.keys(cfg).length) return false;
      const ce = cfg.common_elements || {};
      return !!(ce.search_bar && ce.menu_bar);
    },
    kvStoreLoaded() {
      return this.kvStoreReady;
    },
    common() {
      return (this.trackConfig && this.trackConfig.common_elements) || {};
    },
    testData() {
      return (this.trackConfig && this.trackConfig.test_data) || {};
    },
    gridSections() {
      const keys = ['grid', 'grid2', 'grid3'];
      const kv = this.kvStore || {};
      return keys
        .map((key) => {
          const block = this.common[key];
          if (!block || !Array.isArray(block.items)) return null;
          const items = block.items
            .map((it) => {
              if (it && it.kv_id && kv[it.kv_id]) {
                return { ...kv[it.kv_id], ...it };
              }
              return it;
            })
            .filter((it) => it && (it.item_id || it.kv_id));
          return { title: block.title || '', items, key };
        })
        .filter(Boolean);
    },
    searchResults() {
      if (!this.searchQuery || this.searchQuery.length < 3) return [];
      return this.performSearch(this.searchQuery);
    },
    previewQuantity() {
      if (!this.previewItem || !this.previewItem.item_id) return 0;
      return this.basket[this.previewItem.item_id] || 0;
    },
    previewMaxed() {
      return this.previewItem ? this.isMaxedOut(this.previewItem) : false;
    },
    previewRecommendations() {
      if (!this.previewItem || !this.kvStore) return [];
      const id = this.previewItem.item_id;
      return Object.values(this.kvStore)
        .filter((it) => it && it.item_id && it.item_id !== id && this.hasPrice(it))
        .slice(0, 8);
    } },
  watch: {
    '$route.name': {
      handler(name) {
        if (name === 'bench_grocery_main') {
          this.ensureGroceryContext();
        }
      } },
    '$route.query.q': {
      immediate: true,
      handler(q) {
        this.searchQuery = q ? String(q) : '';
      } } },
  mounted() {
    this.ensureGroceryContext();
    if (!this.configLoaded) {
      this.getTrackConfig();
    } else {
      this.bootstrapFromConfig();
    }
    this.checkLoginState();
    this.loadBasket();
    this.basketInterval = setInterval(() => {
      const username = getGroceryCurrentUser() || 'guest';
      const currentBasket = JSON.stringify(getGroceryBasket(username));
      const previousBasket = JSON.stringify(this.basket);
      if (currentBasket !== previousBasket) {
        this.loadBasket();
      }
    }, 500);
  },
  activated() {
    this.ensureGroceryContext();
    this.checkLoginState();
    if (this.configLoaded) {
      this.bootstrapFromConfig();
    }
  },
  beforeUnmount() {
    if (this.basketInterval) {
      clearInterval(this.basketInterval);
    }
  },
  methods: {
    ensureGroceryContext() {
      if (!isUnifiedBench(this.trackConfig)) return;
      ensureBenchDomainMerged('grocery');
      applyDefaultMockLoginFromTrackConfig(this.trackConfig);
      syncGrocerySessionFromTrackConfig(this.trackConfig);
      const kvPath = this.trackConfig?.test_data?.kv_store_path;
      if (kvPath && !this.kvStoreReady) {
        this.$store.dispatch(GET_KV_STORE, { kvPath }).then(() => {
          this.kvStoreReady = true;
        });
      }
    },
    bootstrapFromConfig() {
      const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || '';
      if (kvPath && !this.kvStoreReady) {
        this.$store.dispatch(GET_KV_STORE, { kvPath }).then(() => {
          this.kvStoreReady = true;
        });
      } else if (!kvPath) {
        this.kvStoreReady = true;
      }
      this.applyStateDelay();
    },
    checkLoginState() {
      applyDefaultMockLoginFromTrackConfig(this.trackConfig);
      this.isUserLoggedIn = isGroceryLoggedIn();
    },
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
            this.$router.push({ name: 'not_found' });
            return;
          }
          if (!this.trackConfig[this.$route.params.state_id]) {
            this.$router.push({ name: 'state_not_found' });
          }
          this.ensureGroceryContext();
          this.checkLoginState();
          this.bootstrapFromConfig();
        });
    },
    hasPrice(item) {
      const p = item && item.price;
      return !(p === undefined || p === null || String(p).trim() === '');
    },
    isMaxedOut(item) {
      const max = parseInt(item && item.max_count, 10);
      if (!max || Number.isNaN(max)) return false;
      return (this.basket[item.item_id] || 0) >= max;
    },
    loadBasket() {
      const username = getGroceryCurrentUser() || 'guest';
      this.basket = getGroceryBasket(username);
    },
    performSearch(query) {
      const kv = this.kvStore || {};
      const q = String(query || '').trim().toLowerCase();
      if (!q || q.length < 3) return [];

      const words = q.split(/\s+/).filter(Boolean);
      const score = (title) => {
        const t = String(title || '').toLowerCase();
        let sc = 0;
        if (t.startsWith(q)) sc += 100;
        if (t.includes(q)) sc += 40;
        for (const w of words) {
          if (t.startsWith(w)) sc += 25;
          if (t.includes(w)) sc += 10;
          let i = 0;
          for (const ch of t) {
            if (ch === w[i]) i++;
          }
          if (i >= Math.max(1, w.length - 1)) sc += 5;
        }
        sc -= Math.min(20, Math.floor(t.length / 6));
        return sc;
      };

      return Object.values(kv)
        .filter((item) => item && item.title)
        .map((item) => ({ item, sc: score(item.title) }))
        .filter((it) => it.sc > 0)
        .sort((a, b) => b.sc - a.sc)
        .slice(0, 100)
        .map((it) => it.item);
    },
    openProductPreview(item) {
      if (!item) return;
      this.previewItem = item;
      this.productPreviewOpen = true;
    },
    onPreviewSelectProduct(rec) {
      if (!rec) return;
      this.previewItem = rec;
    },
    incrementItem(itemId) {
      const username = getGroceryCurrentUser() || 'guest';
      incrementGroceryBasketItem(username, itemId, 1);
      this.loadBasket();
    },
    decrementItem(itemId) {
      const username = getGroceryCurrentUser() || 'guest';
      incrementGroceryBasketItem(username, itemId, -1);
      this.loadBasket();
    } } });
</script>

<style scoped>
.bench-grocery {
  --shop-max-width: 1600px;
  height: auto;
  min-height: 100%;
  overflow: visible;
  display: block;
  background: var(--bench-surface, #f0f3f7);
}

.loading-container {
  display: flex;
  justify-content: center;
  padding: 48px 0;
}

.section-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 20px;
  grid-column: 1 / -1;
}

.search-grid {
  display: block;
}

.no-results {
  font-size: 18px;
  color: #666;
  text-align: center;
  padding: 40px 20px;
}

.grocery-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.skeleton-grid {
  max-width: var(--shop-max-width);
  margin: 0 auto;
}

@media (max-width: 1400px) {
  .grocery-cards {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 1100px) {
  .grocery-cards {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 800px) {
  .grocery-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

<style src="@/assets/books.css"></style>
