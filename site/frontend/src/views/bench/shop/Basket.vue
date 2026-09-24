<template>
  <div v-if="configLoaded" class="bench-market basket-page">
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

    <div class="basket-section">
    <!-- Empty states -->
    <div class="basket-empty" v-if="itemsCount === 0">
      <div class="title">Корзина</div>
      <div class="subtitle">Пока пусто</div>
    </div>

    <!-- Basket main -->
    <div v-else>
      <div class="basket-main">
        <div class="basket-title">Корзина<sup>{{ uniqueItemsCount }}</sup></div> 
      </div>          
      <div class="basket-main pb-10">
        <div class="basket-column">
          <!-- Controls bar -->
          <div class="controls-bar">
            <div class="controls-left">
              <v-checkbox class="oz-checkbox" v-model="selectAll" density="compact" hide-details label="&nbsp;Выбрать все" :true-icon="CheckboxOnIcon" :false-icon="null" @update:model-value="toggleSelectAll" />
            </div>
            <!-- <div class="controls-right">
              <v-btn variant="text" size="small" class="action-btn">
                <v-icon size="16">mdi-share-variant</v-icon>
                Поделиться
              </v-btn>
              <v-btn icon variant="text" size="small" class="action-btn-icon">
                <v-icon size="20">mdi-trash-can-outline</v-icon>
              </v-btn>
            </div> -->
          </div>

          <div class="basket-list">
          <!-- Available items section -->
          <div class="items-section">
            <div class="section-title">Доступны для заказа</div>
            <div class="basket-items">
              <div class="basket-row" v-for="bi in basketResolvedItems" :key="bi.key">
                <div class="item-image-wrapper">
                  <div class="item-thumb">
                    <v-img :src="getImageSrc(bi.item && (bi.item.thumbnail || bi.item.img))" cover />
                  </div>
                  <div class="item-checkbox">
                    <v-checkbox class="oz-checkbox move-checkbox" v-model="selectedItems[bi.key]" density="compact" hide-details :true-icon="CheckboxOnIcon" :false-icon="null" @update:model-value="updateSelectAll" />
                  </div>
                </div>

                <div class="item-details">
                  <div class="item-name">{{ getDisplayName(bi.item, bi.key) }}</div>

                  <!-- Badges -->
                  <div class="item-badges" v-if="bi.item">
                    <div class="badge badge-sale" v-if="getOldPrice(bi.item)">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M8 2.065c-2-.643-.667 3.71-2 3.71-.667 0-.806-1.258-1.339-1.258C3.994 4.517 2 6.56 2 9.13 2 11.474 3.333 14 6 14c.667 0 1-.212.625-.62-1.875-2.044-1.358-4.042-.63-3.808.94.302 1.823 1.779 2.557-1.35.186-.847.653-.622 1.266 0 .921.932 1.402 2.94-.36 5.157-.291.367.209.621 1.021.621C12.23 14 14 12.106 14 9.13c0-4.004-4-6.423-6-7.065"/>
                      </svg>
                      <span>Распродажа</span>
                    </div>
                    <div class="badge badge-coins" v-if="bi.item.coins">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M6.667 6a2 2 0 1 0 0 4 2 2 0 0 0 0-4"/>
                        <path fill-rule="evenodd" d="M2 8c0-4.941 1.059-6 6-6s6 1.059 6 6-1.059 6-6 6-6-1.059-6-6m4.667-3.333a3.333 3.333 0 1 0 0 6.667 3.333 3.333 0 0 0 0-6.667M11 5.114a.667.667 0 0 0-.668 1.154 1.998 1.998 0 0 1 0 3.465.667.667 0 0 0 .668 1.155 3.333 3.333 0 0 0 0-5.774" clip-rule="evenodd"/>
                      </svg>
                      <span>{{ bi.item.coins }}</span>
                    </div>
                  </div>

                  <!-- Postpayment badge -->
                  <div class="item-badges" v-if="bi.item && bi.item.postpayment">
                    <div class="badge badge-postpay">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M4 9c-1 0-1-.5-1-1 0-3 2-3 9-3s9 0 9 3c0 .5 0 1-1 1zm16 2c1 0 1 .5 1 1h-2.5a5.5 5.5 0 0 0-5.5 5.5c0 1.328 0 1.5-1 1.5-4.876 0-7.11 0-8.134-1.113C3 16.945 3 15.207 3 12c0-.5 0-1 1-1z"/>
                        <path d="M18.5 21a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7m-.5-5.5a.5.5 0 0 1 1 0v1.793l.854.853a.5.5 0 0 1-.708.708l-1-1A.5.5 0 0 1 18 17.5z"/>
                      </svg>
                      <span>Постоплата</span>
                    </div>
                  </div>

                  <!-- Additional info like variant -->
                  <div class="item-variant" v-if="bi.item && bi.item.variant">{{ bi.item.variant }}</div>

                  <!-- Action buttons -->
                  <div class="item-actions">
                    <button class="action-icon-btn" :class="{ 'active': isFavorited(bi.key) }" @click="toggleFavorite(bi.key)">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
                        <path fill="currentColor" d="M16 6.022C16 3.457 14.052 1.5 11.5 1.5c-1.432 0-2.665.799-3.5 1.926C7.165 2.299 5.932 1.5 4.5 1.5 1.948 1.5 0 3.457 0 6.022c0 2.457 1.66 4.415 3.241 5.743 1.617 1.358 3.387 2.258 4.062 2.577.444.21.95.21 1.394 0 .675-.32 2.445-1.219 4.062-2.577C14.339 10.437 16 8.479 16 6.022"/>
                      </svg>
                    </button>
                    <button class="action-icon-btn" @click="remove(bi.key)">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
                        <path fill="currentColor" d="m4.888 3.035.275-.826A2.5 2.5 0 0 1 7.535.5h.93a2.5 2.5 0 0 1 2.372 1.71l.275.825c2.267.09 3.555.406 3.555 1.527 0 .938-.417.938-1.25.938H2.583c-.833 0-1.25 0-1.25-.937 0-1.122 1.288-1.438 3.555-1.528m1.856-.299-.088.266Q7.295 3 8 3t1.345.002l-.089-.266a.83.83 0 0 0-.79-.57h-.931a.83.83 0 0 0-.79.57M2.167 7.167c0-.6.416-.834.833-.834h10c.417 0 .833.235.833.834 0 6.666-.416 8.333-5.833 8.333s-5.833-1.667-5.833-8.333m4.166 1.666a.833.833 0 0 0-.833.834v1.666a.833.833 0 1 0 1.667 0V9.667a.833.833 0 0 0-.834-.834m4.167.834a.833.833 0 1 0-1.667 0v1.666a.833.833 0 1 0 1.667 0z"/>
                      </svg>
                    </button>
                    <button class="btn-buy" @click="buyNow(bi.key)">Купить</button>
                  </div>
                </div>

                <div class="item-price-section">
                  <div class="price-info">
                    <div class="current-price">
                      <span class="amount">{{ getCurrentPrice(bi.item) }}</span>
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" class="shop-card-icon" fill="currentColor">
                        <path d="M21 12c0 7 0 7-9 7s-9 0-9-7c0-.5 0-1 1-1h16c1 0 1 .5 1 1m-1-3H4c-1 0-1-.5-1-1 0-3 2-3 9-3s9 0 9 3c0 .5 0 1-1 1"/>
                      </svg>
                    </div>
                    <div class="current-price-without-card">
                      <span>{{ getCurrentPriceWithoutCard(bi.item) }}</span>
                    </div>
                    <div class="old-price" v-if="getOldPrice(bi.item)">{{ getOldPrice(bi.item) }}</div>
                    <div class="customs-info" v-if="bi.item && bi.item.customs">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor">
                        <path d="M8 14c3.723 0 6-2.277 6-6s-2.277-6-6-6-6 2.277-6 6 2.277 6 6 6m1-7h2a1 1 0 1 1 0 2H9v2a1 1 0 1 1-2 0V9H5a1 1 0 0 1 0-2h2V5a1 1 0 0 1 2 0z"/>
                      </svg>
                      <span>Таможенный платёж {{ bi.item.customs }}</span>
                    </div>
                  </div>
                </div>

                <div class="item-quantity">
                  <div class="qty-controls">
                    <v-btn icon size="small" variant="text" @click="dec(bi.key)">
                      <v-icon size="16">mdi-minus</v-icon>
                    </v-btn>
                    <input type="text" :value="bi.count" class="qty-input" readonly />
                    <v-btn icon size="small" variant="text" @click="inc(bi.key)">
                      <v-icon size="16">mdi-plus</v-icon>
                    </v-btn>
                  </div>
                  <div class="qty-warning" v-if="bi.item && bi.item.limited">Количество ограничено</div>
                </div>
              </div>
            </div>
          </div>
          </div>
        </div>

        <!-- Right order panel -->
        <div class="order-side">
          <div class="order-panel">
            <button class="btn-proceed" :disabled="selectedItemsCount === 0" @click="toPurchase">Перейти к оформлению</button>
            <div class="muted">Доступные способы и время доставки можно выбрать при оформлении заказа</div>

            <div class="order-summary">
              <div class="summary-header">
                <span class="summary-title">Ваша корзина</span>
                <span class="summary-meta">{{ selectedItemsCount }} товаров • 8.67 кг</span>
              </div>

              <div class="summary-row">
                <div class="summary-label">Товары ({{ selectedItemsCount }})</div>
                <div class="summary-value">{{ formatCurrency(selectedTotalWithoutCard, 'RUB') }}</div>
              </div>

              <div class="summary-row discount-row">
                <div class="summary-label">
                  <span>Скидка</span>
                  <button class="details-link">Подробнее</button>
                </div>
                <div class="summary-value discount-value">- {{ formatCurrency(selectedTotalDiscount, 'RUB') }}</div>
              </div>

              <div class="summary-total">
                <span class="total-label">С МАРКЕТ Картой</span>
                <div class="total-price">{{ formatCurrency(selectedTotalWithCard, 'RUB') }}</div>
              </div>

              <div class="summary-without-card">
                <span class="without-label">Без МАРКЕТ Карты</span>
                <div class="without-price">{{ formatCurrency(selectedTotalWithoutCard, 'RUB') }}</div>
              </div>
            </div>
          </div>

          <div class="credit-card-tile">
            <div class="tile-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M21 12c0 7 0 7-9 7s-9 0-9-7c0-.5 0-1 1-1h16c1 0 1 .5 1 1m-1-3H4c-1 0-1-.5-1-1 0-3 2-3 9-3s9 0 9 3c0 .5 0 1-1 1"/>
              </svg>
            </div>
            <div class="tile-body">
              <div class="tile-title">С кредитной МАРКЕТ Картой</div>
              <div class="tile-sub">0% до 78 дней</div>
            </div>
            <div class="tile-chevron">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M9.385 6.497a1.5 1.5 0 0 0 .112 2.118L13.257 12l-3.76 3.385a1.5 1.5 0 1 0 2.007 2.23l5-4.5a1.5 1.5 0 0 0 0-2.23l-5-4.5a1.5 1.5 0 0 0-2.119.112"/>
              </svg>
            </div>
          </div>

          <div class="bonus-section">
            <div class="bonus-content">
              <div class="bonus-text">Начислим до 115 бонусов продавцов</div>
              <button class="bonus-toggle">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M3.414 5.65a1.25 1.25 0 0 1 1.765.094L8 8.878l2.82-3.134a1.25 1.25 0 1 1 1.86 1.672l-3.75 4.167a1.25 1.25 0 0 1-1.86 0L3.32 7.416a1.25 1.25 0 0 1 .094-1.765"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
    <shop-login-dialog v-model="loginDialog" :loginData="testData && testData.login_data" @success="onLoginSuccess" />
  </div>
