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

    <div v-else-if="paid" class="basket-placeholder">
      <div class="title section-title">Оформление заказа</div>
      <div class="subtitle">Заказ успешно оформлен</div>
      <div class="hint">Спасибо, заказ принят к доставке</div>
      <div class="actions">
        <v-btn class="home" variant="text" @click="goHome">На главную</v-btn>
      </div>
    </div>

    <div v-else-if="itemsCount === 0" class="basket-placeholder">
      <div class="title section-title">Оформление заказа</div>
      <div class="subtitle">Корзина пуста</div>
      <div class="hint">Добавьте товары, затем вернитесь к оформлению</div>
      <div class="actions">
        <v-btn class="home" variant="text" @click="goBasket">В корзину</v-btn>
      </div>
    </div>

    <div v-else class="basket-main">
      <button class="back-link" type="button" @click="goBasket">
        <v-icon size="18">mdi-chevron-left</v-icon>
        <span>Вернуться в корзину</span>
      </button>
      <div class="title section-title">Оформление заказа</div>
      <div class="layout">
        <div class="left">
          <div class="panel">
            <div class="panel-title">Способ оплаты</div>
            <div class="pay-options">
              <button
                v-for="(opt, i) in payOptions"
                :key="opt.id"
                type="button"
                class="pay-option"
                :class="{ selected: i === selectedPayOption }"
                @click="selectedPayOption = i"
              >
                <span class="pay-icon">
                  <img :src="opt.img" :alt="opt.label" />
                </span>
                <span class="pay-label">{{ opt.label }}</span>
              </button>
            </div>
            <label class="pay-after">
              <input v-model="payOnDelivery" type="checkbox" />
              <span>Оплатить после получения</span>
            </label>
          </div>

          <div class="panel">
            <div class="panel-title">Способ получения</div>
            <div class="address-tile">
              <v-icon size="22" color="#6b7280">mdi-truck-delivery-outline</v-icon>
              <div class="tile-content">
                <div class="tile-title">Курьером, от 15 минут</div>
                <div class="tile-subtitle">{{ userAddress }}</div>
              </div>
            </div>
            <div class="address-tile">
              <v-icon size="22" color="#6b7280">mdi-account-outline</v-icon>
              <div class="tile-content">
                <div class="tile-title">{{ userName }} {{ userPhone }}</div>
              </div>
            </div>
          </div>

          <div class="panel">
            <div class="panel-title">Состав заказа</div>
            <div class="items">
              <div class="basket-item" v-for="bi in basketResolvedItems" :key="bi.key">
                <div class="thumb">
                  <v-img :src="groceryImageSrc(bi.item)" cover></v-img>
                </div>
                <div class="info">
                  <div class="book-name">{{ (bi.item && bi.item.title) || bi.key }}</div>
                  <div v-if="bi.item && bi.item.amount" class="author">{{ bi.item.amount }}</div>
                  <div class="author">{{ bi.count }} шт.</div>
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
        </div>
        <div class="right">
          <div class="summary">
            <v-btn class="purchase-btn" block :disabled="isPaying" @click="pay">
              <template v-if="isPaying">
                <v-progress-circular indeterminate size="20" width="3" color="white" class="mr-2"></v-progress-circular>
                Оплата...
              </template>
              <template v-else>Пополнить и оплатить</template>
            </v-btn>
            <div class="terms-text">
              Нажимая на кнопку, вы соглашаетесь с условиями продажи
            </div>
            <div class="row"><span class="label">{{ itemsCountText }}</span><span class="value">{{ formatCurrency(totalBase, 'RUB') }}</span></div>
            <div class="row"><span class="label">Скидка</span><span class="value discount">{{ formatCurrency(totalDiscount, 'RUB') }}</span></div>
            <div class="row"><span class="label">Доставка</span><span class="value">Без доплат</span></div>
            <div class="divider" />
            <div class="row total"><span class="label">Итого</span><span class="value">{{ formatCurrency(totalFinal, 'RUB') }}</span></div>
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
import { getGroceryUserContext } from '@/common/benchPersonalInfo.js';
import { _logActivity } from '@/common/trackHelper';
import {
  applyDefaultMockLoginFromTrackConfig,
  getGroceryBasket,
  getGroceryCurrentUser,
  isGroceryLoggedIn,
  syncGrocerySessionFromTrackConfig,
  pushGroceryOrder,
  clearGroceryBasket,
} from '@/utils/localCache.js';
import SearchBar from '../../ui/SearchBar.vue';
import MenuBar from '../../ui/MenuBar.vue';

