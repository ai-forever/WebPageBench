<template>
  <div v-if="configLoaded" class="bench-market">
    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isLoggedIn"
      :prefill-query="query"
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

    <!-- SEARCH TAGS -->
    <div v-if="pageSuggestionTags.length" class="page-suggest-tags">
      <div
        v-for="(t, i) in pageSuggestionTags"
        :key="i"
        class="suggestion-tag"
        @click="appendTagToHeaderInput(t)"
      >{{ t }}</div>
    </div>

    <div class="search-section">
      <div class="search-layout">
        <div class="filters-panel">

          <div v-if="categoriesAvailable.length" class="filter-group">
            <div class="filter-group-title">Категория</div>
            <v-radio-group hide-details v-model="filters.category" density="default">
              <v-radio :value="null" label="Все категории" hide-details :true-icon="RadioIcon" :false-icon="RadioIcon"></v-radio>
              <v-radio v-for="cat in categoriesAvailable" :key="cat" :value="cat" :label="cat" hide-details :true-icon="RadioIcon" :false-icon="RadioIcon"></v-radio>
            </v-radio-group>
          </div>

          <div v-if="saleAvailable" class="filter-row">
            <div class="filter-label">Распродажа</div>
            <v-switch
              class="oz-switch"
              v-model="filters.onlySale"
              inset
              density="compact"
              color="#0b63ff"
              :false-icon="null"
              hide-details
            ></v-switch>
          </div>

          <div v-if="brandsAvailable.length" class="filter-group">
            <div class="filter-group-title">Бренд</div>
            <div v-for="b in brandsAvailable" :key="b">
              <v-checkbox
                class="oz-checkbox"
                v-model="filters.brands"
                :value="b"
                :label="b"
                density="compact"
                hide-details
                :true-icon="CheckboxOnIcon"
                :false-icon="null"
              ></v-checkbox>
            </div>
          </div>

          <div v-if="ratingAvailable" class="filter-group">
            <div class="filter-group-title">Рейтинг</div>
            <v-checkbox
              class="oz-checkbox"
              v-model="filters.rating4"
              :value="true"
              label="4+ звезды"
              density="compact"
              hide-details
              :true-icon="CheckboxOnIcon"
              :false-icon="null"
            ></v-checkbox>
          </div>

          <div v-if="priceAvailable" class="filter-group">
            <div class="filter-group-title">Цена</div>
            <div class="price-inputs">
              <v-text-field v-model.number="filters.priceMin" hide-details variant="outlined" density="compact"/>
              <v-text-field v-model.number="filters.priceMax" hide-details variant="outlined"  density="compact"/>
            </div>
            <v-radio-group v-model="filters.priceBucket" density="compact" class="oz-radio">
              <v-radio v-for="b in priceBuckets" :key="b.value" :value="b.value" :label="b.label" hide-details :true-icon="PriceRadioOnIcon" :false-icon="PriceRadioOffIcon" />
              <v-radio :value="null" label="Неважно" hide-details :true-icon="PriceRadioOnIcon" :false-icon="PriceRadioOffIcon" />
            </v-radio-group>
          </div>

          <div v-for="df in dynamicProps" :key="df.key" class="filter-group">
            <div class="filter-group-title">{{ df.key }}</div>
            <div v-for="val in df.values" :key="val">
              <v-checkbox
                class="oz-checkbox"
                v-model="filters.dynamic[df.key]"
                :value="val"
                :label="val"
                density="compact"
                hide-details
                :true-icon="CheckboxOnIcon"
                :false-icon="null"
              ></v-checkbox>
            </div>
          </div>
        </div>

        <div class="container">
          <!-- <div class="search-label">{{ searchTitle }}</div> -->
          <div v-if="visibleItems.length" class="results-grid">
            <shop-item
              v-for="(it, i) in visibleItems"
              :key="'s'+i"
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
              :show-basket="true"
              :logged-in="isLoggedIn"
              :username="username"
              :on-open-login="openLoginDialog"
            />
          </div>
          <div v-else class="no-results">Ничего не найдено</div>
          <div v-if="hasMore" class="show-more-wrap">
            <v-btn variant="flat" @click="showMore">Показать ещё</v-btn>
          </div>
        </div>
      </div>
    </div>

    <shop-login-dialog v-model="loginDialog" :loginData="testData && testData.login_data" />
  </div>
</template>

