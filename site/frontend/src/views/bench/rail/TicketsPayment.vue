<template>
  <div class="bench-rail payment-gateway">
    <!-- Header -->
    <header class="pg-header">
      <div class="pg-header-left">
        <img :src="railLogo" alt="" class="rail-logo" />
        <img :src="BankLogo" alt="Банк" class="bank-logo" />
      </div>
      <div class="pg-header-right">
        <div class="user-info">
          <div class="user-email">{{ userEmail }}</div>
          <div class="user-phone">{{ userPhone }}</div>
        </div>
        <div class="user-avatar">
          <v-icon size="32" color="#1976d2">mdi-account-circle</v-icon>
          <v-icon size="18" color="#bf2020" class="verified-badge">mdi-check-circle</v-icon>
        </div>
      </div>
    </header>

    <!-- Payment Processing Overlay -->
    <div v-if="isProcessing" class="processing-overlay">
      <div class="processing-content">
        <div class="progress-circle">
          <svg viewBox="0 0 100 100">
            <circle class="progress-bg" cx="50" cy="50" r="45" />
            <circle class="progress-bar" cx="50" cy="50" r="45" />
          </svg>
        </div>
        <div class="processing-text">Обработка платежа...</div>
      </div>
    </div>

    <!-- Main Content -->
    <main class="pg-main">
      <div class="card-form-container">
        <!-- Credit Card Widget -->
        <div class="card-wrap">
          <div class="card">
            <div class="input-wrap pan">
              <label>Номер карты</label>
              <input
                v-model="cardNumber"
                type="tel"
                autocomplete="off"
                maxlength="19"
                @input="formatCardNumber"
              />
            </div>
            <div class="input-wrap exp">
              <label>Месяц/Год</label>
              <input
                v-model="cardExpiry"
                type="tel"
                autocomplete="off"
                maxlength="5"
                @input="formatExpiry"
              />
            </div>
            <div class="input-wrap full-name">
              <label>Владелец карты</label>
              <input
                v-model="cardHolder"
                type="text"
                autocomplete="off"
                style="text-transform: uppercase;"
              />
            </div>
            <div class="input-wrap cs-card-name">
              <label>Назовите карту</label>
              <input
                v-model="cardName"
                type="text"
                autocomplete="off"
                maxlength="20"
              />
            </div>
            <div class="input-wrap cvv">
              <label>CVV2(CVC2)</label>
              <input
                v-model="cardCvv"
                type="password"
                autocomplete="off"
                maxlength="3"
              />
            </div>
            <div class="order-id">ID {{ paymentId }}</div>
          </div>
          <div class="backside">
            <div class="order-id">ID {{ paymentId }}</div>
            <div class="black-stripe"></div>
          </div>
        </div>

        <!-- Save Card Checkbox -->
        <label class="save-card-checkbox">
          <input type="checkbox" v-model="saveCard" />
          <span class="checkbox-circle"></span>
          <span>Сохранить карту</span>
        </label>

        <!-- Pay Button -->
        <button class="pay-button" @click="processPayment" :disabled="!isFormValid">
          Оплатить {{ formatPrice(totalPrice) }}
        </button>

        <!-- Back Link -->
        <a href="#" class="back-link" @click.prevent="goBack">
          ← Вернуться в магазин
        </a>
      </div>
    </main>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { getRailTicketUserData, getRailTickets, clearRailTickets, clearRailBookingSession } from "@/utils/localCache.js";
import { _logActivity } from "@/common/trackHelper";
import RailLogoImg from "@/assets/img/rail/rail_pay_logo.png";
import BankLogoImg from "@/assets/img/rail/RU_vtb24_logo.png";

import { benchUserContextMixin } from "@/common/benchUserContextMixin.js";