</template>

<script>
import { defineComponent, h } from 'vue';
import { mapGetters } from 'vuex';
import { benchUserContextMixin } from '@/common/benchUserContextMixin.js';
import SearchBar from '../../ui/SearchBar.vue';
import MenuBar from './components/MenuBar.vue';
import { GET_TRACK_CONFIG, GET_KV_STORE } from '@/store/actions.type';
import { syncMockLoggedInFromTrack, getShopBasket, setShopBasketItem, incrementShopBasketItem, removeShopBasketItem, setCurrentUsername, isShopFavorite, toggleShopFavorite, getShopSelectedItems, setShopSelectedItems, mergeShopBasket } from '@/utils/localCache.js';
import ShopLoginDialog from './components/ShopLoginDialog.vue';
import { _logActivity } from '@/common/trackHelper';
import { isUnifiedBench } from '@/common/benchTheme';
import { ensureBenchDomainMerged, pushBenchRoute, resolveBenchStateId } from '@/common/benchNavigation';
import { resolveAssetUrl } from '@/common/cdnUrls';

const CheckboxOnIcon = () => h('svg', {
  xmlns: 'http://www.w3.org/2000/svg',
  width: '16',
  height: '16',
  class: 'oz-checkbox-svg'
}, [h('path', {
  fill: 'currentColor',
  d: 'M12.707 5.293a1 1 0 0 1 0 1.414l-5 5a1 1 0 0 1-1.414 0l-3-3a1 1 0 0 1 1.414-1.414L7 9.586l4.293-4.293a1 1 0 0 1 1.414 0'
})]);

