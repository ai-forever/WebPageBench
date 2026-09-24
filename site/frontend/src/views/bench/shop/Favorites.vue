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
    <div class="fav-section">
      <div class="fav-layout">
        <div class="filters-panel">
          <div class="filters-title">Категория</div>
          <v-radio-group v-model="filters.category" density="compact">
            <v-radio :value="null" label="Все категории" hide-details></v-radio>
            <v-radio v-for="cat in categoriesAvailable" :key="cat" :value="cat" :label="cat" hide-details></v-radio>
          </v-radio-group>
        </div>
        <div class="container">
          <div class="search-label">Избранное</div>
          <div v-if="visibleItems.length" class="results-grid">
            <div class="card" v-for="fi in visibleItems" :key="fi.key" @click="openItem(fi.item)">
              <div class="thumb">
                <v-img :src="getImageSrc(fi.item && (fi.item.thumbnail || fi.item.img))" cover />
                <div class="img-badges" v-if="hasDiscount(fi.item)">
                  <v-chip class="sale-chip" size="small" variant="flat" color="#ff1f7d" text-color="#ffffff">Распродажа</v-chip>
                </div>
                <button
                  type="button"
                  class="fav-btn"
                  :class="{ active: isFavByKey(fi.key) }"
                  :aria-label="isFavByKey(fi.key) ? 'Убрать из избранного' : 'Добавить в избранное'"
                  :title="isFavByKey(fi.key) ? 'Убрать из избранного' : 'Добавить в избранное'"
                  @click.stop.prevent="toggleFavByKey(fi.key)"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
                    <path fill="currentColor" d="M7 5a4 4 0 0 0-4 4c0 3.552 2.218 6.296 4.621 8.22A21.5 21.5 0 0 0 12 19.91a21.6 21.6 0 0 0 4.377-2.69C18.78 15.294 21 12.551 21 9a4 4 0 0 0-4-4c-1.957 0-3.652 1.396-4.02 3.2a1 1 0 0 1-1.96 0C10.652 6.396 8.957 5 7 5m5 17c-.316-.02-.56-.147-.848-.278a23.5 23.5 0 0 1-4.781-2.942C3.777 16.705 1 13.449 1 9a6 6 0 0 1 6-6 6.18 6.18 0 0 1 5 2.568A6.18 6.18 0 0 1 17 3a6 6 0 0 1 6 6c0 4.448-2.78 7.705-5.375 9.78a23.6 23.6 0 0 1-4.78 2.942c-.543.249-.732.278-.845.278"/>
                  </svg>
                </button>
              </div>
              <div class="price-row">
                <span class="price">{{ getCurrentPrice(fi.item) }}</span>
                <span v-if="getOldPrice(fi.item)" class="old">{{ getOldPrice(fi.item) }}</span>
                <span v-if="getDiscountPercent(fi.item)" class="disc">-{{ getDiscountPercent(fi.item) }}%</span>
              </div>
              <div class="meta-line" v-if="hasDiscount(fi.item)"><v-icon size="16" color="#16a34a">mdi-check-circle</v-icon><span>Стало дешевле</span></div>
              <div class="name">{{ getDisplayName(fi.item) }}</div>
              <div v-if="fi.item && (fi.item.rating || fi.item.reviews_count)" class="rating-row">
                <v-icon size="16" color="#ffb400">mdi-star</v-icon>
                <span class="rating">{{ fi.item.rating }}</span>
                <span class="reviews">{{ fi.item.reviews_count }}</span>
              </div>
              <div class="bottom-controls" @click.stop>
                <template v-if="qty(fi.key) > 0">
                  <div class="qty">
                    <v-btn class="qty-btn" icon variant="text" color="#0b63ff" @click="dec(fi.key)"><v-icon size="20">mdi-minus</v-icon></v-btn>
                    <div class="qty-value">{{ qty(fi.key) }}</div>
                    <v-btn class="qty-btn" icon variant="text" color="#0b63ff" @click="inc(fi.key)"><v-icon size="20">mdi-plus</v-icon></v-btn>
                  </div>
                </template>
                <template v-else>
                  <v-btn class="buy-btn" color="#0b63ff" variant="flat" block @click="addToBasket(fi.key)"><v-icon size="20" style="margin-right:6px;">mdi-cart-outline</v-icon>Завтра</v-btn>
                </template>
              </div>
            </div>
          </div>
          <div v-else class="no-results">Пока пусто</div>
        </div>
      </div>
    </div>
    <shop-login-dialog v-model="loginDialog" :loginData="testData && testData.login_data" @success="onLoginSuccess" />
  </div>
