<template>
  <div v-if="configLoaded" class="bench-books basket-page">
    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isLoggedIn"
      @login="openLoginDialog"
    />
    <login-dialog v-model="loginDialog" :loginData="testData && testData.login_data" @success="onLoginSuccess" />
    <menu-bar :items="(common.menu_bar && common.menu_bar.items) || []" />

    <div v-if="!contentReady" class="loading-container">
      <v-progress-circular indeterminate color="primary" :size="64"></v-progress-circular>
    </div>

    <div v-else-if="paid" class="basket-placeholder">
      <div class="title">Оформление покупки</div>
      <div class="subtitle">Покупка успешно оформлена</div>
      <div class="hint">Книги появятся в разделе «Мои книги»</div>
      <div class="actions">
        <v-btn class="home" variant="text" @click="goHome">На главную</v-btn>
      </div>
    </div>

    <div v-else-if="itemsCount === 0" class="basket-placeholder">
      <div class="title">Оформление покупки</div>
      <div class="subtitle">Корзина пуста</div>
      <div class="hint">Добавьте книги, затем вернитесь к оформлению</div>
      <div class="actions">
        <v-btn class="home" variant="text" @click="goBack">В корзину</v-btn>
      </div>
    </div>

    <div v-else class="basket-main">
      <button class="back-link" type="button" @click="goBack">
        <v-icon size="18">mdi-chevron-left</v-icon>
        <span>Вернуться в корзину</span>
      </button>
      <div class="title">Оформление покупки</div>
      <div class="layout">
        <div class="left">
          <div class="panel">
            <div class="panel-title">Способ оплаты</div>
            <div class="pay-options">
              <button
                v-for="(opt, i) in resolvedPayMethods"
                :key="opt.id || opt.type || opt.label || i"
                type="button"
                class="pay-option"
                :class="{ selected: i === selectedPayIndex }"
                @click="selectPayMethod(i, opt)"
              >
                <span class="pay-icon">
                  <img v-if="opt.img" :src="opt.img" :alt="opt.label" />
                </span>
                <span class="pay-label">{{ opt.label }}</span>
              </button>
            </div>
          </div>

          <div class="panel">
            <div class="panel-title">Способ получения</div>
            <div class="address-tile">
              <v-icon size="22" color="#6b7280">mdi-email-outline</v-icon>
              <div class="tile-content">
                <div class="tile-title">Электронная доставка</div>
                <div class="tile-subtitle">{{ receiptEmail || userEmail || 'Чек и доступ придут на почту' }}</div>
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
                  <book-cover :item="bi.item" />
                </div>
                <div class="info">
                  <div class="book-name">{{ (bi.item && (bi.item.name || bi.item.title)) || bi.key }}</div>
                  <div v-if="bi.item && bi.item.author" class="author">{{ bi.item.author }}</div>
                </div>
                <div class="price-block">
                  <div class="price-current">{{ formatCurrency(getCurrentPrice(bi.item), 'RUB') }}</div>
                  <div v-if="hasDiscount(bi.item)" class="old-and-disc">
                    <span class="price-old">{{ formatCurrency(getBasePrice(bi.item), 'RUB') }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="right">
          <div class="summary">
            <v-btn class="purchase-btn" block :disabled="isPaying || !resolvedPayMethods.length" @click="goSelectedPayment">
              <template v-if="isPaying">
                <v-progress-circular indeterminate size="20" width="3" color="white" class="mr-2"></v-progress-circular>
                Оплата...
              </template>
              <template v-else>{{ payButtonLabel }}</template>
            </v-btn>
            <div class="terms-text">
              Нажимая на кнопку, вы соглашаетесь с условиями продажи
            </div>
            <div class="row"><span class="label">{{ itemsCountText }}</span><span class="value">{{ formatCurrency(totalBase, 'RUB') }}</span></div>
            <div class="row"><span class="label">Скидка</span><span class="value discount">{{ formatCurrency(totalDiscount, 'RUB') }}</span></div>
            <div class="divider" />
            <div class="row total"><span class="label">Итого</span><span class="value">{{ formatCurrency(totalFinal, 'RUB') }}</span></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import SearchBar from "../../ui/SearchBar.vue";
import MenuBar from "../../ui/MenuBar.vue";
import LoginDialog from "../../ui/LoginDialog.vue";
import BookCover from "./BookCover.vue";
import { assets } from "@/assets/books-assets.js";
import { resolveAssetUrl } from "@/common/cdnUrls";
import { _logActivity } from "@/common/trackHelper";
import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { isLoggedIn, setCurrentUsername, getBasketItems, clearBasket } from "@/utils/localCache.js";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";
import { ensureBenchDomainMerged, pushBenchRoute, resolveBenchStateId } from "@/common/benchNavigation";
import { getBenchPersonalInfo } from "@/common/benchPersonalInfo.js";

const FALLBACK_PAY_METHODS = [
  { id: 'card', label: 'Карта', type: 'card', img: '/shop/pay-card.svg' },
  { id: 'sbp', label: 'СБП', type: 'sbp', img: '/shop/pay-sbp.svg' },
  { id: 'wallet', label: 'Кошелёк', type: 'wallet', img: '/shop/pay-wallet.svg' },
];

export default defineComponent({
  name: "BooksPurchase",
  mixins: [StateDelayMixin],
  components: { SearchBar, MenuBar, LoginDialog, BookCover },
  data() {
    return {
      loginDialog: false,
      loggedIn: false,
      basketKeys: [],
      receiptEmail: '',
      selectedPayIndex: 0,
      paid: false,
      isPaying: false,
    };
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
      setCurrentUsername(username);
      this.refreshBasket();
    },
    getImageSrc(imagePath) {
      return resolveAssetUrl(imagePath);
    },
    getPayImage(imageKey) {
      if (!imageKey) return '';
      const key = String(imageKey);
      if (assets[key]) {
        return assets[key];
      }
      if (key.startsWith('http://') || key.startsWith('https://') || key.startsWith('/')) return key;
      if (key.startsWith('./assets/')) {
        const rel = `../../../${key.substring(2)}`;
        return new URL(rel, import.meta.url).href;
      }
      return this.getImageSrc(key);
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
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
            this.$router.push({ name: "not_found" });
            return;
          }
          ensureBenchDomainMerged('books');
          const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || "";
          if (kvPath) {
            this.$store.dispatch(GET_KV_STORE, { kvPath });
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
        });
    },
    refreshBasket() {
      const username = this.loggedIn
        ? ((this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest')
        : 'guest';
      this.basketKeys = getBasketItems(username);
    },
    goSelectedPayment() {
      const pm = (this.resolvedPayMethods && this.resolvedPayMethods[this.selectedPayIndex]) || null;
      if (!pm || this.isPaying) return;
      if (pm.to_view_type) {
        pushBenchRoute(this.$router, {
          name: pm.to_view_type,
          stateId: pm.to_state || this.$route.params.state_id,
          trackId: this.$route.params.track_id,
        });
        return;
      }
      this.payInline(pm);
    },
    payInline(pm) {
      try {
        const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
        const basket = this.basketKeys || [];
        const amount = Number(this.totalFinal || 0);
        _logActivity(this, { type: 'submit_payment', username, amount, basket, payment: (pm && (pm.type || pm.id)) || 'card' });
        clearBasket(username);
      } catch (e) {}
      this.isPaying = true;
      setTimeout(() => {
        this.isPaying = false;
        this.paid = true;
        this.refreshBasket();
      }, 200);
    },
    selectPayMethod(idx, pm) {
      this.selectedPayIndex = idx;
      _logActivity(this, { type: 'select_pay_method', value: pm && (pm.type || pm.id) });
    },
    goBack() {
      pushBenchRoute(this.$router, {
        name: 'bench_books_basket',
        stateId: 'state_basket',
        trackId: this.$route.params.track_id,
      });
    },
    goHome() {
      pushBenchRoute(this.$router, {
        name: 'bench_books_main',
        stateId: 'state_main',
        trackId: this.$route.params.track_id,
      });
    },
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
    booksUser() {
      return getBenchPersonalInfo(this.trackConfig);
    },
    userName() {
      return this.booksUser.fullName || this.booksUser.name || '';
    },
    userPhone() {
      return this.booksUser.phone || '';
    },
    userEmail() {
      return this.booksUser.email || '';
    },
    content() {
      const state = this.$route && this.$route.params && this.$route.params.state_id;
      const resolved = resolveBenchStateId(state, this.trackConfig);
      const cfg = (state && this.trackConfig && this.trackConfig[state])
        || (resolved && this.trackConfig && this.trackConfig[resolved]);
      return cfg ? cfg.content : {};
    },
    configLoaded() {
      return this.trackConfig && Object.keys(this.trackConfig).length > 0;
    },
    payMethodsFromConfig() {
      const fromContent = (this.content && this.content.pay_methods) || [];
      if (fromContent.length) return fromContent;
      const fromState = (this.trackConfig && this.trackConfig.state_books_purchase
        && this.trackConfig.state_books_purchase.content
        && this.trackConfig.state_books_purchase.content.pay_methods) || [];
      if (fromState.length) return fromState;
      const booksDomain = this.trackConfig && this.trackConfig.domain_configs && this.trackConfig.domain_configs.books;
      return (booksDomain && booksDomain.state_books_purchase
        && booksDomain.state_books_purchase.content
        && booksDomain.state_books_purchase.content.pay_methods) || [];
    },
    resolvedPayMethods() {
      const configured = this.payMethodsFromConfig;
      if (configured && configured.length) {
        return configured.map((pm) => ({
          ...pm,
          label: pm.name || pm.label,
          img: pm.img || this.getPayImage(pm.image) || '/shop/pay-card.svg',
        }));
      }
      return FALLBACK_PAY_METHODS;
    },
    selectedPayMethod() {
      return (this.resolvedPayMethods && this.resolvedPayMethods[this.selectedPayIndex]) || null;
    },
    payButtonLabel() {
      return this.selectedPayMethod && this.selectedPayMethod.to_view_type
        ? 'Продолжить'
        : 'Пополнить и оплатить';
    },
    basketResolvedItems() {
      const kv = this.kvStore || {};
      return (this.basketKeys || []).map(k => ({ key: k, item: kv[k] || null }));
    },
    itemsCount() { return (this.basketResolvedItems || []).length; },
    itemsCountText() {
      const n = this.itemsCount;
      return n === 1 ? '1 книга' : `${n} книги`;
    },
    totalBase() {
      return this.basketResolvedItems.reduce((sum, bi) => sum + this.getBasePrice(bi.item), 0);
    },
    totalFinal() {
      return this.basketResolvedItems.reduce((sum, bi) => sum + this.getCurrentPrice(bi.item), 0);
    },
    totalDiscount() {
      return Math.max(0, this.totalBase - this.totalFinal);
    },
  },
  mounted() {
    ensureBenchDomainMerged('books');
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      this.applyStateDelay();
    }
    this.loggedIn = isLoggedIn();
    this.receiptEmail = (this.testData && this.testData.login_data && this.testData.login_data.login)
      || this.userEmail
      || '';
    this.refreshBasket();
  },
});
</script>

<style src="@/assets/books.css"></style>
<style scoped>
.bench-books {
  --shop-max-width: 1300px;
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
  background: var(--bench-surface-elevated, #fff);
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
  background: var(--bench-surface-elevated, #fff);
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