<script>
import { defineComponent, h, nextTick } from 'vue';
import { mapGetters } from 'vuex';
import { benchUserContextMixin } from '@/common/benchUserContextMixin.js';
import SearchBar from '../../ui/SearchBar.vue';
import ShopItem from './components/ShopItem.vue';
import MenuBar from './components/MenuBar.vue';
import ShopLoginDialog from './components/ShopLoginDialog.vue';
import { GET_TRACK_CONFIG, GET_KV_STORE } from '@/store/actions.type';
import { syncMockLoggedInFromTrack, getShopFavorites, toggleShopFavorite, getCurrentUsername } from '@/utils/localCache.js';
import { _logActivity } from '@/common/trackHelper';
import { resolveAssetUrl } from '@/common/cdnUrls';

const RadioIcon = () => h('svg', {
  xmlns: 'http://www.w3.org/2000/svg',
  width: '24',
  height: '24',
  class: 'c1y_11',
  style: 'color: var(--graphicTertiary);'
}, [h('path', {
  fill: 'currentColor',
  d: 'M14.615 6.497a1.5 1.5 0 0 1-.112 2.118L10.743 12l3.76 3.385a1.5 1.5 0 0 1-2.006 2.23l-5-4.5a1.5 1.5 0 0 1 0-2.23l5-4.5a1.5 1.5 0 0 1 2.118.112'
})]);

const CheckboxOnIcon = () => h('svg', {
  xmlns: 'http://www.w3.org/2000/svg',
  width: '16',
  height: '16',
  class: 'oz-checkbox-svg'
}, [h('path', {
  fill: 'currentColor',
  d: 'M12.707 5.293a1 1 0 0 1 0 1.414l-5 5a1 1 0 0 1-1.414 0l-3-3a1 1 0 0 1 1.414-1.414L7 9.586l4.293-4.293a1 1 0 0 1 1.414 0'
})]);

const CheckboxOffIcon = () => h('svg', {
  xmlns: 'http://www.w3.org/2000/svg',
  width: '16',
  height: '16',
  class: 'oz-checkbox-svg'
}, [
  h('circle', { cx: '10', cy: '10', r: '9.5', fill: '#ffffff', stroke: '#cbd5e1', 'stroke-width': '1' })
]);

const PriceRadioOnIcon = () => h('svg', {
  xmlns: 'http://www.w3.org/2000/svg',
  width: '20',
  height: '20',
  class: 'oz-radio-svg'
}, [
  h('circle', { cx: '10', cy: '10', r: '10', fill: '#0b63ff' }),
  h('circle', { cx: '10', cy: '10', r: '5', fill: '#ffffff' })
]);

const PriceRadioOffIcon = () => h('svg', {
  xmlns: 'http://www.w3.org/2000/svg',
  width: '20',
  height: '20',
  class: 'oz-radio-svg'
}, [
  h('circle', { cx: '10', cy: '10', r: '9.5', fill: '#ffffff', stroke: '#cbd5e1', 'stroke-width': '1' })
]);

