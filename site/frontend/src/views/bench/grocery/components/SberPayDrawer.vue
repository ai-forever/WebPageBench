<template>
  <div>
    <div v-if="isOpen" class="sberpay-overlay" @click="onClose"></div>
    <div class="sberpay-drawer" :class="{ open: isOpen }" role="dialog" aria-modal="true">
      <div class="sp-header">
        <v-btn class="sp-close" variant="flat" @click="onClose">
          <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M22.364 11.05L20.9498 9.63574L16.0001 14.5855L11.0503 9.63574L9.63611 11.05L14.5859 15.9997L9.63611 20.9495L11.0503 22.3637L16.0001 17.4139L20.9498 22.3637L22.364 20.9495L17.4143 15.9997L22.364 11.05Z"/></svg>
        </v-btn>
      </div>
      <div class="sp-content" :class="{ 'success-state': isSuccess }">
        <div class="sp-merchant">
          <div class="sp-merchant-left">
            <svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" fill="none" viewBox="0 0 24 24" style="min-width: 32px; min-height: 32px;"><path fill="#0C9C0C" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint0_radial_1_1128)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint1_radial_1_1128)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint2_radial_1_1128)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint3_radial_1_1128)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="#fff" d="M11.973 12.57v1.198h-.687V9.921h1.28c1.214 0 1.73.435 1.73 1.303 0 .896-.604 1.346-1.73 1.346zm0-2.016v1.383h.645c.637 0 .967-.208.967-.73 0-.473-.287-.654-.955-.654zM14.66 11.213c.18-.135.51-.247.983-.247.802 0 1.198.275 1.198.99v1.813h-.605v-.495c-.132.318-.466.539-.907.539-.554 0-.883-.314-.883-.852 0-.627.456-.803 1.13-.803h.622v-.12c0-.39-.187-.511-.555-.511-.506 0-.797.197-.983.489zm1.537 1.586v-.223h-.543c-.38 0-.561.072-.561.319 0 .208.153.34.44.34.433 0 .637-.247.664-.436M17.158 11.02h.717l.753 1.885.615-1.884h.681l-1.098 3.039c-.243.659-.49.807-.852.807-.17 0-.358-.05-.44-.12v-.6a.49.49 0 0 0 .33.138c.197 0 .346-.132.45-.502zM5.632 11.216v.844l1.118.701 2.678-1.97a3 3 0 0 0-.353-.585L6.75 11.917z"></path><path fill="#fff" d="M9.01 11.938v.06a2.262 2.262 0 1 1-.987-1.864l.574-.42a2.939 2.939 0 1 0 1.044 1.759z"></path><defs><radialGradient id="paint0_radial_1_1128" cx="0" cy="0" r="1" gradientTransform="matrix(11.273 0 0 10.6132 1.5 6.75)" gradientUnits="userSpaceOnUse"><stop stop-color="#15D015"></stop><stop offset="1" stop-color="#15D015" stop-opacity="0"></stop></radialGradient><radialGradient id="paint1_radial_1_1128" cx="0" cy="0" r="1" gradientTransform="matrix(11.4018 0 0 18.512 .598 6.75)" gradientUnits="userSpaceOnUse"><stop stop-color="#FAED05"></stop><stop offset="1" stop-color="#0C9C0C" stop-opacity="0"></stop></radialGradient><radialGradient id="paint2_radial_1_1128" cx="0" cy="0" r="1" gradientTransform="matrix(-8.11657 0 0 -7.20371 23.305 6.75)" gradientUnits="userSpaceOnUse"><stop stop-color="#42E3B4"></stop><stop offset="1" stop-color="#15D015" stop-opacity="0"></stop></radialGradient><radialGradient id="paint3_radial_1_1128" cx="0" cy="0" r="1" gradientTransform="matrix(-20.6135 0 0 -19.33 22.5 17.25)" gradientUnits="userSpaceOnUse"><stop stop-color="#129DFA"></stop><stop offset="1" stop-color="#15D015" stop-opacity="0"></stop></radialGradient></defs></svg>
            <div v-if="isSuccess" class="sp-countdown">Окно закроется через {{ countdownText }}</div>
            <div v-if="!isSuccess" class="sp-merchant-info">
              <div class="sp-merchant-name">{{ merchantName }}</div>
              <div class="sp-user">
                <span class="sp-user-name">{{ userShortName }}</span>
                <img :src="assets['profile_placeholder']" alt="avatar" class="sp-avatar" />
              </div>
            </div>
          </div>
        </div>

        <div class="sp-amount-row" v-if="!isSuccess">
          <div class="sp-amount-left">
            <div class="sp-label">{{ merchantName.toUpperCase() }}</div>
            <div class="sp-amount">{{ basketTotal }} ₽</div>
          </div>
          <div class="sp-merchant-badge">
            <img :src="assets['sber_merch_logo']" alt="merchIcon" class="sp-merchant-badge-img" />
          </div>
        </div>

        <div class="sp-card" v-if="!isSuccess">
          <div class="sp-card-left">
            <img :src="assets['mir_pay']" class="sp-mirlogo" />
            <div class="sp-card-info">
              <div class="sp-card-balance">{{ cardMoney }} ₽</div>
              <div class="sp-card-caption">МИР •• {{ last4 }}</div>
            </div>
          </div>
          <div class="sp-card-right"></div>
        </div>

        <div v-if="!isSuccess" class="sp-note">Запомним счет для оплаты в этом сервисе. Его всегда можно поменять в настройках SberPay.</div>

        <div v-if="isSuccess" class="sp-success">
          <div class="sp-success-title">Оплатили</div>
          <div class="sp-success-link" @click="onClose">Перейти в магазин</div>
        </div>

        <div v-if="!isSuccess" class="sp-buttons">
          <v-btn class="sp-pay" color="#21A038" :loading="isSubmitting" :disabled="isSubmitting" block @click="submit">
            <span>Оплатить</span>
          </v-btn>
          <v-btn class="sp-cancel" variant="outlined" block @click="onClose">Отменить</v-btn>
        </div>

        <div v-if="isSuccess" class="sp-bottom-illustration">
          <img :src="assets['success_payment_character']" alt="success" />
        </div>
      </div>
    </div>
  </div>
  
