<template>
  <div v-if="configLoaded" class="bench-grocery basket-page">
    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isUserLoggedIn"
    />
    <menu-bar :items="(common.menu_bar && common.menu_bar.items) || []" />

    <div v-if="!contentReady" class="loading-container">
      <v-progress-circular indeterminate color="primary" :size="64"></v-progress-circular>
    </div>

    <div v-else-if="itemsCount === 0" class="basket-placeholder">
      <div class="title section-title">Корзина</div>
      <div class="subtitle">Корзина пуста</div>
      <div class="hint">Добавьте товары с главной или из каталога</div>
      <div class="actions">
        <v-btn class="home" variant="text" @click="goHome">На главную</v-btn>
      </div>
    </div>

    <div v-else class="basket-main">
      <div class="title section-title">Корзина<sup>{{ uniqueItemsCount }}</sup></div>
      <div class="layout">
        <div class="left">
          <div class="items">
            <div class="basket-item" v-for="bi in basketResolvedItems" :key="bi.key">
              <div class="thumb">
                <v-img :src="groceryImageSrc(bi.item)" cover></v-img>
              </div>
              <div class="info">
                <div class="book-name">{{ (bi.item && bi.item.title) || bi.key }}</div>
                <div v-if="bi.item && bi.item.amount" class="author">{{ bi.item.amount }}</div>
                <div class="row-actions">
                  <a href="javascript:void(0)" class="action" @click="remove(bi.key)">
                    <v-icon size="18">mdi-trash-can-outline</v-icon>
                    <span>Удалить</span>
                  </a>
                </div>
              </div>
              <div class="qty-controls">
                <v-btn icon size="small" variant="text" @click="dec(bi.key)">
                  <v-icon size="16">mdi-minus</v-icon>
                </v-btn>
                <input type="text" :value="bi.count" class="qty-input" readonly />
                <v-btn icon size="small" variant="text" @click="inc(bi.key)">
                  <v-icon size="16">mdi-plus</v-icon>
                </v-btn>
              </div>
              <div class="price-block">
                <div class="price-current">{{ formatCurrency(lineTotal(bi), 'RUB') }}</div>
                <div v-if="hasDiscount(bi.item)" class="old-and-disc">
                  <span class="price-old">{{ formatCurrency(lineBase(bi), 'RUB') }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="right">
          <div class="summary">
            <div class="row"><span class="label">{{ itemsCountText }}</span><span class="value">{{ formatCurrency(totalBase, 'RUB') }}</span></div>
            <div class="row"><span class="label">Скидка</span><span class="value discount">{{ formatCurrency(totalDiscount, 'RUB') }}</span></div>
            <div class="divider" />
            <div class="row total"><span class="label">Итого</span><span class="value">{{ formatCurrency(totalFinal, 'RUB') }}</span></div>
            <v-btn class="purchase-btn" block @click="goCheckout">Перейти к оформлению</v-btn>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import { GET_TRACK_CONFIG, GET_KV_STORE } from '@/store/actions.type';
import { StateDelayMixin } from '@/common/stateDelayMixin.js';
import { ensureBenchDomainMerged, pushBenchRoute } from '@/common/benchNavigation';
import { isUnifiedBench } from '@/common/benchTheme';
import { groceryImageSrc } from '@/common/groceryImages';
import { _logActivity } from '@/common/trackHelper';
import {
  applyDefaultMockLoginFromTrackConfig,
  getGroceryBasket,
  getGroceryCurrentUser,
  incrementGroceryBasketItem,
  isGroceryLoggedIn,
  removeGroceryBasketItem,
  syncGrocerySessionFromTrackConfig,
} from '@/utils/localCache.js';
import SearchBar from '../../ui/SearchBar.vue';
import MenuBar from '../../ui/MenuBar.vue';

export default defineComponent({
  name: 'GroceryBasket',
  mixins: [StateDelayMixin],
  components: { SearchBar, MenuBar },
  data() {
    return {
      isUserLoggedIn: false,
      basketMap: {},
    };
  },
  computed: {
    ...mapGetters(['trackConfig', 'kvStore']),
    configLoaded() {
      return this.trackConfig && Object.keys(this.trackConfig).length > 0;
    },
    common() {
      return (this.trackConfig && this.trackConfig.common_elements) || {};
    },
    username() {
      return getGroceryCurrentUser() || 'guest';
    },
    basketResolvedItems() {
      const kv = this.kvStore || {};
      return Object.entries(this.basketMap || {})
        .map(([key, count]) => ({ key, count: Number(count) || 0, item: kv[key] || null }))
        .filter((bi) => bi.count > 0);
    },
    uniqueItemsCount() {
      return this.basketResolvedItems.length;
    },
    itemsCount() {
      return this.basketResolvedItems.reduce((sum, bi) => sum + Math.max(0, bi.count), 0);
    },
    itemsCountText() {
      const n = this.itemsCount;
      const mod10 = n % 10;
      const mod100 = n % 100;
      let word = 'товаров';
      if (mod10 === 1 && mod100 !== 11) word = 'товар';
      else if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) word = 'товара';
      return `${n} ${word}`;
    },
    totalBase() {
      return this.basketResolvedItems.reduce((sum, bi) => sum + this.lineBase(bi), 0);
    },
    totalFinal() {
      return this.basketResolvedItems.reduce((sum, bi) => sum + this.lineTotal(bi), 0);
    },
    totalDiscount() {
      return Math.max(0, this.totalBase - this.totalFinal);
    },
  },
  methods: {
    groceryImageSrc,
    unitPrice(item) {
      return parseFloat(item && item.price) || 0;
    },
    unitBase(item) {
      const old = parseFloat(item && item.old_price) || 0;
      const current = this.unitPrice(item);
      return old > current ? old : current;
    },
    hasDiscount(item) {
      const old = parseFloat(item && item.old_price) || 0;
      return old > this.unitPrice(item);
    },
    lineTotal(bi) {
      return this.unitPrice(bi.item) * Math.max(0, bi.count);
    },
    lineBase(bi) {
      return this.unitBase(bi.item) * Math.max(0, bi.count);
    },
    formatCurrency(value, currencyCode) {
      const num = Number(value || 0);
      if (!currencyCode || currencyCode === 'RUB' || currencyCode === '₽') {
        const formatted = num.toLocaleString('ru-RU', {
          minimumFractionDigits: num % 1 === 0 ? 0 : 2,
          maximumFractionDigits: 2,
        });
        return `${formatted}\u00A0₽`;
      }
      return `${num.toLocaleString('ru-RU')} ${currencyCode}`.trim();
    },
    refreshBasket() {
      this.basketMap = getGroceryBasket(this.username) || {};
    },
    inc(key) {
      incrementGroceryBasketItem(this.username, key, 1);
      this.refreshBasket();
      _logActivity(this, { type: 'basket_add', item_id: key, amount: Number(this.basketMap[key] || 0) });
    },
    dec(key) {
      incrementGroceryBasketItem(this.username, key, -1);
      this.refreshBasket();
      _logActivity(this, { type: 'basket_remove', item_id: key, amount: Number(this.basketMap[key] || 0) });
    },
    remove(key) {
      removeGroceryBasketItem(this.username, key);
      this.refreshBasket();
      _logActivity(this, { type: 'basket_remove', item_id: key });
    },
    goHome() {
      pushBenchRoute(this.$router, {
        name: 'bench_grocery_main',
        stateId: 'state_main',
        trackId: this.$route.params.track_id,
      });
    },
    goCheckout() {
      pushBenchRoute(this.$router, {
        name: 'bench_grocery_purchase',
        stateId: 'state_grocery_purchase',
        trackId: this.$route.params.track_id,
      });
    },
    getTrackConfig() {
      return this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          if (isUnifiedBench(this.trackConfig)) ensureBenchDomainMerged('grocery');
          applyDefaultMockLoginFromTrackConfig(this.trackConfig);
          syncGrocerySessionFromTrackConfig(this.trackConfig);
          this.isUserLoggedIn = isGroceryLoggedIn();
          const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || '';
          const kvPromise = kvPath ? this.$store.dispatch(GET_KV_STORE, { kvPath }) : Promise.resolve();
          this.refreshBasket();
          this.applyStateDelay();
          return kvPromise;
        });
    },
  },
  mounted() {
    if (isUnifiedBench(this.trackConfig)) ensureBenchDomainMerged('grocery');
    applyDefaultMockLoginFromTrackConfig(this.trackConfig);
    syncGrocerySessionFromTrackConfig(this.trackConfig);
    this.isUserLoggedIn = isGroceryLoggedIn();
    this.refreshBasket();
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || '';
      if (kvPath) this.$store.dispatch(GET_KV_STORE, { kvPath });
      this.applyStateDelay();
    }
  },
});
</script>

<style src="@/assets/books.css"></style>
<style src="@/assets/grocery.css"></style>
<style scoped>
.bench-grocery {
  --shop-max-width: 1600px;
  height: auto;
  min-height: 100%;
  overflow: visible;
  display: block;
  background: var(--bench-surface, #f0f3f7);
}
.loading-container { display: flex; justify-content: center; padding: 48px 0; }
.basket-main .title sup { font-size: 15px; font-weight: 400; color: #4b5563; margin-left: 6px; }
.qty-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--bench-primary-light, #f5f7fa);
  border-radius: 8px;
  padding: 4px;
  justify-content: center;
}
.qty-input {
  width: 40px;
  text-align: center;
  border: none;
  background: transparent;
  font-weight: 600;
  font-size: 14px;
  outline: none;
}
@media (max-width: 900px) {
  .basket-main :deep(.layout) { grid-template-columns: 1fr; }
}
</style>