export default defineComponent({
  name: 'ShopSearch',
  mixins: [benchUserContextMixin],
  components: { SearchBar, ShopLoginDialog, ShopItem, MenuBar },
  data() {
    return {
      loggedIn: false,
      loginDialog: false,
      itemsSearchList: [],
      foundItemsAll: [],
      showCount: 15,
      favorites: [],
      filters: {
        category: null,
        brands: [],
        onlySale: false,
        rating4: false,
        priceMin: null,
        priceMax: null,
        priceBucket: null,
        dynamic: {}
      },
      RadioIcon,
      PriceRadioOnIcon,
      PriceRadioOffIcon,
      CheckboxOnIcon,
      CheckboxOffIcon,
    };
  },
  computed: {
    ...mapGetters(['trackConfig', 'kvStore']),
    isLoggedIn() { return this.loggedIn; },
    configLoaded() { return this.trackConfig && Object.keys(this.trackConfig).length > 0; },
    common() { return (this.trackConfig && this.trackConfig.common_elements) || {}; },
    testData() { return (this.trackConfig && this.trackConfig.test_data) || {}; },
    username() { const u = this.benchSessionUser || 'guest'; return this.loggedIn ? u : 'shop_guest'; },
    query() { return (this.$route && this.$route.query && this.$route.query.q) || ''; },
    scope() { return (this.$route && this.$route.query && this.$route.query.scope) || ''; },
    searchTitle() { return ''; },

    pageSuggestionTags() {
      try {
        const q = String(this.query || '').trim().toLowerCase();
        if (!q) return [];
        const map = (this.common && this.common.suggestions_list) || {};
        const keys = Object.keys(map || {});
        const ranked = keys
          .map(k => ({ key: k, sc: this.pageFuzzyScore(q, String(k).toLowerCase()) }))
          .filter(x => x.sc > 0)
          .sort((a,b) => b.sc - a.sc)
          .slice(0, 5)
          .map(x => x.key);
        const out = [];
        ranked.forEach(k => {
          const arr = (map[k] && map[k].tags) || [];
          (arr || []).forEach(t => { const s = String(t); if (s && !out.includes(s)) out.push(s); });
        });
        return out;
      } catch(e) { return []; }
    },

    content() { const st = this.trackConfig[this.$route.params.state_id]; return st && st.content || {}; },
    userData() { return (this.testData && this.testData.user_data) || {}; },
    userFullName() { const n = this.userData && this.userData.name; return n || 'Пользователь'; },

    brandsAvailable() {
      const set = new Set();
      (this.foundItemsAll || []).forEach(it => { if (it && it.brand) set.add(String(it.brand)); });
      return Array.from(set).sort();
    },
    categoriesAvailable() {
      const set = new Set();
      (this.foundItemsAll || []).forEach(it => { const c = this.getCategory(it); if (c) set.add(c); });
      return Array.from(set).sort();
    },
    saleAvailable() { return (this.foundItemsAll || []).some(it => this.hasDiscount(it)); },
    ratingAvailable() { return (this.foundItemsAll || []).some(it => Number(it.rating) > 0); },
    priceAvailable() { return (this.foundItemsAll || []).some(it => this.readPrice(it) != null); },
    priceMinMax() {
      const prices = (this.foundItemsAll || []).map(it => this.readPrice(it)).filter(v => typeof v === 'number');
      if (!prices.length) return { min: 0, max: 0 };
      return { min: Math.min(...prices), max: Math.max(...prices) };
    },
    priceBuckets() {
      const { min, max } = this.priceMinMax;
      if (min >= max) return [];
      const step = (max - min) / 4;
      const buckets = [
        { from: min, to: Math.round(min + step), label: `до ${this.formatCurrency(Math.round(min + step), 'RUB')}` },
        { from: Math.round(min + step), to: Math.round(min + 2*step), label: `${this.formatCurrency(Math.round(min + step), 'RUB')}–${this.formatCurrency(Math.round(min + 2*step), 'RUB')}` },
        { from: Math.round(min + 2*step), to: Math.round(min + 3*step), label: `${this.formatCurrency(Math.round(min + 2*step), 'RUB')}–${this.formatCurrency(Math.round(min + 3*step), 'RUB')}` },
        { from: Math.round(min + 3*step), to: max, label: `${this.formatCurrency(Math.round(min + 3*step), 'RUB')} и дороже` }
      ];
      return buckets.map((b, idx) => ({ value: `${b.from}-${b.to}-${idx}`, label: b.label, from: b.from, to: b.to }));
    },
    dynamicProps() {
      const map = {};
      (this.foundItemsAll || []).forEach(it => {
        const props = it && it.properties || {};
        Object.keys(props).forEach(k => {
          if (!map[k]) map[k] = new Set();
          const val = String(props[k]).trim();
          if (val) map[k].add(val);
        });
      });
      const arr = Object.keys(map).map(k => ({ key: k, values: Array.from(map[k]).slice(0, 12) }));
      return arr.filter(x => x.values.length >= 2);
    },
    filteredItems() {
      const list = this.foundItemsAll || [];
      const f = this.filters || {};
      const brandSet = new Set((f.brands || []).map(x => String(x)));
      const priceMin = f.priceMin != null ? Number(f.priceMin) : this.priceMinMax.min;
      const priceMax = f.priceMax != null ? Number(f.priceMax) : this.priceMinMax.max;
      return list.filter(it => {
        if (f.category && this.getCategory(it) !== f.category) return false;
        if (brandSet.size && !brandSet.has(String(it.brand))) return false;
        if (f.onlySale && !this.hasDiscount(it)) return false;
        if (f.rating4 && !(Number(it.rating) >= 4)) return false;
        const price = this.readPrice(it);
        if (typeof price === 'number' && (price < priceMin || price > priceMax)) return false;
        const dyn = f.dynamic || {};
        for (const k of Object.keys(dyn)) {
          const selected = dyn[k] || [];
          if (selected.length === 0) continue;
          const val = it && it.properties && it.properties[k];
          if (!selected.includes(String(val))) return false;
        }
        return true;
      });
    },
    visibleItems() { return (this.filteredItems || []).slice(0, this.showCount); },
    hasMore() { return (this.filteredItems || []).length > this.showCount; }
  },
  methods: {
    appendTagToHeaderInput(t) {
      // navigate updating query without reloading header component state
      const q = String(this.query || '').trim();
      const add = String(t || '').trim();
      const next = q ? `${q} ${add}` : add;
      const query = { q: next };
      if (this.scope) query.scope = this.scope;
      this.$router.push({ name: 'bench_catalog_search', params: { state_id: 'state_search', track_id: this.$route.params.track_id }, query });
    },
    pageFuzzyScore(q, key) {
      const query = String(q || '').toLowerCase();
      const text = String(key || '').toLowerCase();
      if (!query || !text) return 0;
      let qi = 0, score = 0, streak = 0;
      for (let i = 0; i < text.length && qi < query.length; i++) {
        if (text[i] === query[qi]) { qi++; streak++; score += 2 * streak; } else { streak = 0; }
      }
      if (qi < query.length) return 0;
      if (text.startsWith(query)) score += 10;
      return score - Math.max(0, text.length - query.length);
    },
    openLoginDialog() { this.loginDialog = true; },
    getTrackConfig() { this.$store.dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id }).then(() => { this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig); const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || ''; if (kvPath) return this.$store.dispatch(GET_KV_STORE, { kvPath }); return Promise.resolve(); }); },
    buildItemsList() {
      try {
        const list = [];
        const kv = this.kvStore || {};
        Object.keys(kv).forEach(key => {
          const it = kv[key];
          if (!it) return;
          const name = this.getDisplayName(it);
          const brand = it.brand || '';
          const cat = this.getCategory(it) || '';
          const props = it.properties ? Object.values(it.properties).join(' ') : '';
          const label = [name, brand, cat, props].filter(Boolean).join(' ');
          if (label) list.push({ key, label: String(label), item: it });
        });
        this.itemsSearchList = list;
      } catch(e) { this.itemsSearchList = []; }
    },
    scoreLabel(query, label) {
      const q = String(query || '').trim().toLowerCase();
      const t = String(label || '').toLowerCase();
      if (!q || !t) return 0;
      let sc = 0;
      if (t.startsWith(q)) sc += 100;
      if (t.includes(q)) sc += 40;
      const words = q.split(/\s+/).filter(Boolean);
      for (const w of words) {
        if (t.startsWith(w)) sc += 25;
        if (t.includes(w)) sc += 10;
        let i = 0; for (const ch of t) { if (ch === w[i]) i++; }
        if (i >= Math.max(1, w.length - 1)) sc += 5;
      }
      sc -= Math.min(20, Math.floor(t.length / 6));
      return sc;
    },
    runSearch() {
      const q = this.query;
      if (!q) { this.foundItemsAll = []; return; }
      const ranked = this.itemsSearchList
        .map(x => ({ ...x, sc: this.scoreLabel(q, x.label) + (this.scope ? this.scoreLabel(this.scope, x.label) : 0) }))
        .filter(x => x.sc > 0)
        .sort((a,b) => b.sc - a.sc);
      this.foundItemsAll = ranked.map(x => x.item);
      const { min, max } = this.priceMinMax;
      this.filters.priceMin = Math.floor(min);
      this.filters.priceMax = Math.ceil(max);
      this.filters.priceBucket = null;
      this.filters.dynamic = {};
      nextTick(() => this.ensureDynamicArrays());
    },
    ensureDynamicArrays() {
      const dyn = this.filters.dynamic || {};
      (this.dynamicProps || []).forEach(df => {
        const key = df && df.key;
        if (!key) return;
        if (!Array.isArray(dyn[key])) dyn[key] = [];
      });
      this.filters.dynamic = { ...dyn };
    },
    showMore() { this.showCount += 15; },
    refreshFavorites() {
      try {
        const username = getCurrentUsername();
        this.favorites = (getShopFavorites(username) || []).map(String);
      } catch(e) { this.favorites = []; }
    },
    getItemKey(it) { return it.kv_id || it.key || it.id || it.product_id || (it.to_state ? String(it.to_state).replace(/^item_/, '') : '') || ''; },
    isFav(it) { const key = this.getItemKey(it); return key ? this.favorites.includes(String(key)) : false; },
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
    openItem(it) {
      const to_state = it.to_state || (it.id ? `item_${it.id}` : undefined);
      const to_view_type = it.to_view_type || 'bench_catalog_item';
      if (to_state) this.$router.push({ name: to_view_type, params: { state_id: to_state, track_id: this.$route.params.track_id } });
    },
    getImageSrc(s) { return resolveAssetUrl(s); },
    getDisplayName(it) { return it.name || it.title || it.product_id || ''; },
    roundCurrency(value) { return Math.round(Number(value || 0)); },
    getBasePriceValue(it) {
      if (!it) return 0;
      const raw = typeof it.data_price === 'number' ? it.data_price : Number(it.price || it.price_current || 0);
      return this.roundCurrency(raw);
    },
    readPrice(it) { return this.getBasePriceValue(it); },
    formatCurrency(value, currencyCode) {
      const num = Number(value || 0);
      if (!currencyCode || currencyCode === 'RUB' || currencyCode === '₽') {
        const formatted = num.toLocaleString('ru-RU', { minimumFractionDigits: num % 1 === 0 ? 0 : 2, maximumFractionDigits: 2 });
        return `${formatted}\u00A0₽`;
      }
      return `${num.toLocaleString('ru-RU')} ${currencyCode}`.trim();
    },
    getCurrentPrice(it) { return this.formatCurrency(this.readPrice(it), it.currency); },
    getOldPrice(it) {
      if (it && it.price_old) return this.formatCurrency(it.price_old, it.currency);
      return '';
    },
    getDiscountPercent(it) { if (!it || !it.price_old) return ''; if (it.discount_percent) return it.discount_percent; if (it.discount) return String(it.discount).replace('%',''); return ''; },
    hasDiscount(it) { return !!(this.getDiscountPercent(it) || (typeof it.price_old === 'number')); },
    getCategory(it) {
      const bc = Array.isArray(it && it.breadcrumbs) ? it.breadcrumbs : [];
      if (bc.length === 0) return '';
      const last = bc[bc.length - 1] && bc[bc.length - 1].label;
      if (it.brand && last && String(last).toLowerCase() === String(it.brand).toLowerCase() && bc.length >= 2) {
        return bc[bc.length - 2].label;
      }
      return last || '';
    }
  },
  watch: {
    kvStore: { deep: true, handler() { this.buildItemsList(); this.runSearch(); } },
    query() { this.runSearch(); },
    scope() { this.runSearch(); },
    dynamicProps: { deep: true, handler() { this.ensureDynamicArrays(); } },
    'filters.priceBucket'(v) {
      if (!v) {
        // "Неважно": clear explicit bounds so filtering uses full range
        this.filters.priceMin = null;
        this.filters.priceMax = null;
        return;
      }
      const b = (this.priceBuckets || []).find(x => x.value === v);
      if (b) { this.filters.priceMin = b.from; this.filters.priceMax = b.to; }
    },
    filters: { deep: true, handler() { this.showCount = 15; } }
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) this.getTrackConfig();
    this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig);
    this.buildItemsList();
    this.runSearch();
    this.refreshFavorites();
  }
});
</script>