export default defineComponent({
  name: "RailTicketsPayment",
  mixins: [benchUserContextMixin],
  data() {
    return {
      cardNumber: "",
      cardExpiry: "",
      cardHolder: "",
      cardName: "",
      cardCvv: "",
      saveCard: false,
      paymentId: "1520530995",
      isProcessing: false,
    };
  },
  computed: {
    ...mapGetters(["trackConfig", "kvStore"]),
    configLoaded() {
      return this.trackConfig && Object.keys(this.trackConfig).length > 0;
    },
    testData() {
      return (this.trackConfig && this.trackConfig.test_data) || {};
    },
    configUserData() {
      return this.railPrimaryPassenger;
    },
    railLogo() {
      return RailLogoImg;
    },
    BankLogo() {
      return BankLogoImg;
    },
    userEmail() {
      const userData = getRailTicketUserData();
      return this.configUserData?.email || this.personalInfo.email || "";
    },
    userPhone() {
      const userData = getRailTicketUserData();
      return this.configUserData?.phone || this.personalInfo.phone || "";
    },
    tickets() {
      return getRailTickets() || [];
    },
    totalPrice() {
      return this.tickets.reduce((sum, ticket) => sum + (ticket.totalPrice || 0), 0) || 4649.2;
    },
    isFormValid() {
      return (
        this.cardNumber.replace(/\s/g, "").length >= 16 &&
        this.cardExpiry.length === 5 &&
        this.cardHolder.length > 0 &&
        this.cardCvv.length >= 3
      );
    },
  },
  methods: {
    getTrackConfig() {
      this.$store.dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id }).then(() => {
        if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
          this.$router.push({ name: "not_found" });
          return;
        }
        const kvPath = this.testData.kv_store_path || "";
        if (kvPath) {
          this.$store.dispatch(GET_KV_STORE, { kvPath });
        }
      });
    },
    formatCardNumber(e) {
      let value = e.target.value.replace(/\D/g, "");
      value = value.substring(0, 16);
      const groups = value.match(/.{1,4}/g);
      this.cardNumber = groups ? groups.join(" ") : value;
    },
    formatExpiry(e) {
      let value = e.target.value.replace(/\D/g, "");
      value = value.substring(0, 4);
      if (value.length >= 2) {
        this.cardExpiry = value.substring(0, 2) + "/" + value.substring(2);
      } else {
        this.cardExpiry = value;
      }
    },
    formatPrice(price) {
      return price.toLocaleString("ru-RU", { minimumFractionDigits: 1, maximumFractionDigits: 1 }).replace(",", ",") + " ₽";
    },
    goBack() {
      this.$router.push({
        name: "bench_rail_tickets_checkout",
        params: {
          track_id: this.$route.params.track_id,
          state_id: this.$route.params.state_id,
        },
      });
    },
    processPayment() {
      if (!this.isFormValid) return;

      const enteredNumber = this.cardNumber.replace(/\s/g, "");
      const cardParams = {
        card_number_masked: enteredNumber.slice(0, 4) + " **** **** " + enteredNumber.slice(-4),
        card_expiry: this.cardExpiry,
        card_holder: this.cardHolder,
        amount: this.totalPrice,
      };

      // Agents never receive card_data; accept any filled-in card that passes the form.
      _logActivity(this, {
        type: "submit_payment",
        result: "success",
        ...cardParams,
      });

      // Show processing overlay
      this.isProcessing = true;

      // Wait 5 seconds then complete payment
      setTimeout(() => {
        // Clear tickets and booking session
        clearRailTickets();
        clearRailBookingSession();

        this.isProcessing = false;

        // Navigate to main page
        this.$router.push({
          name: "bench_rail_main",
          params: {
            track_id: this.$route.params.track_id,
            state_id: this.$route.params.state_id,
          },
        });
      }, 200);
    },
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    }
    // Generate random payment ID
    this.paymentId = Math.floor(1000000000 + Math.random() * 9000000000).toString();
  },
});
</script>