export default defineComponent({
  name: 'ShopBasket',
  mixins: [benchUserContextMixin],
  components: { SearchBar, ShopLoginDialog, MenuBar },
  data() { return { loggedIn: false, basketMap: {}, loginDialog: false, CheckboxOnIcon, selectedItems: {}, selectAll: false, pendingBuyKey: null }; },
  computed: {
    ...mapGetters(['trackConfig', 'kvStore']),
    configLoaded() { return this.trackConfig && Object.keys(this.trackConfig).length > 0; },
    common() { return (this.trackConfig && this.trackConfig.common_elements) || {}; },
    isLoggedIn() { return this.loggedIn; },
    testData() { return (this.trackConfig && this.trackConfig.test_data) || {}; },
    username() { return this.benchSessionUser || 'guest'; },
    effectiveUsername() { return this.loggedIn ? this.username : 'shop_guest'; },
    basketResolvedItems() {
      const kv = this.kvStore || {};
      const entries = Object.entries(this.basketMap || {});
      return entries.map(([key, count]) => ({ key, count: Number(count) || 0, item: kv[key] || null }));
    },
    uniqueItemsCount() { return this.basketResolvedItems.length; },
    itemsCount() { return this.basketResolvedItems.reduce((s, bi) => s + Math.max(0, bi.count), 0); },
    totalBase() { return this.roundCurrency(this.basketResolvedItems.reduce((s, bi) => s + this.getBasePriceValue(bi.item) * Math.max(0, bi.count), 0)); },
    totalFinal() { return this.roundCurrency(this.basketResolvedItems.reduce((s, bi) => s + this.getCurrentPriceValue(bi.item) * Math.max(0, bi.count), 0)); },
    totalDiscount() { return Math.max(0, this.totalBase - this.totalFinal); },
    selectedItemsCount() {
      return this.basketResolvedItems
        .filter(bi => this.selectedItems[bi.key])
        .reduce((s, bi) => s + Math.max(0, bi.count), 0);
    },
    selectedTotalWithCard() {
      return this.roundCurrency(this.basketResolvedItems
        .filter(bi => this.selectedItems[bi.key])
        .reduce((s, bi) => s + this.getCurrentPriceValue(bi.item) * Math.max(0, bi.count), 0));
    },
    selectedTotalWithoutCard() {
      return this.roundCurrency(this.basketResolvedItems
        .filter(bi => this.selectedItems[bi.key])
        .reduce((s, bi) => {
          const priceWithoutCard = this.getPriceWithoutCardValue(bi.item);
          return s + priceWithoutCard * Math.max(0, bi.count);
        }, 0));
    },
    selectedTotalDiscount() {
      return this.roundCurrency(this.basketResolvedItems
        .filter(bi => this.selectedItems[bi.key])
        .reduce((s, bi) => {
          const basePrice = this.getBasePriceValue(bi.item);
          const discountPercent = Number(bi.item?.discount || 0);
          const discountAmount = basePrice * (discountPercent / 100);
          return s + discountAmount * Math.max(0, bi.count);
        }, 0));
    }
  },
  methods: {
    roundCurrency(value) { return Math.round(Number(value || 0)); },
    isFavorited(itemKey) {
      if (!this.loggedIn) return false;
      return isShopFavorite(this.username, itemKey);
    },
    toggleFavorite(itemKey) {
      if (!this.loggedIn) {
        this.openLoginDialog();
        return;
      }
      toggleShopFavorite(this.username, itemKey);
      // Force re-render by updating a reactive property
      this.$forceUpdate();
    },
    toggleSelectAll(value) {
      const newSelectedItems = {};
      if (value) {
        this.basketResolvedItems.forEach(bi => {
          newSelectedItems[bi.key] = true;
        });
      }
      this.selectedItems = newSelectedItems;
      this.saveSelectedItems();
    },
    updateSelectAll() {
      const allSelected = this.basketResolvedItems.every(bi => this.selectedItems[bi.key]);
      this.selectAll = allSelected && this.basketResolvedItems.length > 0;
      this.saveSelectedItems();
    },
    saveSelectedItems() {
      if (!this.loggedIn) return;
      setShopSelectedItems(this.username, this.selectedItems);
    },
    loadSelectedItems() {
      if (!this.loggedIn) {
        this.selectedItems = {};
        this.selectAll = false;
        return;
      }
      const savedSelections = getShopSelectedItems(this.username);
      // Initialize with saved state or empty object
      const newSelectedItems = {};
      this.basketResolvedItems.forEach(bi => {
        // Use saved state if available, otherwise default to false
        newSelectedItems[bi.key] = savedSelections[bi.key] || false;
      });
      this.selectedItems = newSelectedItems;
      // Update selectAll based on loaded state
      const allSelected = this.basketResolvedItems.every(bi => this.selectedItems[bi.key]);
      this.selectAll = allSelected && this.basketResolvedItems.length > 0;
    },
    initializeSelectedItems() {
      // Load from localStorage instead of initializing to false
      this.loadSelectedItems();
    },
    openLoginDialog() { this.loginDialog = true; },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = this.benchSessionUser || 'guest';
      setCurrentUsername(username);
      try { mergeShopBasket('shop_guest', username, true); } catch(e) {}
      this.refreshBasket();
      this.$nextTick(() => {
        if (!this.pendingBuyKey) return;
        const key = this.pendingBuyKey;
        this.pendingBuyKey = null;
        this.selectOnlyItem(key);
        this.goToPurchase();
      });
    },
    getImageSrc(s) { return resolveAssetUrl(s); },
    getDisplayName(it, fallback) { return (it && (it.name || it.title || it.product_id)) || fallback || ''; },
    formatCurrency(value, currencyCode) { const num = Number(value || 0); if (!currencyCode || currencyCode === 'RUB') { const f = num.toLocaleString('ru-RU', { minimumFractionDigits: num % 1 === 0 ? 0 : 2, maximumFractionDigits: 2 }); return `${f}\u00A0₽`; } return `${num.toLocaleString('ru-RU')} ${currencyCode}`.trim(); },
    getBasePriceValue(it) {
      if (!it) return 0;
      const raw = typeof it.data_price === 'number' ? it.data_price : Number(it.price || it.price_current || 0);
      return this.roundCurrency(raw);
    },

    getPriceWithoutCardValue(it) {
      if (!it) return 0;
      const basePrice = this.getBasePriceValue(it);
      const discountPercent = Number(it.discount || 0);
      const discounted = basePrice - basePrice * (discountPercent / 100);
      return this.roundCurrency(Math.max(0, discounted));
    },

    getPriceWithCardValue(it) {
      if (!it) return 0;
      const withoutCard = this.getPriceWithoutCardValue(it);
      const cardDiscount = Number(it.card_discount_value || 0);
      return this.roundCurrency(Math.max(0, withoutCard - cardDiscount));
    },

    getCurrentPriceValue(it) { return this.getPriceWithCardValue(it); },
    
    getCurrentPriceWithoutCard(it) {
      if (!it) return '0 ₽';
      const priceWithoutCard = this.getPriceWithoutCardValue(it);
      return this.formatCurrency(priceWithoutCard, it.currency);
    },

    getOldPriceValue(it) { if (!it) return 0; return Number(it.price_old || 0); },
    getCurrentPrice(it) { const val = this.getCurrentPriceValue(it); return this.formatCurrency(val, it && it.currency); },
    getOldPrice(it) { const v = this.getOldPriceValue(it); return v ? this.formatCurrency(v, it && it.currency) : ''; },
    refreshBasket() {
      this.basketMap = getShopBasket(this.effectiveUsername);
      this.$nextTick(() => {
        this.initializeSelectedItems();
      });
    },
    inc(key) {
      incrementShopBasketItem(this.effectiveUsername, key, 1);
      this.refreshBasket();
      const amount = Number(this.basketMap[key] || 0);
      _logActivity(this, { type: 'basket_add', item_id: key, amount });
    },
    dec(key) {
      const cur = Number(this.basketMap[key] || 0);
      const next = Math.max(0, cur - 1);
      setShopBasketItem(this.effectiveUsername, key, next);
      this.refreshBasket();
      const amount = Number(this.basketMap[key] || 0);
      _logActivity(this, { type: 'basket_remove', item_id: key, amount });
    },
    remove(key) {
      removeShopBasketItem(this.effectiveUsername, key);
      this.refreshBasket();
      _logActivity(this, { type: 'basket_remove', item_id: key });
    },
    goToPurchase() {
      pushBenchRoute(this.$router, {
        name: 'bench_catalog_purchase',
        stateId: 'state_purchase',
        trackId: this.$route.params.track_id,
      });
    },
    selectOnlyItem(itemKey) {
      this.selectedItems = { [itemKey]: true };
      this.selectAll = false;
      this.saveSelectedItems();
    },
    buyNow(itemKey) {
      if (!itemKey) return;
      if (!this.loggedIn) {
        // Selection for guest isn't persisted; remember intent and resume after login.
        this.pendingBuyKey = itemKey;
        this.openLoginDialog();
        return;
      }
      this.selectOnlyItem(itemKey);
      this.goToPurchase();
    },
    toPurchase() { if (!this.loggedIn) { this.openLoginDialog(); return; } this.goToPurchase(); },
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig);
          const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || '';
          if (kvPath) return this.$store.dispatch(GET_KV_STORE, { kvPath });
          return Promise.resolve();
        })
        .then(() => { this.refreshBasket(); });
    }
  },
  mounted() {
    if (isUnifiedBench(this.trackConfig)) {
      ensureBenchDomainMerged('shop');
    }
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else if (isUnifiedBench(this.trackConfig)) {
      const stateId = this.$route.params.state_id;
      const resolvedState = resolveBenchStateId(stateId, this.trackConfig);
      const hasState =
        (stateId && this.trackConfig[stateId])
        || (resolvedState && this.trackConfig[resolvedState]);
      if (!hasState) {
        this.$router.push({ name: 'state_not_found' });
        return;
      }
    }
    this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig);
    this.refreshBasket();
  }
});
</script>