</template>

<script>
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import { benchUserContextMixin } from '@/common/benchUserContextMixin.js';
import SearchBar from '../../ui/SearchBar.vue';
import MenuBar from './components/MenuBar.vue';
import { GET_TRACK_CONFIG, GET_KV_STORE } from '@/store/actions.type';
import { syncMockLoggedInFromTrack, setCurrentUsername, getShopFavorites, getShopBasket, setShopBasketItem, incrementShopBasketItem, getCurrentUsername, toggleShopFavorite } from '@/utils/localCache.js';
import ShopLoginDialog from './components/ShopLoginDialog.vue';
import { resolveAssetUrl } from '@/common/cdnUrls';

export default defineComponent({
  name: 'ShopFavorites',
  mixins: [benchUserContextMixin],
  components: { SearchBar, ShopLoginDialog, MenuBar },
  data() { return { loggedIn: false, loginDialog: false, favoritesKeys: [], basketMap: {}, filters: { category: null } }; },
  computed: {
    ...mapGetters(['trackConfig', 'kvStore']),
    isLoggedIn() { return this.loggedIn; },
    configLoaded() { return this.trackConfig && Object.keys(this.trackConfig).length > 0; },
    common() { return (this.trackConfig && this.trackConfig.common_elements) || {}; },
    testData() { return (this.trackConfig && this.trackConfig.test_data) || {}; },
    content() { const st = this.trackConfig[this.$route.params.state_id]; return st && st.content || {}; },
    username() { return this.benchSessionUser || 'guest'; },
    itemsAll() {
      const kv = this.kvStore || {};
      const keys = Array.isArray(this.favoritesKeys) ? this.favoritesKeys : [];
      return keys.map(k => ({ key: k, item: kv[k] || null })).filter(x => !!x.item);
    },
    categoriesAvailable() {
      const set = new Set();
      (this.itemsAll || []).forEach(x => { const c = this.getCategory(x.item); if (c) set.add(c); });
      return Array.from(set).sort();
    },
    visibleItems() {
      const cat = this.filters.category;
      return (this.itemsAll || []).filter(x => !cat || this.getCategory(x.item) === cat);
    }
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = this.benchSessionUser || 'guest';
      setCurrentUsername(username);
      this.refreshFavorites();
      this.refreshBasket();
    },
    refreshFavorites() { try { this.favoritesKeys = (getShopFavorites(getCurrentUsername()) || []).map(String); } catch(e) { this.favoritesKeys = []; } },
    refreshBasket() { if (!this.loggedIn) { this.basketMap = {}; return; } this.basketMap = getShopBasket(this.username) || {}; },
    qty(key) { return Number(this.basketMap[key] || 0); },
    inc(key) { incrementShopBasketItem(this.username, key, 1); this.refreshBasket(); },
    dec(key) { const cur = Number(this.basketMap[key] || 0); const next = Math.max(0, cur - 1); setShopBasketItem(this.username, key, next); this.refreshBasket(); },
    addToBasket(key) { if (!this.loggedIn) { this.openLoginDialog(); return; } const cur = Number(this.basketMap[key] || 0); setShopBasketItem(this.username, key, Math.max(1, cur + 1)); this.refreshBasket(); },
    openItem(it) { const to_state = it && (it.to_state || (it.id ? `item_${it.id}` : null) || (it.product_id ? `item_${it.product_id}` : null)); const to_view_type = it && (it.to_view_type || 'bench_catalog_item'); if (to_state) this.$router.push({ name: to_view_type, params: { state_id: to_state, track_id: this.$route.params.track_id } }); },
    getImageSrc(s) { return resolveAssetUrl(s); },
    getDisplayName(it) { return it && (it.name || it.title || it.product_id) || ''; },
    readPrice(it) { if (!it) return null; if (typeof it.data_price === 'number') return it.data_price; if (typeof it.price === 'number') return it.price; return null; },
    formatCurrency(value, currencyCode) { const num = Number(value || 0); if (!currencyCode || currencyCode === 'RUB' || currencyCode === '₽') { const formatted = num.toLocaleString('ru-RU', { minimumFractionDigits: num % 1 === 0 ? 0 : 2, maximumFractionDigits: 2 }); return `${formatted}\u00A0₽`; } return `${num.toLocaleString('ru-RU')} ${currencyCode}`.trim(); },
    getCurrentPrice(it) { return this.formatCurrency(this.readPrice(it), it && it.currency); },
    getOldPrice(it) { const val = (it && typeof it.price_old === 'number') ? it.price_old : null; return val != null ? this.formatCurrency(val, it && it.currency) : ''; },
    getDiscountPercent(it) { if (it && it.discount_percent) return it.discount_percent; if (it && it.discount) return String(it.discount).replace('%',''); return ''; },
    hasDiscount(it) { return !!(this.getDiscountPercent(it) || (typeof (it && it.price_old) === 'number')); },
    getCategory(it) {
      const bc = Array.isArray(it && it.breadcrumbs) ? it.breadcrumbs : [];
      if (bc.length === 0) return '';
      const last = bc[bc.length - 1] && bc[bc.length - 1].label;
      if (it.brand && last && String(last).toLowerCase() === String(it.brand).toLowerCase() && bc.length >= 2) {
        return bc[bc.length - 2].label;
      }
      return last || '';
    },
    isFavByKey(key) { return this.favoritesKeys.includes(String(key)); },
    toggleFavByKey(key) { if (!key) return; toggleShopFavorite(getCurrentUsername(), String(key)); this.refreshFavorites(); },
    getTrackConfig() {
      this.$store.dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id }).then(() => {
        this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig);
        this.refreshFavorites();
        this.refreshBasket();
      });
    }
  },
  watch: { loggedIn() { this.refreshFavorites(); this.refreshBasket(); } },
  mounted() { if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) this.getTrackConfig(); this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig); this.refreshFavorites(); this.refreshBasket(); }
});
</script>

