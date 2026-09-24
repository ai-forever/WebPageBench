<template>
  <div v-if="configLoaded" class="bench-books">    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isLoggedIn"
      @login="openLoginDialog"
    />
    <login-dialog v-model="loginDialog" :loginData="testData && testData.login_data" @success="onLoginSuccess" />
    <menu-bar :items="common.menu_bar && common.menu_bar.items" />

    <div v-if="!contentReady" class="loading-container">
      <v-progress-circular indeterminate color="primary" :size="64"></v-progress-circular>
    </div>

    <div v-if="contentReady">
    <!-- MAIN SECTION -->

    <div v-if="basketKeys.length === 0" class="basket-placeholder">
      <div class="title">Корзина</div>
      <div class="subtitle">Корзина пуста</div>
      <div class="hint">Загляните в раздел «Популярное» или начните с главной</div>
      <div class="actions">
        <v-btn class="popular" variant="flat">Популярное</v-btn>
        <v-btn class="home" variant="text" @click="goHome">Главная</v-btn>
      </div>
    </div>

    <div v-else class="basket-main">
      <div class="title">Корзина</div>
      <div class="layout">
        <div v-if="isLoading" class="layout-loader" style="display:flex;align-items:center;justify-content:center;min-height:200px;">
          <v-progress-circular indeterminate color="primary" :size="48"></v-progress-circular>
        </div>
        <template v-else>
          <div class="left">
            <div class="items">
              <div class="basket-item" v-for="bi in basketResolvedItems" :key="bi.key">
                <div class="thumb">
                  <book-cover :item="bi.item" />
                </div>
                <div class="info">
                  <div class="book-name">{{ (bi.item && (bi.item.name || bi.item.title)) || bi.key }}</div>
                  <div v-if="bi.item && bi.item.author" class="author">{{ bi.item.author }}</div>
                  <div class="meta">
                    <v-icon size="16">mdi-headphones</v-icon>
                    <span>Аудио</span>
                  </div>
                  <div class="row-actions">
                    <a href="javascript:void(0)" class="action">
                      <v-icon size="18">mdi-heart-outline</v-icon>
                      <span>Отложить</span>
                    </a>
                    <a href="javascript:void(0)" class="action" @click="removeFromBasket(bi.key)">
                      <v-icon size="18">mdi-trash-can-outline</v-icon>
                      <span>Удалить</span>
                    </a>
                  </div>
                </div>
                <div class="price-block">
                  <div class="price-current">{{ formatCurrency(getCurrentPrice(bi.item), getCurrency(bi.item)) }}</div>
                  <div v-if="hasDiscount(bi.item)" class="old-and-disc">
                    <span class="price-old">{{ formatCurrency(getBasePrice(bi.item), getCurrency(bi.item)) }}</span>
                    <span class="discount">-{{ getDiscountPercent(bi.item) }}%</span>
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
              <v-btn class="purchase-btn" block @click="goPurchase">Перейти к покупке</v-btn>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- END MAIN SECTION -->

    <shop-item-carousel
      :title="common.item_carousel && common.item_carousel.title"
      :items="carouselItems"
    />
</div>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import SearchBar from "../../ui/SearchBar.vue";
import MenuBar from "../../ui/MenuBar.vue";
import ShopItemCarousel from "../../ui/ShopItemCarousel.vue";
import LoginDialog from "../../ui/LoginDialog.vue";
import BookCover from "./BookCover.vue";
import { isLoggedIn, getBasketItems, removeBasketItem, setCurrentUsername, addBasketItem, clearBasket } from "@/utils/localCache.js";
import { _logActivity } from "@/common/trackHelper";
import { ensureBenchDomainMerged, pushBenchRoute, resolveBenchStateId } from "@/common/benchNavigation";
import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";