export default defineComponent({
  name: 'GroceryPurchase',
  mixins: [StateDelayMixin],
  components: { SearchBar, MenuBar },
  data() {
    return {
      isUserLoggedIn: false,
      basketMap: {},
      paid: false,
      selectedPayOption: 0,
      payOnDelivery: false,
      isPaying: false,
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
    groceryUser() {
      return getGroceryUserContext(this.trackConfig);
    },
    userName() {
      return this.groceryUser.fullName || this.groceryUser.name || '';
    },
    userPhone() {
      return this.groceryUser.phone || '';
    },
    userAddress() {
      return this.groceryUser.address || 'Адрес доставки';
    },
    username() {
      return getGroceryCurrentUser() || 'guest';
    },
    payOptions() {
      return [
        { id: 'card', label: 'Карта', img: '/shop/pay-card.svg' },
        { id: 'sbp', label: 'СБП', img: '/shop/pay-sbp.svg' },
        { id: 'wallet', label: 'Кошелёк', img: '/shop/pay-wallet.svg' },
      ];
    },
    basketResolvedItems() {
      const kv = this.kvStore || {};
      return Object.entries(this.basketMap || {})
        .map(([key, count]) => ({ key, count: Number(count) || 0, item: kv[key] || null }))
        .filter((bi) => bi.count > 0);
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
    goHome() {
      pushBenchRoute(this.$router, {
        name: 'bench_grocery_main',
        stateId: 'state_main',
        trackId: this.$route.params.track_id,
      });
    },
    goBasket() {
      pushBenchRoute(this.$router, {
        name: 'bench_grocery_basket',
        stateId: 'state_grocery_basket',
        trackId: this.$route.params.track_id,
      });
    },
    pay() {
      if (this.isPaying) return;
      const method = (this.payOptions[this.selectedPayOption] || {}).id || 'card';
      try {
        const username = this.username;
        const basketMap = getGroceryBasket(username) || {};
        const basket = Object.keys(basketMap).reduce((arr, k) => {
          const qty = Number(basketMap[k] || 0);
          for (let i = 0; i < qty; i++) arr.push(k);
          return arr;
        }, []);
        const amount = Number(this.totalFinal || 0);
        _logActivity(this, { type: 'submit_payment', username, amount, basket, payment: method });
        pushGroceryOrder(username, { status: 'done', items: basketMap, payment: method });
        clearGroceryBasket(username);
      } catch (e) {}
      this.isPaying = true;
      setTimeout(() => {
        this.isPaying = false;
        this.paid = true;
        this.refreshBasket();
      }, 200);
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
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #6b7280;
  cursor: pointer;
  font-size: 14px;
  background: none;
  border: none;
  padding: 0;
  margin-bottom: 12px;
}
.panel {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid #eceff1;
}
.panel-title {
  font-size: 20px;
  font-weight: 800;
  color: #15223b;
  margin-bottom: 12px;
}
.pay-options {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.pay-option {
  width: 118px;
  border: 2px solid #e6eaed;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  padding: 6px 6px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.pay-option.selected,
.pay-option:hover {
  border-color: #3b3bd8;
}
.pay-icon {
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 6px;
  background: #f3f4f6;
}
.pay-icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.pay-label {
  font-size: 12px;
  font-weight: 700;
  color: #374151;
}
.pay-after {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
}
.address-tile {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-top: 1px solid #f1f3f5;
}
.address-tile:first-of-type { border-top: 0; padding-top: 0; }
.tile-title { font-weight: 700; color: #111827; }
.tile-subtitle { color: #6b7280; font-size: 14px; margin-top: 4px; }
.terms-text {
  font-size: 12px;
  color: #6b7280;
  margin: 10px 0 8px;
  line-height: 1.4;
}
.basket-main :deep(.basket-item) {
  grid-template-columns: 96px 1fr auto;
}
.basket-main :deep(.left .items) {
  gap: 12px;
}
@media (max-width: 900px) {
  .basket-main :deep(.layout) { grid-template-columns: 1fr; }
}
</style>
