<template>
  <div v-if="configLoaded" class="bench-books">
    <logo-line :image="common.logo_line && common.logo_line.image" :color="common.logo_line && common.logo_line.color" />

    <div v-if="!contentReady" class="loading-container">
      <v-progress-circular indeterminate color="primary" :size="64"></v-progress-circular>
    </div>

    <div v-if="contentReady">
    <!-- MAIN SECTION -->
    <div class="purchase-main">
      <div class="back-line">
        <button class="back-link" @click="goBack">
          <v-icon size="18">mdi-chevron-left</v-icon>
          <span>Назад</span>
        </button>
      </div>
      <div class="title">Оплата российской картой</div>

      <div class="ru-card-layout">
        <div class="bank-box">
          <div class="bank-header">
            <div class="bank-brand">
              <img class="bank-logo" :src="getImg('logo_sber')" alt="SBER" />
            </div>
          </div>
          <div class="amount-line-container mt-8">
            <div class="amount-line">
              <div class="merchant">Книги</div>
              <div class="amount">{{ formatCurrency(totalFinal, 'RUB') }}</div>
            </div>
            <div>
              <button class="icon-btn" aria-label="store"><img :src="getImg('icon_store')" alt="" /></button>
            </div>
          </div>          

          <v-btn class="sber-pay mt-4" block>
            <img :src="getImg('button_pay_sber')" />
          </v-btn>

          <div class="divider"><span>или</span></div>

          <!-- CARD FORM -->
          <div class="card-form">
            <div class="label">Картой</div>
            <div v-if="showPaymentError" class="error-alert">
              <v-icon size="18" class="mr-2">mdi-alert-circle-outline</v-icon>
              <span>Операция отклонена. Обратитесь в банк, выпустивший карту</span>
            </div>
            <!-- card number -->
            <v-text-field
              v-model="cardNumber"
              variant="outlined"
              density="comfortable"
              hide-details="auto"
              placeholder="Номер карты"
              :error="!!cardNumberError"
              :error-messages="cardNumberError ? [cardNumberError] : []"
              type="tel"
              inputmode="numeric"
              autocomplete="cc-number"
              :maxlength="19"
              :disabled="isSubmitting"
              @blur="onCardNumberBlur"
            />
            <div class="row mt-4">
              <!-- card month and year -->
              <v-text-field
                class="half"
                v-model="cardDate"
                variant="outlined"
                density="comfortable"
                hide-details
                placeholder="Месяц/Год"
                type="tel"
                inputmode="numeric"
                autocomplete="cc-exp"
                :maxlength="5"
                :error="!!dateError"
                :error-messages="dateError ? [dateError] : []"
                :disabled="isSubmitting"
                @blur="onDateBlur"
              />
              <!-- card cvv code -->
              <v-text-field
                class="half"
                v-model="cardCvv"
                variant="outlined"
                density="comfortable"
                hide-details
                placeholder="CVC / CVV"
                type="tel"
                inputmode="numeric"
                autocomplete="cc-csc"
                :maxlength="3"
                :error="!!cvvError"
                :error-messages="cvvError ? [cvvError] : []"
                :disabled="isSubmitting"
                @blur="onCvvBlur"
              />
            </div>
            <v-btn
              class="pay-submit mt-6"
              block
              :class="{ enabled: isFormValid }"
              :disabled="!isFormValid || isSubmitting"
              :loading="isSubmitting"
              @click="submitCard"
            >Оплатить</v-btn>
            <div class="brands">
              <span class="brand">МИР</span>
              <span class="dot">•</span>
              <span class="brand">VISA</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- END MAIN SECTION -->
    </div>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import LogoLine from "../../ui/LogoLine.vue";
import { assets } from "@/assets/books-assets.js";
import { _logActivity } from "@/common/trackHelper";

import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { isLoggedIn, setCurrentUsername, getBasketItems, addPurchasedItems, clearBasket } from "@/utils/localCache.js";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";