<style src="@/assets/books.css"></style>
<style src="@/assets/shop.css"></style>

<style scoped>
.basket-section {
  max-width: var(--shop-max-width, 1400px);
  margin: 0 auto;
  padding: 0 16px;
  color: #001a34;
}
.basket-section :deep(.v-label) {
  color: #001a34 !important;
  opacity: 1 !important;
}
.basket-section :deep(.v-selection-control__wrapper) {
  opacity: 1;
}
.basket-empty .title,
.basket-empty .subtitle {
  color: #001a34;
  opacity: 1;
}
.basket-main { max-width: var(--shop-max-width, 1200px); margin: 24px auto 0 auto; padding: 0 0 0px 0; display:grid; grid-template-columns: 1fr 450px; gap: 16px; }
.basket-column { display: flex; flex-direction: column; gap: 12px; }
.basket-list { background:#fff; border-radius: 20px; padding: 16px; }
.basket-title { font-size: 30px; font-weight: 700; padding: 0; margin: 0 0 5px 0; color: #001a34; opacity: 1; }
.basket-title sup { font-size: 15px; font-weight: 400; color: #4b5563; margin-left: 6px; opacity: 1; }

/* Promotional banner */
.promo-banner { background:#fff; border-radius: 25px; padding: 12px 16px; display: flex; align-items: center; gap: 12px;}
.promo-icon { flex-shrink: 0; width: 24px; height: 24px; color: #f1117e; }
.promo-content { flex: 1; }
.promo-title { font-weight: 400; font-size: 17px; color: #111827; }
.promo-subtitle { font-size: 13px; color: #6b7280; margin-top: 2px; line-height: 1; }
.promo-badge { flex-shrink: 0; background: #fff4f7; color: #f1117e; padding: 2px 8px; border-radius: 8px; font-size: 14px; font-weight: 600; }

/* Controls bar */
.controls-bar { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f3f4f6; background: white; border-radius: 25px; padding: 12px; }
.controls-left :deep(.v-input) { font-weight: 600; }
.controls-right { display: flex; gap: 8px; }
.action-btn { text-transform: none; color: #6b7280 !important; font-size: 13px; }
.action-btn-icon { color: #6b7280 !important; }

/* Items section */
.section-title { font-size: 16px; font-weight: 700; color: #001a34; opacity: 1; margin-bottom: 16px; background: #f5f7fa; padding:12px 16px; border-radius: 12px; }
.basket-items { display: flex; flex-direction: column; gap: 12px; }

/* Item row */
.basket-row { display: grid; grid-template-columns: 88px 1fr 180px auto; align-items: start; gap: 20px; padding: 16px 5px; background: #fff;}

.item-image-wrapper { position: relative; }
.item-thumb { width: 88px; height: 117px; border-radius: 12px; overflow: hidden; background: #f9fafb; }
.item-thumb :deep(img), .item-thumb :deep(.v-img) { border-radius: 12px; }
.item-checkbox { position: absolute; top: 6px; left: 6px; }
.item-checkbox :deep(.v-selection-control__wrapper) { width: 20px; height: 20px; }

.item-details { flex: 1; min-width: 0; }
.item-name { font-weight: 400; font-size: 16px; color: #111827; line-height: 20px; margin-bottom: 8px; letter-spacing: 0;}
.item-badges { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 500; }
.badge svg { width: 14px; height: 14px; }
.badge-sale { background: #f1117e; color: #fff; }
.badge-coins { background: rgba(91, 81, 222, 0.1); color: #5b51de; }
.badge-postpay { background: var(--bench-primary-light, #f3f4f6); color: var(--bench-text-muted, #6b7280); }
.item-variant { font-size: 12px; color: #6b7280; margin-bottom: 8px; }
.item-actions { display: flex; align-items: center; gap: 8px; margin-top: 12px; }
.action-icon-btn {
  background: var(--bench-primary-light, #f3f4f6);
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
  padding: 0;
}
.action-icon-btn svg { color: #6b7280; }
.action-icon-btn:hover { background: #e5e7eb; }
.action-icon-btn.active { background: #fff4f7; }
.action-icon-btn.active svg { color: #f1117e; }
.btn-buy {
  text-transform: none;
  background: var(--bench-primary-light, #f3f4f6);
  color: #111827;
  font-weight: 600;
  font-size: 13px;
  border-radius: 8px;
  border: none;
  padding: 8px 16px;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-buy:hover { background: #e5e7eb; }

/* Price section */
.item-price-section { text-align: left; }
.current-price { display: flex; align-items: center; justify-content: flex-start; gap: 4px; font-size: 16px; font-weight: 800; color: #10c44c; margin-bottom: 0px; }

/* #f1117e */

.current-price-without-card { display: flex; align-items: center; justify-content: flex-start; gap: 4px; font-size: 13px; font-weight: 600; color: #9fa1a5; margin-bottom: 4px; line-height: 1;}

.shop-card-icon { color: #10c44c; width: 16px; height: 16px; }
.old-price { font-size: 13px; color: #9ca3af; text-decoration: line-through; margin-bottom: 8px; }
.customs-info { display: flex; align-items: center; gap: 4px; font-size: 11px; color: #6b7280; justify-content: flex-end; margin-top: 8px; }
.customs-info svg { width: 14px; height: 14px; color: #9ca3af; flex-shrink: 0; }

/* Quantity controls */
.item-quantity { min-width: 120px; }
.qty-controls { display: flex; align-items: center; gap: 4px; background: var(--bench-primary-light, #f9fafb); border-radius: 8px; padding: 4px; justify-content: center; }
.qty-input { width: 40px; text-align: center; border: none; background: transparent; font-weight: 600; font-size: 14px; outline: none; }
.qty-warning { font-size: 11px; color: #ef4444; font-weight: 500; text-align: center; margin-top: 6px; }

/* Order panel */
.order-side { position: sticky; top: 10px; height: max-content; }
.order-panel { background: var(--bench-surface-elevated, #fff); border-radius: 25px; padding: 22px; }

.btn-proceed {
  width: 100%;
  background: #22c55e;
  color: #fff;
  font-weight: 700;
  font-size: 15px;
  border: none;
  border-radius: 16px;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-proceed:hover { background: #16a34a; }
.btn-proceed:disabled { background: #e2e8f0; color: #94a3b8; cursor: not-allowed; }
.btn-proceed:disabled:hover { background: #e2e8f0; }

.order-panel .muted {
  color: #6b7280;
  font-size: 14px;
  line-height: 1.4;
  margin-top: 12px;
}

.order-summary {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #f3f4f6;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.summary-title {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
}

.summary-meta {
  font-size: 14px;
  color: #9ca3af;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  font-size: 14px;
}

.summary-label {
  color: #2b2c2d;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-value {
  font-weight: 600;
  color: #111827;
}

.discount-row .summary-label {
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: center;
}

.details-link {
  background: none;
  border: none;
  color: #0b63ff;
  font-size: 14px;
  cursor: pointer;
  font-weight: 600;
  padding: 0;
  text-decoration: none;
  /* display: block; */
}

.discount-value {
  color: #f1117e;
}

.summary-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f3f4f6;
}

.total-label {
  font-size: 20px;
  color: #111827;
  font-weight: 700;
}

.total-price {
  font-size: 22px;
  font-weight: 700;
  color: #22c55e;
}

.summary-without-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 13px;
}

.without-label {
  color: #8b8b8b;
  font-size: 14px;
}

.without-price {
  color: #909295;
  font-weight: 700;
}

.credit-card-tile {
  margin-top: 12px;
  background: var(--bench-surface-elevated, #fff);
  border-radius: 25px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: background 0.2s;
}
.credit-card-tile:hover { background: var(--bench-primary-light, #f9fafb); }

.tile-icon {
  flex-shrink: 0;
  background: var(--bench-primary-light, #eef2ff);
  color: #0b63ff;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.tile-body {
  flex: 1;
}

.tile-title {
  font-weight: 400;
  font-size: 16px;
  color: #111827;
  line-height: 1.3;
}

.tile-sub {
  color: #6b7280;
  font-size: 12px;
  margin-top: 2px;
}

.tile-chevron {
  flex-shrink: 0;
  color: #cbd5e1;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bonus-section {
  margin-top: 12px;
  background: var(--bench-surface-elevated, #fff);
  border-radius: 25px;
  padding: 16px;
}

.bonus-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.bonus-text {
  flex: 1;
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  line-height: 1.4;
  padding-right: 10px;
}

.bonus-toggle {
  flex-shrink: 0;
  background: none;
  border: none;
  color: #cbd5e1;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}
.bonus-toggle:hover { color: #9ca3af; }

/* Custom МАРКЕТ checkbox styling */
.oz-checkbox :deep(.v-selection-control) { min-height: 20px; margin-bottom: 0; }
.oz-checkbox :deep(.v-selection-control__input) {
  width: 20px;
  height: 20px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: var(--bench-primary-light, #ebf7ff);
}

.oz-checkbox :deep(.v-label) { font-weight: 500 !important; color: #001a34 !important; opacity: 1 !important; }

.oz-checkbox.move-checkbox :deep(.v-selection-control__input) {
  width: 20px;
  height: 20px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  margin-right: 15px;
  margin-top: -15px;
  box-shadow: 0 0 0 4px #fff;
  background: var(--bench-primary-light, #ebf7ff);
}

.oz-checkbox :deep(.v-icon) {
  background-color: #fff;
  color: transparent;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  padding: 2px;
  font-size: 10px !important;
  box-shadow: 1px 0 0 2px #fff;
  border: 1px solid #cbd5e1;
  box-shadow: 0 0 0 4px #fff;
}
.oz-checkbox :deep(.v-icon svg) { display: none; }
.oz-checkbox :deep(.v-selection-control--dirty .v-icon svg) { display: block; }
.oz-checkbox :deep(.v-selection-control--dirty .v-icon) {
  border-color: #0b63ff;
  background-color: #0b63ff;
  color: #fff;
  box-shadow: 0 0 0 4px #fff;
}
.oz-checkbox :deep(.v-icon .oz-checkbox-svg) { display: block; }
.oz-checkbox :deep(.v-icon:has(svg)) { display: grid; place-items: center; }
</style>