</template>

<script>
import { defineComponent } from 'vue';
import { assets } from '@/assets/grocery-assets.js';
import { getGroceryBasket, getGroceryCurrentUser, pushGroceryOrder, clearGroceryBasket } from '@/utils/localCache.js';
import { _logActivity } from '@/common/trackHelper';

export default defineComponent({
  name: 'SberPayDrawer',
  props: {
    isOpen: { type: Boolean, default: false },
    merchantName: { type: String, default: 'Доставка' },
    basketTotal: { type: Number, default: 0 },
    userShortName: { type: String, default: 'Пользователь' },
    cardNumber: { type: String, default: '' },
    cardMoney: { type: String, default: '' },
  },
  data() {
    return { assets, isSubmitting: false, isSuccess: false, countdown: 60, timer: null, finalized: false };
  },
  computed: {
    last4() {
      const n = String(this.cardNumber || '').replace(/\D/g, '');
      return n ? n.slice(-4) : '';
    },
    countdownText() {
      const s = Math.max(0, this.countdown);
      const mm = Math.floor(s / 60);
      const ss = String(s % 60).padStart(2, '0');
      return `${mm}:${ss}`;
    }
  },
  methods: {
    onClose() {
      if (this.isSuccess || this.isSubmitting) {
        this.finalizeOrderIfNeeded();
      }
      if (this.timer) { clearInterval(this.timer); this.timer = null; }
      this.$emit('close');
      // Always reset component state so next open is fresh
      this.resetState();
    },
    submit() {
      this.isSubmitting = true;
      try {
        const username = getGroceryCurrentUser() || 'guest';
        const basketMap = getGroceryBasket(username) || {};
        const basket = Object.keys(basketMap).reduce((arr, k) => {
          const qty = Number(basketMap[k] || 0);
          for (let i = 0; i < qty; i++) arr.push(k);
          return arr;
        }, []);
        const amount = Number(this.basketTotal || 0);
        _logActivity(this, { type: 'submit_payment', username, amount, basket });
      } catch (e) {console.error(e);}
      setTimeout(() => {
        this.isSubmitting = false;
        this.switchToSuccess();
      }, 200);
    },
    switchToSuccess() {
      // Move basket to orders and clear basket (idempotent)
      this.finalizeOrderIfNeeded();
      // show success state
      this.isSuccess = true;
      this.startCountdown();
    },
    finalizeOrderIfNeeded() {
      if (this.finalized) return;
      const username = getGroceryCurrentUser() || 'guest';
      const items = getGroceryBasket(username);
      try {
        pushGroceryOrder(username, { status: 'done', items });
      } catch (e) {}
      try { clearGroceryBasket(username); } catch (e) {}
      this.finalized = true;
    },
    resetState() {
      if (this.timer) { clearInterval(this.timer); this.timer = null; }
      this.isSubmitting = false;
      this.isSuccess = false;
      this.countdown = 60;
      this.finalized = false;
    },
    startCountdown() {
      this.countdown = 30;
      if (this.timer) clearInterval(this.timer);
      this.timer = setInterval(() => {
        this.countdown -= 1;
        if (this.countdown <= 0) {
          clearInterval(this.timer);
          this.timer = null;
          this.onClose();
        }
      }, 1000);
    }
  },
  beforeUnmount() {
    if (this.timer) clearInterval(this.timer);
    if (this.isSuccess || this.isSubmitting) {
      this.finalizeOrderIfNeeded();
    }
  },
  watch: {
    isOpen(newVal) {
      // Ensure fresh state when opened again
      if (newVal) {
        this.resetState();
      } else {
        if (this.timer) { clearInterval(this.timer); this.timer = null; }
      }
    }
  }
});
</script>

