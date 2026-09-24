<template>
  <div v-if="configLoaded" class="bench-market">
    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isLoggedIn"
      @login="openLoginDialog"
    />
    <div class="menu-wrap menu-rounded pb-4">
      <menu-bar
        :items="(common.menu && common.menu.items) || []"
        :logged-in="isLoggedIn"
        :delivery-type="shopUser.delivery_type"
        :address="shopUser.address"
      />
    </div>

    <div v-if="!contentReady" class="loading-container">
      <v-progress-circular indeterminate color="primary" :size="64"></v-progress-circular>
    </div>

    <!-- FIRST GRID COMPONENT -->
    <div v-if="contentReady">
    <div class="grid">
      <div v-if="kvStoreLoaded" class="cards">
        <shop-item
          v-for="(it, i) in gridItemsResolved"
          :key="'g'+i"
          :item="it"
          :get-image-src="getImageSrc"
          :get-current-price="getCurrentPrice"
          :get-old-price="getOldPrice"
          :get-discount-percent="getDiscountPercent"
          :get-display-name="getDisplayName"
          :get-item-key="getItemKey"
          :is-fav="isFav"
          :toggle-fav="toggleFav"
          :open-item="openItem"
          :logged-in="isLoggedIn"
          :username="(testData && testData.login_data && testData.login_data.login) || 'guest'"
        />
      </div>
      <div v-else-if="configLoaded" class="section">
        <v-row class="skeleton-grid">
          <v-col v-for="n in 12" :key="n" cols="2">
            <v-skeleton-loader type="image, article" elevation="0"></v-skeleton-loader>
          </v-col>
        </v-row>
      </div>
    </div>

    <div class="grid">
      <div v-if="kvStoreLoaded" class="cards">
        <shop-item
          v-for="(it, i) in gridItemsResolved2"
          :key="'g'+i"
          :item="it"
          :get-image-src="getImageSrc"
          :get-current-price="getCurrentPrice"
          :get-old-price="getOldPrice"
          :get-discount-percent="getDiscountPercent"
          :get-display-name="getDisplayName"
          :get-item-key="getItemKey"
          :is-fav="isFav"
          :toggle-fav="toggleFav"
          :open-item="openItem"
          :logged-in="isLoggedIn"
          :username="(testData && testData.login_data && testData.login_data.login) || 'guest'"
        />
        
      </div>
      <div v-else-if="configLoaded" class="section">
        <v-row class="skeleton-grid">
          <v-col v-for="n in 12" :key="n" cols="2">
            <v-skeleton-loader type="image, article" elevation="0"></v-skeleton-loader>
          </v-col>
        </v-row>
      </div>
    </div>

    <div class="grid">
      <div v-if="kvStoreLoaded" class="cards">
        <shop-item
          v-for="(it, i) in gridItemsResolved3"
          :key="'g'+i"
          :item="it"
          :get-image-src="getImageSrc"
          :get-current-price="getCurrentPrice"
          :get-old-price="getOldPrice"
          :get-discount-percent="getDiscountPercent"
          :get-display-name="getDisplayName"
          :get-item-key="getItemKey"
          :is-fav="isFav"
          :toggle-fav="toggleFav"
          :open-item="openItem"
          :logged-in="isLoggedIn"
          :username="(testData && testData.login_data && testData.login_data.login) || 'guest'"
        />
        
      </div>
      <div v-else-if="configLoaded" class="section">
        <v-row class="skeleton-grid">
          <v-col v-for="n in 12" :key="n" cols="2">
            <v-skeleton-loader type="image, article" elevation="0"></v-skeleton-loader>
          </v-col>
        </v-row>
      </div>
    </div>

  <div class="grid">
    <div v-if="kvStoreLoaded" class="cards">
      <div v-for="(it, i) in gridItemsResolved4" :key="'g'+i" class="card" @click="openItem(it)">
        <div class="thumb">
          <div v-if="it.original_tag" class="sale-badge">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 2.065c-2-.643-.667 3.71-2 3.71-.667 0-.806-1.258-1.339-1.258C3.994 4.517 2 6.56 2 9.13 2 11.474 3.333 14 6 14c.667 0 1-.212.625-.62-1.875-2.044-1.358-4.042-.63-3.808.94.302 1.823 1.779 2.557-1.35.186-.847.653-.622 1.266 0 .921.932 1.402 2.94-.36 5.157-.291.367.209.621 1.021.621C12.23 14 14 12.106 14 9.13c0-4.004-4-6.423-6-7.065"/>
            </svg>
            Распродажа
          </div>
          <v-img :src="getImageSrc(it.thumbnail || it.img)" cover />
          <button
            type="button"
            class="fav-btn"
            :class="{ active: isFav(it) }"
            :aria-label="isFav(it) ? 'Убрать из избранного' : 'Добавить в избранное'"
            :title="isFav(it) ? 'Убрать из избранного' : 'Добавить в избранное'"
            @click.stop.prevent="toggleFav(it)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M7 5a4 4 0 0 0-4 4c0 3.552 2.218 6.296 4.621 8.22A21.5 21.5 0 0 0 12 19.91a21.6 21.6 0 0 0 4.377-2.69C18.78 15.294 21 12.551 21 9a4 4 0 0 0-4-4c-1.957 0-3.652 1.396-4.02 3.2a1 1 0 0 1-1.96 0C10.652 6.396 8.957 5 7 5m5 17c-.316-.02-.56-.147-.848-.278a23.5 23.5 0 0 1-4.781-2.942C3.777 16.705 1 13.449 1 9a6 6 0 0 1 6-6 6.18 6.18 0 0 1 5 2.568A6.18 6.18 0 0 1 17 3a6 6 0 0 1 6 6c0 4.448-2.78 7.705-5.375 9.78a23.6 23.6 0 0 1-4.78 2.942c-.543.249-.732.278-.845.278"/>
            </svg>
          </button>
        </div>
        <div class="price-row">
          <span class="price">{{ getCurrentPrice(it) }}</span>
          <span v-if="getOldPrice(it)" class="old">{{ getOldPrice(it) }}</span>
          <span v-if="getDiscountPercent(it)" class="disc">−{{ getDiscountPercent(it) }}%</span>
        </div>
        <div class="name">{{ getDisplayName(it) }}</div>
        <div v-if="it.rating || it.reviews_count" class="rating-row">
          <div class="rating-item">
            <v-icon size="16" color="#ffb400">mdi-star</v-icon>
            <span class="rating">{{ it.rating }}</span>
          </div>
          <div class="rating-item">
            <v-icon size="16" color="#9aa1ac">mdi-message-text-outline</v-icon>
            <span class="reviews">{{ it.reviews_count }}</span>
          </div>
          <div class="rating-item">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="#005bff">
              <path d="M8.999 6.994c-.704.196-1.13.728-1.042 1.073.09.345.715.585 1.418.388.704-.196 1.13-.728 1.042-1.073-.09-.345-.714-.585-1.418-.388"/>
              <path d="M14 8c0 3.723-2.277 6-6 6-2.73 0-4.683-1.225-5.53-3.346.261.15.57.214.878.161.855-.146 1.364-1.063 1.058-1.907-.226-.625-.859-1.005-1.492-.896-.38.065-.692.282-.894.578A9 9 0 0 1 2 8c0-3.723 2.277-6 6-6 2.672 0 4.6 1.173 5.475 3.213a.31.31 0 0 0-.291.001.34.34 0 0 0-.158.389l.274 1.065-2.017-.91-.02-.006c-.063-.013-.123.048-.105.118l.566 2.2.011.034a.32.32 0 0 0 .313.22.33.33 0 0 0 .293-.417l-.276-1.074 1.93.87Q14 7.85 14 8M8.834 6.354c-1.019.284-1.686 1.128-1.491 1.885s1.178 1.14 2.197.856 1.687-1.128 1.492-1.885-1.18-1.14-2.198-.856m-2.093.65-1.93.537-.032.011a.337.337 0 0 0-.169.459.32.32 0 0 0 .378.166l.858-.239-.863 2.206-.006.02c-.01.065.048.125.114.107l2.094-.584.034-.012a.34.34 0 0 0 .214-.33c-.014-.216-.21-.354-.4-.301l-1.046.291.862-2.204.006-.02c.011-.066-.048-.126-.114-.108"/>
              <path d="M3.853 9.314c-.065-.494-.557-.789-1-.6a.76.76 0 0 0-.443.798c.064.494.556.79 1 .601a.76.76 0 0 0 .443-.799"/>
            </svg>
            <span class="market-badge">Маркет</span>
          </div>
        </div>
      </div>
    </div>
    <div v-else-if="configLoaded" class="section">
      <v-row class="skeleton-grid">
        <v-col v-for="n in 12" :key="n" cols="2">
          <v-skeleton-loader type="image, article" elevation="0"></v-skeleton-loader>
        </v-col>
      </v-row>
    </div>
  </div>

  <div class="grid">
    <div v-if="kvStoreLoaded" class="cards">
      <div v-for="(it, i) in gridItemsResolved5" :key="'g'+i" class="card" @click="openItem(it)">
        <div class="thumb">
          <div v-if="it.original_tag" class="sale-badge">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 2.065c-2-.643-.667 3.71-2 3.71-.667 0-.806-1.258-1.339-1.258C3.994 4.517 2 6.56 2 9.13 2 11.474 3.333 14 6 14c.667 0 1-.212.625-.62-1.875-2.044-1.358-4.042-.63-3.808.94.302 1.823 1.779 2.557-1.35.186-.847.653-.622 1.266 0 .921.932 1.402 2.94-.36 5.157-.291.367.209.621 1.021.621C12.23 14 14 12.106 14 9.13c0-4.004-4-6.423-6-7.065"/>
            </svg>
            Распродажа
          </div>
          <v-img :src="getImageSrc(it.thumbnail || it.img)" cover />
          <button
            type="button"
            class="fav-btn"
            :class="{ active: isFav(it) }"
            :aria-label="isFav(it) ? 'Убрать из избранного' : 'Добавить в избранное'"
            :title="isFav(it) ? 'Убрать из избранного' : 'Добавить в избранное'"
            @click.stop.prevent="toggleFav(it)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M7 5a4 4 0 0 0-4 4c0 3.552 2.218 6.296 4.621 8.22A21.5 21.5 0 0 0 12 19.91a21.6 21.6 0 0 0 4.377-2.69C18.78 15.294 21 12.551 21 9a4 4 0 0 0-4-4c-1.957 0-3.652 1.396-4.02 3.2a1 1 0 0 1-1.96 0C10.652 6.396 8.957 5 7 5m5 17c-.316-.02-.56-.147-.848-.278a23.5 23.5 0 0 1-4.781-2.942C3.777 16.705 1 13.449 1 9a6 6 0 0 1 6-6 6.18 6.18 0 0 1 5 2.568A6.18 6.18 0 0 1 17 3a6 6 0 0 1 6 6c0 4.448-2.78 7.705-5.375 9.78a23.6 23.6 0 0 1-4.78 2.942c-.543.249-.732.278-.845.278"/>
            </svg>
          </button>
        </div>
        <div class="price-row">
          <span class="price">{{ getCurrentPrice(it) }}</span>
          <span v-if="getOldPrice(it)" class="old">{{ getOldPrice(it) }}</span>
          <span v-if="getDiscountPercent(it)" class="disc">−{{ getDiscountPercent(it) }}%</span>
        </div>
        <div class="name">{{ getDisplayName(it) }}</div>
        <div v-if="it.rating || it.reviews_count" class="rating-row">
          <div class="rating-item">
            <v-icon size="16" color="#ffb400">mdi-star</v-icon>
            <span class="rating">{{ it.rating }}</span>
          </div>
          <div class="rating-item">
            <v-icon size="16" color="#9aa1ac">mdi-message-text-outline</v-icon>
            <span class="reviews">{{ it.reviews_count }}</span>
          </div>
          <div class="rating-item">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="#005bff">
              <path d="M8.999 6.994c-.704.196-1.13.728-1.042 1.073.09.345.715.585 1.418.388.704-.196 1.13-.728 1.042-1.073-.09-.345-.714-.585-1.418-.388"/>
              <path d="M14 8c0 3.723-2.277 6-6 6-2.73 0-4.683-1.225-5.53-3.346.261.15.57.214.878.161.855-.146 1.364-1.063 1.058-1.907-.226-.625-.859-1.005-1.492-.896-.38.065-.692.282-.894.578A9 9 0 0 1 2 8c0-3.723 2.277-6 6-6 2.672 0 4.6 1.173 5.475 3.213a.31.31 0 0 0-.291.001.34.34 0 0 0-.158.389l.274 1.065-2.017-.91-.02-.006c-.063-.013-.123.048-.105.118l.566 2.2.011.034a.32.32 0 0 0 .313.22.33.33 0 0 0 .293-.417l-.276-1.074 1.93.87Q14 7.85 14 8M8.834 6.354c-1.019.284-1.686 1.128-1.491 1.885s1.178 1.14 2.197.856 1.687-1.128 1.492-1.885-1.18-1.14-2.198-.856m-2.093.65-1.93.537-.032.011a.337.337 0 0 0-.169.459.32.32 0 0 0 .378.166l.858-.239-.863 2.206-.006.02c-.01.065.048.125.114.107l2.094-.584.034-.012a.34.34 0 0 0 .214-.33c-.014-.216-.21-.354-.4-.301l-1.046.291.862-2.204.006-.02c.011-.066-.048-.126-.114-.108"/>
              <path d="M3.853 9.314c-.065-.494-.557-.789-1-.6a.76.76 0 0 0-.443.798c.064.494.556.79 1 .601a.76.76 0 0 0 .443-.799"/>
            </svg>
            <span class="market-badge">Маркет</span>
          </div>
        </div>
      </div>
    </div>
    <div v-else-if="configLoaded" class="section">
      <v-row class="skeleton-grid">
        <v-col v-for="n in 12" :key="n" cols="2">
          <v-skeleton-loader type="image, article" elevation="0"></v-skeleton-loader>
        </v-col>
      </v-row>
    </div>
  </div>

    </div>

    <shop-login-dialog v-model="loginDialog" :loginData="testData && testData.login_data" @success="onLoginSuccess" />
  </div>
  <div v-else />