export default defineComponent({
  name: "BooksPurchaseRuCard",
  mixins: [StateDelayMixin],
  components: { LogoLine },
  data() {
    return { loginDialog: false, loggedIn: false, basketKeys: [], cardNumber: '', cardDate: '', cardCvv: '', submitAttempted: false, cardNumberBlurred: false, dateBlurred: false, cvvBlurred: false, isSubmitting: false, showPaymentError: false };
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
      setCurrentUsername(username);
      this.refreshBasket();
    },
    getImg(imageKey) {
      if (!imageKey) return '';
      const key = String(imageKey);
      // Check if it's an asset key (like 'logo_sber', 'icon_store', etc.)
      if (assets[key]) {
        return assets[key];
      }
      // Fallback for other image formats (URLs, file paths, etc.)
      if (key.startsWith('http://') || key.startsWith('https://')) return key;
      if (key.startsWith('./assets/')) {
        const rel = `../../../${key.substring(2)}`;
        return new URL(rel, import.meta.url).href;
      }
      const rel = `../${key}`;
      return new URL(rel, import.meta.url).href;
    },
    getCurrentPrice(item) {
      if (!item) return 0;
      const p = item && item.prices;
      if (p && p.final_price != null) return p.final_price;
      return item.price != null ? item.price : 0;
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
          const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || "";
          if (kvPath) {
            this.$store.dispatch(GET_KV_STORE, { kvPath });
          }
          this.loggedIn = isLoggedIn();
          this.refreshBasket();
          this.applyStateDelay();
        });
    },
    sanitizeCardNumber(value) {
      return String(value || '').replace(/\D/g, '');
    },
    luhnCheck(number) {
      const digits = this.sanitizeCardNumber(number);
      if (!digits) return false;
      let sum = 0;
      let shouldDouble = false;
      for (let i = digits.length - 1; i >= 0; i--) {
        let d = parseInt(digits.charAt(i), 10);
        if (shouldDouble) {
          d *= 2;
          if (d > 9) d -= 9;
        }
        sum += d;
        shouldDouble = !shouldDouble;
      }
      return sum % 10 === 0;
    },
    formatCardNumberInput(raw) {
      const digits = this.sanitizeCardNumber(raw).slice(0, 16);
      return digits.replace(/(.{4})/g, '$1 ').trim();
    },
    formatExpiryInput(raw) {
      const digits = String(raw || '').replace(/\D/g, '').slice(0, 4);
      if (digits.length <= 2) return digits;
      return `${digits.slice(0, 2)}/${digits.slice(2)}`;
    },
    formatCvvInput(raw) {
      return String(raw || '').replace(/\D/g, '').slice(0, 3);
    },
    onCardNumberBlur() {
      this.cardNumberBlurred = true;
    },
    onDateBlur() {
      this.dateBlurred = true;
    },
    onCvvBlur() {
      this.cvvBlurred = true;
    },
    submitCard() {
      this.submitAttempted = true;
      if (!this.isFormValid || this.isSubmitting) {
        _logActivity(this, {
          type: 'submit_payment',
          card_number: this.cardNumber,
          card_date: this.cardDate,
          card_cvv: this.cardCvv,
          result: 'failed',
        });
        return;
      }
      this.isSubmitting = true;
      this.showPaymentError = false;
      const cfgCard = (this.testData && this.testData.card_data) || {};
      const expected = {
        number: this.sanitizeCardNumber(cfgCard.number || ''),
        date: String(cfgCard.date || '').trim(),
        cvv: String(cfgCard.cvv || '').trim(),
      };
      const entered = {
        number: this.sanitizeCardNumber(this.cardNumber),
        date: String(this.cardDate || '').trim(),
        cvv: String(this.cardCvv || '').trim(),
      };
      setTimeout(() => {
        this.isSubmitting = false;
        const isMatch = entered.number === expected.number && entered.date === expected.date && entered.cvv === expected.cvv;
        if (isMatch) {
          _logActivity(this, {
            type: 'submit_payment',
            card_number: entered.number,
            card_date: entered.date,
            card_cvv: entered.cvv,
            result: 'success',
          });
          const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
          if (this.basketKeys && this.basketKeys.length > 0) {
            addPurchasedItems(username, this.basketKeys);
            clearBasket(username);
          }
          this.refreshBasket();
          this.$router.push({ name: 'bench_books_payment_success', params: { track_id: this.$route.params.track_id, state_id: 'state_payment_success' } });
        } else {
          _logActivity(this, {
            type: 'submit_payment',
            card_number: entered.number,
            card_date: entered.date,
            card_cvv: entered.cvv,
            result: 'failed',
          });
          this.cardNumber = '';
          this.cardDate = '';
          this.cardCvv = '';
          this.cardNumberBlurred = false;
          this.dateBlurred = false;
          this.cvvBlurred = false;
          this.submitAttempted = false;
          this.showPaymentError = true;
        }
      }, 2000);
    },
    refreshBasket() {
      if (!this.loggedIn) {
        this.basketKeys = [];
        return;
      }
      const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
      this.basketKeys = getBasketItems(username);
    },
    goBack() {
      this.$router.push({ name: 'bench_books_purchase', params: { track_id: this.$route.params.track_id, state_id: 'state_purchase' } });
    },
  },
  computed: {
    ...mapGetters(["trackConfig", "kvStore"]),
    isLoggedIn() { return this.loggedIn; },
    content() {
      const state = this.$route && this.$route.params && this.$route.params.state_id;
      const cfg = state && this.trackConfig && this.trackConfig[state];
      return cfg ? cfg.content : {};
    },
    common() {
      return (this.trackConfig && this.trackConfig.common_elements) || {};
    },
    testData() {
      return (this.trackConfig && this.trackConfig.test_data) || {};
    },
    configLoaded() {
      return this.trackConfig && Object.keys(this.trackConfig).length > 0;
    },
    basketResolvedItems() {
      const kv = this.kvStore || {};
      return (this.basketKeys || []).map(k => ({ key: k, item: kv[k] || null }));
    },
    totalFinal() {
      return this.basketResolvedItems.reduce((sum, bi) => sum + this.getCurrentPrice(bi.item), 0);
    },
    cardNumberValid() {
      return this.luhnCheck(this.cardNumber);
    },
    dateValid() {
      const val = String(this.cardDate || '').trim();
      if (!/^\d{2}\/\d{2}$/.test(val)) return false;
      const month = parseInt(val.slice(0, 2), 10);
      return month >= 1 && month <= 12;
    },
    cvvValid() {
      return /^\d{3}$/.test(String(this.cardCvv || '').trim());
    },
    isFormValid() {
      return this.cardNumberValid && this.dateValid && this.cvvValid;
    },
    cardNumberError() {
      // Show error after full input or blur with non-empty
      const digits = this.sanitizeCardNumber(this.cardNumber);
      const shouldShow = this.submitAttempted || (this.cardNumberBlurred && digits.length > 0);
      if (!shouldShow) return '';
      return this.cardNumberValid ? '' : 'Неверный номер карты';
    },
    dateError() {
      const hasValue = String(this.cardDate || '').trim().length > 0;
      const shouldShow = (this.submitAttempted && hasValue) || (this.dateBlurred && hasValue);
      if (!shouldShow) return '';
      return this.dateValid ? '' : 'Неверная дата';
    },
    cvvError() {
      const hasValue = String(this.cardCvv || '').trim().length > 0;
      const shouldShow = (this.submitAttempted && hasValue) || (this.cvvBlurred && hasValue);
      if (!shouldShow) return '';
      return this.cvvValid ? '' : 'Неверный CVV';
    },
  },
  watch: {
    cardNumber(newVal) {
      const formatted = this.formatCardNumberInput(newVal);
      if (formatted !== newVal) this.cardNumber = formatted;
      // Auto-validate when full number (16 digits) entered
      const digits = this.sanitizeCardNumber(formatted);
      if (digits.length === 16) this.submitAttempted = true;
      if (this.showPaymentError) this.showPaymentError = false;
    },
    cardDate(newVal) {
      const formatted = this.formatExpiryInput(newVal);
      if (formatted !== newVal) this.cardDate = formatted;
      if (this.showPaymentError) this.showPaymentError = false;
    },
    cardCvv(newVal) {
      const formatted = this.formatCvvInput(newVal);
      if (formatted !== newVal) this.cardCvv = formatted;
      if (this.showPaymentError) this.showPaymentError = false;
    }
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      this.applyStateDelay();
    }
    this.loggedIn = isLoggedIn();
    this.refreshBasket();
  },
});
</script>