<style scoped>
.payment-gateway {
  min-height: 100vh;
  background: var(--bench-surface, #fff);
  display: flex;
  flex-direction: column;
  font-family: Arial, Helvetica, sans-serif;
  color: var(--bench-text, #333);
}

/* Header */
.pg-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 40px;
  border-bottom: 1px solid #eee;
}

.pg-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rail-logo {
  height: 32px;
  width: auto;
}

.bank-logo {
  height: 32px;
  width: auto;
  margin-left: 24px;
}

.pg-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info {
  font-size: 14px;
  text-align: right;
  font-family: Verdana, sans-serif;
}

.user-email {
  color: #1976d2;
  font-weight: 600;
}

.user-phone {
  color: #1976d2;
  text-decoration: underline;
}

.user-avatar {
  position: relative;
}

.verified-badge {
  position: absolute;
  bottom: -2px;
  right: -4px;
}

/* Main Content */
.pg-main {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
}

.card-form-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

/* Card Widget */
.card-wrap {
  display: inline-block;
  position: relative;
  margin: auto;
  width: 100%;
  max-width: 460px;
}

.card {
  font-size: 11px;
  width: 330px;
  color: white;
  height: 200px;
  border-radius: 20px;
  padding: 20px 20px 6px;
  background: #4876bb;
  box-sizing: border-box;
  text-align: left;
  position: relative;
  left: 0;
  z-index: 1;
}

.backside {
  display: block;
  background: #E5EBF2;
  border-radius: 20px;
  position: relative;
  margin-left: auto;
  margin-right: -130px;
  width: 388px;
  height: 200px;
  padding-top: 33px;
  margin-top: -164px;
  box-sizing: border-box;
}

.backside .order-id {
  position: absolute;
  top: 10px;
  right: 0;
  opacity: 0.2;
  font-size: 10px;
  width: 116px;
  text-align: center;
  color: #333;
}

.backside .black-stripe {
  background: black;
  height: 47px;
  width: 100%;
}

.card .order-id {
  position: absolute;
  bottom: 10px;
  right: 15px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 10px;
}

.input-wrap {
  margin-bottom: 8px;
}

.input-wrap label {
  display: block;
  font-size: 11px;
  color: #fff;
  margin-bottom: 4px;
  text-transform: none;
  letter-spacing: 0.5px;
}

.input-wrap input {
  width: 100%;
  background: rgba(255, 255, 255, 0.95);
  border: none;
  border-radius: 4px;
  padding: 8px 10px;
  font-size: 14px;
  color: #333;
  outline: none;
  box-sizing: border-box;
}

.input-wrap input::placeholder {
  color: #999;
}

.input-wrap.pan {
  width: 190px;
  display: inline-block;
  vertical-align: top;
}

.input-wrap.pan input {
  letter-spacing: 1px;
}

.input-wrap.exp {
  width: 80px;
  display: inline-block;
  vertical-align: top;
  margin-left: 10px;
}

.input-wrap.full-name {
  width: 100%;
  margin-top: 8px;
}

.input-wrap.full-name input {
  text-transform: uppercase;
  font-size: 14px;
}

.input-wrap.cs-card-name {
  display: none;
}

.input-wrap.cvv {
  position: absolute;
  right: -110px;
  top: 130px;
  width: 90px;
}

.input-wrap.cvv label {
  color: #000;
}

.input-wrap.cvv input {
  background: var(--bench-surface-elevated, #fff);
  border: 1px solid #ddd;
  text-align: center;
  letter-spacing: 4px;
}

/* Save Card Checkbox */
.save-card-checkbox {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 14px;
  color: var(--bench-text, #333);
}

.save-card-checkbox input {
  display: none;
}

.checkbox-circle {
  width: 18px;
  height: 18px;
  border: 1px solid #1976d2;
  border-radius: 50%;
  position: relative;
}

.save-card-checkbox input:checked + .checkbox-circle {
  border-color: #1976d2;
  background: #1976d2;
}

.save-card-checkbox input:checked + .checkbox-circle::after {
  content: "";
  position: absolute;
  top: 3px;
  left: 5px;
  width: 4px;
  height: 8px;
  border: solid #fff;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

/* Pay Button */
.pay-button {
  width: 100%;
  max-width: 400px;
  background: #e21a1a;
  color: #fff;
  border: none;
  border-radius: 5px;
  padding: 15px 32px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  margin-top: 20px;
  transition: background 0.2s;
}

.pay-button:hover:not(:disabled) {
  background: #c91515;
}

.pay-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* Back Link */
.back-link {
  font-size: 14px;
  color: #1976d2;
  text-decoration: none;
  margin-top: 16px;
}

.back-link:hover {
  text-decoration: underline;
}

/* Processing Overlay */
.processing-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: color-mix(in srgb, var(--bench-surface, #fff) 95%, transparent);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.processing-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.progress-circle {
  width: 100px;
  height: 100px;
}

.progress-circle svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.progress-bg {
  fill: none;
  stroke: #e0e0e0;
  stroke-width: 8;
}

.progress-bar {
  fill: none;
  stroke: #e21a1a;
  stroke-width: 8;
  stroke-linecap: round;
  stroke-dasharray: 283;
  stroke-dashoffset: 283;
  animation: progress-animation 5s linear forwards;
}

@keyframes progress-animation {
  from {
    stroke-dashoffset: 283;
  }
  to {
    stroke-dashoffset: 0;
  }
}

.processing-text {
  font-size: 18px;
  color: var(--bench-text, #333);
  font-weight: 500;
}
</style>