<style src="@/assets/books.css"></style>
<style src="@/assets/shop.css"></style>

<style scoped>
.fav-section { max-width: var(--shop-max-width, 1400px); margin: 16px auto; padding: 0 16px; }
.fav-layout { display: grid; grid-template-columns: 280px 1fr; gap: 16px; }
.filters-panel {
  background: #fff;
  border-radius: 16px;
  padding: 12px;
  height: fit-content;
  color: #001a34;
}
.filters-title { font-weight: 900; margin-bottom: 8px; color: #001a34; }
.filters-panel :deep(.v-label) {
  color: #001a34 !important;
  opacity: 1 !important;
}
.filters-panel :deep(.v-selection-control__wrapper) {
  opacity: 1;
}
.container .search-label { font-size: 24px; font-weight: 900; margin-bottom: 8px; color: #001a34; }
.results-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.card { background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 12px; cursor: pointer; }
.card:hover { box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
.thumb { width: 100%; aspect-ratio: 3/4; border-radius: 12px; overflow: hidden; margin-bottom: 8px; position: relative; }
.img-badges { position: absolute; left: 8px; top: 8px; display: flex; gap: 6px; }
.thumb .fav-btn {
  position: absolute;
  right: 6px;
  top: 6px;
  width: 40px;
  height: 40px;
  min-width: 40px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: rgba(255,255,255,0.92);
  color: #cbd5e1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 4;
}
.thumb .fav-btn.active { color: #ff1f7d; }
.price-row { display: flex; align-items: baseline; gap: 8px; }
.price-row .price { color: #ff1f7d; font-weight: 900; font-size: 20px; }
.price-row .old { color: #9aa1ac; text-decoration: line-through; font-weight: 700; font-size: 14px; }
.disc { color: #ff1f7d; margin-left: 0; font-weight: 900; font-size: 14px; }
.meta-line { display: inline-flex; align-items: center; gap: 6px; color: #0a5f1a; margin: 6px 0; font-size: 13px; }
.name { color: #001a34; font-weight: 800; margin-top: 2px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 38px; }
.rating-row { color: #6b7280; font-size: 12px; margin-top: 4px; display: flex; align-items: center; gap: 6px; }
.rating-row .rating { color: #1f2937; font-weight: 800; }
.rating-row .rating::after { content: '\u2022'; color: #93a3b5; margin-left: 6px; }
.rating-row .reviews { color: #94a3b8; }
.bottom-controls { margin-top: 12px; }
.buy-btn { text-transform: none; font-weight: 900; height: 44px; border-radius: 12px; }
.qty { display: grid; grid-template-columns: 44px 1fr 44px; align-items: center; height: 44px; background: var(--bench-primary-light, #f3f6fb); border: 1px solid #e5e7eb; border-radius: 12px; }
.qty-value { text-align: center; font-weight: 900; color: #001a34; }
.qty-btn { min-width: 44px; height: 44px; }
.no-results { color: #6b7280; margin-top: 12px; }
@media (max-width: 1200px) { .results-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 900px) { .fav-layout { grid-template-columns: 1fr; } .results-grid { grid-template-columns: repeat(2, 1fr); } }
</style>