<style src="@/assets/books.css"></style>
<style>
:root {
  --sber-gradient-base: linear-gradient(84.67deg,#fbee01 -11.85%,#c7e701 -1.91%,#2cda01 21.01%,#21de58 41.9%,#3ee3a9 60.03%,#37dabe 78.36%,#15cae0 97.56%,#00c7d3 111.85%);
  --sber-gradient-hover: linear-gradient(84.67deg,#fbee01 0.09%,#b9e701 11.56%,#4be701 29.7%,#0ada01 47.6%,#21de58 65.18%,#3ee3a9 83.5%,#37dabe 101.12%,#15cae0 106.67%,#00c7d3 111.85%);
  --sber-gradient-active: linear-gradient(0deg,rgba(38,38,38,0.05),rgba(38,38,38,0.05)),linear-gradient(84.67deg,#fbee01 0.09%,#b9e701 11.56%,#4be701 29.7%,#0ada01 47.6%,#21de58 65.18%,#3ee3a9 83.5%,#37dabe 101.12%,#15cae0 106.67%,#00c7d3 111.85%);
}
</style>
<style scoped>
.bench-books { --shop-max-width: 650px; }

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  padding: 40px 20px;
}

.purchase-main { max-width: var(--shop-max-width); margin: 24px auto; padding: 0 16px; }
.purchase-main .title { font-size: 28px; font-weight: 800; color: #15223b; margin: 4px 0 16px 0; }

/* Back link */
.back-link { display: inline-flex; align-items: center; gap: 6px; color: #6b7280; cursor: pointer; font-size: 14px; }

.ru-card-layout { max-width: 630px; }
.bank-box { background: #f1f2f2; border-radius: 0px; padding: 50px 100px; }
.bank-header { display: flex; align-items: center; justify-content: space-between; }
.bank-brand { display: inline-flex; align-items: center; gap: 10px; }
.bank-logo { height: 24px; }
.bank-name { color: #099a49; font-weight: 800; }
.icon-btn {border: none; border-radius: 8px; padding: 8px; color: #6b7280; }
.amount-line-container { display: flex; align-items: center; justify-content: space-between; }
.amount-line { display: block; align-items: baseline; gap: 14px; }
.merchant { color: #6b7280; font-size: 14px; }
.amount { font-size: 28px; font-weight: 900; }

.sber-pay { box-shadow: none; margin-top: 14px; height: 68px; border-radius: 12px; color: #fff; font-weight: 800; text-transform: none; font-size: 16px; background: var(--sber-gradient-base); display: flex; align-items: center; justify-content: flex-start; padding-left: 0; padding-right: 0; }
.sber-pay:hover { background: var(--sber-gradient-hover); }
.sber-pay:active { background: var(--sber-gradient-active); }
.sber-pay img { height: 100%; width: auto; object-fit: contain; margin-left: 20px; }

.divider { display: flex; align-items: center; gap: 12px; color: #9ca3af; margin: 18px 0; }
.divider::before, .divider::after { content: ""; flex: 1 1 auto; height: 1px; background: #e5e7eb; }
.divider span { flex: 0 0 auto; }

.card-form { background: #ffffff; border-radius: 16px; padding: 20px; border: 1px solid #e5e7eb; }
.card-form .label { font-weight: 500; margin-bottom: 12px; color: #1f2937; font-size: 20px; }
.card-form .row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.card-form .half { width: 100%; }
.card-form :deep(.v-text-field) { --v-theme-primary: #3b3bd8; }
.card-form :deep(.v-field) { background: #ffffff; border: 1px solid #f3f4f6; border-radius: 12px; min-height: 52px; }
.card-form :deep(.v-field__input) { padding-top: 12px; padding-bottom: 12px; color: #1f2937; }

.pay-submit { margin-top: 10px; height: 52px; border-radius: 12px; text-transform: none; font-weight: 400; box-shadow: none; font-size: 16px;}
.pay-submit.v-btn--disabled { opacity: 1; background: #f3f4f6 !important; color: #bababa; }
.pay-submit.enabled { background: #3d3dc7 !important; color: #ffffff; }

.brands { margin-top: 14px; color: #9ca3af; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; gap: 10px; width: 100%; }
.brands .dot { color: #c1c7d0; }

.error-alert { display: flex; align-items: center; gap: 8px; background: #fee2e2; color: #ef4444; border-radius: 8px; padding: 10px 12px; margin-bottom: 12px; }
</style>