<style scoped>
.sberpay-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.35); z-index: 100; }
.sberpay-drawer { position: fixed; top: 0; right: 0; height: 100vh; width: 400px; max-width: 100vw; background: #fff; z-index: 101; transform: translateX(100%); transition: transform 0.5s ease; box-shadow: -4px 0 12px rgba(0,0,0,0.12); display: flex; flex-direction: column; }
.sberpay-drawer.open { transform: translateX(0); }
.sp-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; }
.sp-countdown { font-size: 14px; color: #404040; }
.sp-close :deep(svg) { color: #404040; }
.sp-content { padding: 8px 40px 80px; display: flex; flex-direction: column; gap: 16px; height: 100%; box-sizing: border-box; }
.sp-merchant-left { display: flex; justify-content: space-between; align-items: center; }
.sp-merchant-logo { width: 72px; height: 36px; object-fit: contain; border-radius: 18px; background: #21A038; }
.sp-merchant-info { display: flex; flex-direction: column; gap: 6px; }
.sp-user { display: flex; align-items: center; gap: 8px; }
.sp-avatar { width: 40px; height: 40px; border-radius: 50%; }
.sp-user-name { font-size: 14px; color: #404040; font-weight: 400; }
.sp-merchant-name { display:none; }
.sp-amount-row { display: flex; justify-content: space-between; align-items: center; }
.sp-label { font-size: 14px; color: #7a7a7a; letter-spacing: .5px; }
.sp-amount { font-size: 28px; font-weight: 700; }
.sp-merchant-badge-img { width: 60px; height: 60px; object-fit: contain; border-radius: 12px; }
.sp-card { background: #eaeaea; border-radius: 12px; padding: 12px; display: flex; justify-content: space-between; align-items: center; }
.sp-card-left { display: flex; gap: 12px; align-items: center; }
.sp-mirlogo { width: 36px; height: 24px; object-fit: contain; }
.sp-card-balance { font-weight: 700; }
.sp-card-caption { color: #7a7a7a; font-size: 13px; }
.sp-note { font-size: 14px; color: #333; font-weight:700; background: #eaeaea; border-radius: 12px; padding: 12px; }
.sp-buttons { display: flex; flex-direction: column; gap: 8px; font-size: 20px;}
.sp-pay { text-transform: none; font-weight: 400; height: 48px !important; font-size: 15px; padding: 28px 0; border-radius: 10px;}
.sp-cancel { text-transform: none; font-weight: 400; height: 48px !important; border: 0px !important; font-size: 15px; padding: 28px 0; border-radius: 10px;}

.sp-success { margin-top: 40px; }
.sp-success-title { font-size: 36px; font-weight: 600; color: #1a1a1a; }
.sp-success-link { color: #21A038; font-weight: 500; margin-top: 12px; cursor: pointer; }

.sp-bottom-illustration { position: absolute; bottom: 0; right: 0px; overflow: visible; }
.sp-bottom-illustration img { width: 120%; margin-left: -25%; display: block; }
</style>