export default defineComponent({
  name: "BooksBasket",
  mixins: [StateDelayMixin],
  components: { SearchBar, MenuBar, ShopItemCarousel, LoginDialog, BookCover },
  data() {
    return { isLoading: false, loginDialog: false, loggedIn: false, basketKeys: [] };
  },
  methods: {
    getCurrency(item) {
      const nested = item && item.prices && item.prices.currency;
      return nested || (item && item.currency) || 'RUB';
    },
    getCurrentPrice(item) {
      if (!item) return 0;
      const p = item.prices;
      if (p && p.final_price != null) return p.final_price;
      return item.price != null ? item.price : 0;
    },
    getBasePrice(item) {
      if (!item) return 0;
      const p = item.prices;
      const base = p && (p.base_price != null ? p.base_price : p.old_price);
      if (base != null) return base;
      return this.getCurrentPrice(item);
    },
    getDiscountPercent(item) {
      if (!item) return 0;
      const p = item.prices;
      const nested = p && p.discount_percent;
      const top = item.discount_percent;
      return nested != null ? nested : (top != null ? top : 0);
    },
    hasDiscount(item) {
      return this.getDiscountPercent(item) > 0 && this.getBasePrice(item) !== this.getCurrentPrice(item);
    },
    formatCurrency(value, currencyCode) {
      const num = Number(value || 0);
      if (currencyCode === 'RUB' || currencyCode === 'RUR' || currencyCode === '₽' || !currencyCode) {
        const formatted = num.toLocaleString('ru-RU', { minimumFractionDigits: num % 1 === 0 ? 0 : 2, maximumFractionDigits: 2 });
        return `${formatted}\u00A0₽`;
      }
      return `${num.toLocaleString('ru-RU')} ${currencyCode}`.trim();
    },
    goPurchase() {
      if (!this.loggedIn) {
        this.openLoginDialog();
        return;
      }
      pushBenchRoute(this.$router, {
        name: 'bench_books_purchase',
        stateId: 'state_purchase',
        trackId: this.$route.params.track_id });
    },
    openLoginDialog() { this.loginDialog = true; },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
      setCurrentUsername(username);
      // merge guest basket into user basket
      try {
        const guestItems = getBasketItems('guest');
        if (Array.isArray(guestItems) && guestItems.length > 0) {
          for (const k of guestItems) addBasketItem(username, k);
          clearBasket('guest');
        }
      } catch (e) {}
      this.refreshBasket();
    },
    getTrackConfig() {
      this.isLoading = true;
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
            this.$router.push({ name: "not_found" });
            return Promise.resolve();
          }
          ensureBenchDomainMerged('books');
          const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || "";
          let kvPromise = Promise.resolve();
          if (kvPath) {
            kvPromise = this.$store.dispatch(GET_KV_STORE, { kvPath });
          }
          const stateId = this.$route.params.state_id;
          const resolvedState = resolveBenchStateId(stateId, this.trackConfig);
          const hasState =
            (stateId && this.trackConfig[stateId])
            || (resolvedState && this.trackConfig[resolvedState]);
          if (!hasState) {
            this.$router.push({ name: "state_not_found" });
          }
          this.loggedIn = isLoggedIn();
          this.refreshBasket();
          this.applyStateDelay();

          return kvPromise;
        })
        .finally(() => {
          this.isLoading = false;
        });
    },
    goHome() {
      pushBenchRoute(this.$router, {
        name: 'bench_books_main',
        stateId: 'state_main',
        trackId: this.$route.params.track_id });
    },
    refreshBasket() {
      const username = this.loggedIn
        ? ((this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest')
        : 'guest';
      this.basketKeys = getBasketItems(username);
    },
    removeFromBasket(key) {
      const username = this.loggedIn
        ? ((this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest')
        : 'guest';
      removeBasketItem(username, key);
      _logActivity(this, { type: 'basket_remove', item_id: key });
      this.refreshBasket();
    }
  },
  computed: {
    ...mapGetters(["trackConfig", "kvStore"]),
    isLoggedIn() { return this.loggedIn; },
    common() {
      return (this.trackConfig && this.trackConfig.common_elements) || {};
    },
    testData() {
      return (this.trackConfig && this.trackConfig.test_data) || {};
    },
    configLoaded() {
      return this.trackConfig && Object.keys(this.trackConfig).length > 0;
    },
    content() {
      const state = this.trackConfig && this.trackConfig[this.$route.params.state_id];
      return (state && state.content) || {};
    },
    // take item from kv store
    carouselItems() {
      const src = (this.common && this.common.item_carousel && this.common.item_carousel.items) || [];
      const kv = this.kvStore || {};
      
      return src.map(it => {
        if (it && it.kv_id && kv[it.kv_id]) {
          const kvItem = kv[it.kv_id];
          return { ...kvItem, ...it };
        }
        return it;
      });
    },
    basketResolvedItems() {
      const kv = this.kvStore || {};
      return (this.basketKeys || []).map(k => ({ key: k, item: kv[k] || null }));
    },
    itemsCount() { return (this.basketResolvedItems || []).length; },
    itemsCountText() {
      const n = this.itemsCount;
      const label = n === 1 ? '1 книга' : `${n} книги`;
      return label;
    },
    totalBase() {
      return this.basketResolvedItems.reduce((sum, bi) => sum + this.getBasePrice(bi.item), 0);
    },
    totalFinal() {
      return this.basketResolvedItems.reduce((sum, bi) => sum + this.getCurrentPrice(bi.item), 0);
    },
    totalDiscount() { return Math.max(0, this.totalBase - this.totalFinal); } },
  mounted() {
    ensureBenchDomainMerged('books');
    const routeStateId = this.$route.params.state_id;
    const resolvedState = resolveBenchStateId(routeStateId, this.trackConfig);
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      const hasState =
        (routeStateId && this.trackConfig[routeStateId])
        || (resolvedState && this.trackConfig[resolvedState]);
      if (!hasState) {
        this.$router.push({ name: 'state_not_found' });
        return;
      }
      this.applyStateDelay();
    }
    this.loggedIn = isLoggedIn();
    this.refreshBasket();
  } });
</script>

<style src="@/assets/books.css"></style>
<style scoped>
.bench-books { --shop-max-width: 1600px; }
</style>