<style src="@/assets/books.css"></style>
<style src="@/assets/shop.css"></style>

<style scoped>
.page-suggest-tags { max-width: var(--shop-max-width, 1400px); margin: 0 auto; padding: 20px 16px 8px 0px; display: flex; flex-wrap: wrap; gap: 10px; }
.page-suggest-tags .suggestion-tag { background: #f2f4f7; color: #001a34; border-radius: 14px; padding: 8px 12px; font-size: 14px; font-weight: 600; cursor: pointer; user-select: none; }
.page-suggest-tags .suggestion-tag:hover { background: #e9edf2; }
.search-section { max-width: var(--shop-max-width, 1400px); margin: 16px auto; padding: 0 0px; }
.search-layout { display: grid; grid-template-columns: 280px 1fr; gap: 16px; }
.filters-panel { background: #fff; border-radius: 16px; padding: 15px 20px; height: fit-content; }
.filters-title { font-weight: 900; margin-bottom: 8px; }
.filter-group { margin: 12px 0 12px; }
.filter-group-title { font-weight: 600; margin-bottom: 10px; margin-top: 15px; color: #15223b; }
.filter-row { display: flex; align-items: center; justify-content: space-between; padding: 6px 0; }
.filter-label { font-weight: 700; color: #15223b; }
.price-inputs { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 20px; }
/* .price-inputs:deep(.v-field__input) { padding: 0 12px; } */


.container .search-label { font-size: 24px; font-weight: 900; margin-bottom: 8px; }
.results-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.card { background: white; border: 0; padding: 12px; cursor: pointer; border-radius: 20px; }
.card:hover { background: white; }
.thumb { width: 100%; aspect-ratio: 3/4; border-radius: 8px; overflow: hidden; margin-bottom: 8px; position: relative; }
.thumb .fav-btn { position: absolute; right: 0px; top: 4px; min-width: 32px; height: 32px; }
.price-row { display: flex; align-items: baseline; gap: 8px; }
.price-row .price { color: #ff1f7d; font-weight: 800; font-size: 18px; }
.price-row .old { color: #9aa1ac; text-decoration: line-through; font-weight: 600; font-size: 14px; }
.disc { color: #ff1f7d; margin-left: 0; font-weight: 800; font-size: 14px; }
.rating-row { color: #6b7280; font-size: 12px; margin-top: 4px; display: flex; align-items: center; gap: 6px; }
.rating-row .rating { color: #1f2937; font-weight: 800; }
.rating-row .rating::after { content: '\2022'; color: #93a3b5; margin-left: 6px; }
.rating-row .reviews { color: #94a3b8; }
.tag { display: inline-block; background: #ff1f7d; color: #fff; border-radius: 12px; padding: 2px 8px; font-size: 12px; font-weight: 700; margin: 6px 0; }
.show-more-wrap { display: flex; justify-content: center; margin-top: 16px; }
.no-results { color: #6b7280; margin-top: 12px; }

.oz-checkbox :deep(.v-selection-control) { min-height: 20px; margin-bottom:5px; }
.oz-checkbox :deep(.v-selection-control__input) {
  width: 20px;
  height: 20px; 
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  margin-right: 8px;
}

.oz-checkbox :deep(.v-icon) {
  background-color: #fff;
  color: transparent;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  margin: -1px;
  padding: 2px;
  font-size: 10px !important;
}
.oz-checkbox :deep(.v-icon svg) { display: none; }
.oz-checkbox :deep(.v-selection-control--dirty .v-icon svg) { display: block; }
.oz-checkbox :deep(.v-selection-control--dirty .v-icon) {
  border-color: transparent;
  background-color: #0b63ff; 
  color: #fff; 
}
.oz-radio :deep(.v-selection-control) { min-height: 24px; margin-bottom:5px;}
.oz-radio :deep(.v-selection-control__input) { margin-right: 8px; }
.oz-radio :deep(.v-icon) {
  width: 20px;
  height: 20px;
}
.oz-checkbox :deep(.v-icon .oz-checkbox-svg) { display: block; }
.oz-checkbox :deep(.v-icon:has(svg)) { display: grid; place-items: center; }

/* МАРКЕТ-like switch styling */
.oz-switch :deep(.v-selection-control) { height: 28px; }
.oz-switch :deep(.v-switch__track) {
  background-color: #dadada;
  height: 32px;
  border-radius: 16px;
  opacity: 1;
}
.oz-switch :deep(.v-selection-control--dirty .v-switch__track) {
  background-color: #005bff;
}
.oz-switch :deep(.v-switch__thumb) {
  width: 26px;
  height: 26px;
  background-color: #fff;
  box-shadow: none;
  transform: translateX(0px);
  transition: transform .2s cubic-bezier(.85,0,.15,1), background-color .2s cubic-bezier(.85,0,.15,1);
}
.oz-switch :deep(.v-selection-control--dirty .v-switch__thumb) {
  transform: translateX(0px);
}
.oz-switch :deep(.v-switch__thumb .c75_3_3-a3) {
  position: absolute;
  left: 6px;
  top: 6px;
  color: #005bff;
  transform: scale(0.5);
}
.oz-switch :deep(.v-selection-control--dirty .v-switch__thumb .c75_3_3-a3) {
  transform: scale(1);
}
</style>