</template>

<script>
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import { GET_TRACK_CONFIG, GET_KV_STORE } from '@/store/actions.type';
import MenuBar from './components/MenuBar.vue';
import ShopLoginDialog from './components/ShopLoginDialog.vue';
import SearchBar from '../../ui/SearchBar.vue';
import ShopItem from './components/ShopItem.vue';
import { shopAssets } from '@/assets/shop-assets.js';
import { syncMockLoggedInFromTrack, setCurrentUsername, getShopFavorites, toggleShopFavorite, getCurrentUsername } from '@/utils/localCache.js';
import { StateDelayMixin } from '@/common/stateDelayMixin.js';
import { benchUserContextMixin } from '@/common/benchUserContextMixin.js';
import { _logActivity } from '@/common/trackHelper';
import { resolveAssetUrl } from '@/common/cdnUrls';

export default defineComponent({
  name: 'ShopMain',
  mixins: [benchUserContextMixin,StateDelayMixin],
  components: { MenuBar, ShopLoginDialog, SearchBar, ShopItem },
  data() { return { loginDialog: false, loggedIn: false, favorites: [], kvStoreReady: false }; },
  computed: {
    ...mapGetters(['trackConfig', 'kvStore']),
    isLoggedIn() { return this.loggedIn; },
    configLoaded() { return this.trackConfig && Object.keys(this.trackConfig).length > 0; },
    kvStoreLoaded() { return this.kvStoreReady; },
    common() { return (this.trackConfig && this.trackConfig.common_elements) || {}; },
    testData() { return (this.trackConfig && this.trackConfig.test_data) || {}; },
    gridItemsResolved() { return this.resolveGridItems('grid'); },
    gridItemsResolved2() { return this.resolveGridItems('grid2'); },
    gridItemsResolved3() { return this.resolveGridItems('grid3'); },
    gridItemsResolved4() { return this.resolveGridItems('grid4'); },
    gridItemsResolved5() { return this.resolveGridItems('grid5'); }
  },
  methods: {
    resolveGridItems(gridKey) {
      const src = (this.common && this.common[gridKey] && this.common[gridKey].items) || [];
      const kv = this.kvStore || {};
      return src
        .map(it => (it && it.kv_id && kv[it.kv_id]) ? { ...kv[it.kv_id], ...it } : null)
        .filter(Boolean);
    },
    openLoginDialog() { this.loginDialog = true; },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = this.benchSessionUser || 'guest';
      setCurrentUsername(username);
    },
    getImageSrc(src) {
      return resolveAssetUrl(src);
    },
    formatCurrency(value, currencyCode) {
      const num = Number(value || 0);
      if (!currencyCode || currencyCode === 'RUB') {
        const formatted = num.toLocaleString('ru-RU', { minimumFractionDigits: num % 1 === 0 ? 0 : 2, maximumFractionDigits: 2 });
        return `${formatted}\u00A0₽`;
      }
      return `${num.toLocaleString('ru-RU')} ${currencyCode}`.trim();
    },
    roundCurrency(value) { return Math.round(Number(value || 0)); },
    getBasePriceValue(it) {
      if (!it) return 0;
      const raw = typeof it.data_price === 'number' ? it.data_price : Number(it.price || it.price_current || 0);
      return this.roundCurrency(raw);
    },
    getDisplayName(it) {
      return it.name || it.title || it.product_id || '';
    },
    getItemKey(it) {
      return it.kv_id || it.key || it.id || it.product_id || (it.to_state ? String(it.to_state).replace(/^item_/, '') : '') || '';
    },
    refreshFavorites() {
      try {
        const username = getCurrentUsername();
        this.favorites = (getShopFavorites(username) || []).map(String);
      } catch(e) { this.favorites = []; }
    },
    isFav(it) {
      const key = this.getItemKey(it);
      return key ? this.favorites.includes(String(key)) : false;
    },
    toggleFav(it) {
      const key = this.getItemKey(it);
      if (!key) return;
      const username = getCurrentUsername();
      const wasFav = this.isFav(it);
      toggleShopFavorite(username, String(key));
      this.refreshFavorites();
      const raw = String(key);
      const itemId = raw.startsWith('item_') ? raw : `item_${raw}`;
      _logActivity(this, { type: wasFav ? 'remove_favorites' : 'add_favorites', item_id: itemId });
    },
    getCurrentPrice(it) { return this.formatCurrency(this.getBasePriceValue(it), it.currency); },
    getOldPrice(it) {
      // New KV may not include old price; try to derive if discount available and price_old present
      if (it.price_old) {
        return this.formatCurrency(it.price_old, it.currency);
      }
      return '';
    },
    getDiscountPercent(it) {
      if (!it || !it.price_old) return '';
      if (it.discount_percent) return it.discount_percent;
      if (it.discount) return String(it.discount).replace('%','');
      return '';
    },
    openItem(it) {
      const to_state = "item_" + it.id;
      const to_view_type = 'bench_catalog_item';
      this.$router.push({ name: to_view_type, params: { state_id: to_state, track_id: this.$route.params.track_id } });
    },
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig);
          const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || '';
          if (kvPath) {
            this.$store.dispatch(GET_KV_STORE, { kvPath }).then(() => {
              this.kvStoreReady = true;
            });
          } else {
            this.kvStoreReady = true;
          }
          if (!this.trackConfig[this.$route.params.state_id]) {
            this.$router.push({ name: 'state_not_found' });
          }
          this.applyStateDelay();
        });
    }
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || '';
      if (kvPath && !this.kvStoreReady) {
        this.$store.dispatch(GET_KV_STORE, { kvPath }).then(() => {
          this.kvStoreReady = true;
        });
      } else if (!kvPath) {
        this.kvStoreReady = true;
      }
      this.applyStateDelay();
    }
    this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig);
    this.refreshFavorites();
  }
});
</script>

<style src="@/assets/books.css"></style>
<style src="@/assets/shop.css"></style>

<style scoped>
.bench-market .menu-bg-wrap { position: relative; }
.bench-market .card { position: relative; }
</style>

