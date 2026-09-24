<template>
  <div class="bench-rail rail-checkout-page rail-gray-bg">
    <div v-if="!configLoaded" class="loading-box">
      <v-progress-circular indeterminate color="#e21a1a" :size="48"></v-progress-circular>
    </div>

    <template v-else>
      <!-- Header -->
      <RailSearchHeader :rail-logo="railLogo" :is-logged-in="loggedIn" :user-name="currentUserName" @open-login="openLoginDrawer" @logout="handleLogout" />

      <!-- Main Content -->
      <div class="checkout-content">
        <div class="checkout-container">
          <div class="top-card">
            <!-- Back button and steps -->
            <div class="checkout-header">
              <button class="back-btn" @click="goBack">
                <v-icon size="24">mdi-arrow-left</v-icon>
              </button>
              <div class="steps-indicator">
                <span v-for="step in 7" :key="step" class="step completed">{{ step }}</span>
              </div>
            </div>

            <h1 class="checkout-title">Заказ готов к оплате</h1>
          </div>

          <div class="outbound-ticket">
            <!-- Outbound Ticket -->
            <div v-if="outboundTicket">
                <!-- Route Card -->
                <div class="route-card">
                  <div class="ticket-header">
                    <div class="train-info">
                      <span class="train-number">{{ outboundTicket.train.number }}</span>
                      <span class="train-name">{{ outboundTicket.train.name }}</span>
                      <span class="route-separator">·</span>
                      <span class="train-route">{{ outboundTicket.train.fromStation }} — {{ outboundTicket.train.toStation }}</span>
                    </div>
                    <v-icon size="24" class="sapsan-icon">mdi-train</v-icon>
                  </div>
                <!-- Timeline -->
                <div class="trip-timeline">
                    <div class="timeline-point departure">
                      <div class="date">{{ formatDateFull(outboundTicket.departureDate) }}</div>
                      <div class="time">{{ outboundTicket.train.departureTime }}</div>
                      <div class="station-code">{{ getStationCode(outboundTicket.train.fromStation) }}</div>
                      <div class="station-name">{{ outboundTicket.train.fromStation }}</div>
                    </div>
                    <div class="timeline-line">
                      <span class="route-link">Маршрут</span>
                      <div class="duration">{{ outboundTicket.train.duration || '4 ч 5 мин' }}</div>
                    </div>
                    <div class="timeline-point arrival">
                      <div class="date">{{ formatDateFull(outboundTicket.departureDate) }}</div>
                      <div class="time">{{ outboundTicket.train.arrivalTime }}</div>
                      <div class="station-code">{{ getStationCode(outboundTicket.train.toStation) }}</div>
                      <div class="station-name">{{ outboundTicket.train.toStation }}</div>
                    </div>
                  </div>
                </div>
          </div>

          <div class="checkout-main-block mt-8">
            <!-- Tickets List -->

              <!-- Passenger Info -->
              <div v-for="(passenger, idx) in outboundTicket.passengers" :key="'out-' + idx" class="passenger-block">
                <div class="passenger-info">
                  <div class="passenger-header">
                    <span class="passenger-name">{{ getPassengerName(passenger) }}</span>
                    <span class="passenger-price">{{ formatPrice(outboundTicket.selectedSeats[idx]?.price || 0) }}</span>
                  </div>
                  <div class="passenger-details">
                    <div class="document-info">{{ getDocumentInfo(passenger) }}</div>
                    <div class="tariff-info">
                      <span>Тариф: </span>
                      <span class="tariff-name">{{ getTariffName(passenger) }}. </span>
                      <span class="tariff-desc">{{ getTariffDesc(passenger) }}</span>
                    </div>
                    <div class="class-info">Класс обслуживания: {{ outboundTicket.selectedClass?.name || 'Купе' }}</div>
                  </div>
                </div>

                <div class="seat-info">
                  <div class="seat-details">
                    <div class="seat-location">
                      Вагон {{ padNumber(outboundTicket.selectedSeats[idx]?.carriageNumber, 2) }},
                      Место {{ padNumber(outboundTicket.selectedSeats[idx]?.seatNumber, 3) }},
                      Купе {{ getCompartmentNumber(outboundTicket.selectedSeats[idx]?.seatNumber) }}
                    </div>
                    <div class="seat-class">{{ outboundTicket.selectedClass?.name }} {{ getClassCode(outboundTicket) }}, ДОСС, {{ getSeatPosition(outboundTicket.selectedSeats[idx]?.seatNumber) }}</div>
                    <div class="numbering-hint">Нумерация вагонов с головы поезда</div>
                  </div>
                  <div class="seat-amenities">
                    <v-icon size="28" title="Розетка">mdi-power-plug-outline</v-icon>
                    <v-icon size="28" title="Кондиционер">mdi-snowflake</v-icon>
                    <v-icon size="28" title="Биотуалет">mdi-toilet</v-icon>
                    <div class="luggage-info">
                      <v-icon size="28">mdi-leaf</v-icon>
                      <span>37.05 кг</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Animal Transport Section -->
              <div class="animal-transport-section">
                <div class="animal-transport-header">
                  <div class="animal-transport-title">
                    <v-icon size="24" color="#b51313">mdi-paw</v-icon>
                    <h3>Провоз животного</h3>
                  </div>
                  <button class="animal-transport-btn">
                    <v-icon size="18">mdi-plus</v-icon>
                    <span>Оформить</span>
                  </button>
                </div>
                <div class="animal-transport-content">
                  <p>В этом разделе вы можете оформить перевозку:</p>
                  <ul>
                    <li>мелкого животного (в переноске);</li>
                  </ul>
                </div>
                <div class="animal-transport-notice warning">
                  <v-icon size="20" color="#b51313">mdi-alert-circle</v-icon>
                  <span>Оформление провоза животного обязательное. Без перевозочного документа на животное посадка в поезд не допускается.</span>
                </div>
                <div class="animal-transport-notice info">
                  <v-icon size="20" color="#b51313">mdi-information</v-icon>
                  <span>Вы можете провезти животное только при выкупе полного купе. Если у вас уже выкуплены билеты в это купе в других заказах, на странице оформления провоза животного эти билеты будут автоматически найдены.</span>
                </div>
              </div>
            </div>

            <div>
                <!-- Ticket Summary -->
                <div class="ticket-summary mt-4">
                  <span class="tickets-count">{{ outboundTicket.selectedSeats?.length || 1 }} билет</span>
                  <span class="tickets-price">{{ formatPrice(outboundTicket.totalPrice || 0) }}</span>
                </div>

              <!-- Return Ticket Label -->
              <div v-if="returnTicket" class="return-label">Обратный билет</div>

              <!-- Return Ticket -->
              <div v-if="returnTicket" class="ticket-group">
                <!-- Route Card -->
                <div class="route-card">
                  <div class="ticket-header">
                    <div class="train-info">
                      <span class="train-number">{{ returnTicket.train.number }}</span>
                      <span class="train-name">{{ returnTicket.train.name }}</span>
                      <span class="route-separator">·</span>
                      <span class="train-route">{{ returnTicket.train.fromStation }} — {{ returnTicket.train.toStation }}</span>
                    </div>
                    <v-icon size="24" class="sapsan-icon">mdi-train</v-icon>
                  </div>

                  <!-- Timeline -->
                  <div class="trip-timeline">
                    <div class="timeline-point departure">
                      <div class="date">{{ formatDateFull(returnTicket.departureDate) }}</div>
                      <div class="time">{{ returnTicket.train.departureTime }}</div>
                      <div class="station-code">{{ getStationCode(returnTicket.train.fromStation) }}</div>
                      <div class="station-name">{{ returnTicket.train.fromStation }}</div>
                    </div>
                    <div class="timeline-line">
                      <span class="route-link">Маршрут</span>
                      <div class="duration">{{ returnTicket.train.duration || '4 ч 5 мин' }}</div>
                    </div>
                    <div class="timeline-point arrival">
                      <div class="date">{{ formatDateFull(returnTicket.departureDate) }}</div>
                      <div class="time">{{ returnTicket.train.arrivalTime }}</div>
                      <div class="station-code">{{ getStationCode(returnTicket.train.toStation) }}</div>
                      <div class="station-name">{{ returnTicket.train.toStation }}</div>
                    </div>
                  </div>
                </div>

                <!-- Passenger Details Card -->
                <div class="ticket-card mt-8">

                <!-- Passenger Info -->
                <div v-for="(passenger, idx) in returnTicket.passengers" :key="'ret-' + idx" class="passenger-block">
                  <div class="passenger-info">
                    <div class="passenger-header">
                      <span class="passenger-name">{{ getPassengerName(passenger) }}</span>
                      <span class="passenger-price">{{ formatPrice(returnTicket.selectedSeats[idx]?.price || 0) }}</span>
                    </div>
                    <div class="passenger-details">
                      <div class="document-info">{{ getDocumentInfo(passenger) }}</div>
                      <div class="tariff-info">
                        <span>Тариф:</span>
                        <span class="tariff-name">«Туда-обратно».</span>
                        <span class="tariff-desc">Одновременно в направлении «туда» и «обратно»</span>
                      </div>
                      <div class="class-info">Класс обслуживания: {{ returnTicket.selectedClass?.name || 'Купе' }}</div>
                    </div>
                  </div>

                  <div class="seat-info">
                    <div class="seat-details">
                      <div class="seat-location">
                        Вагон {{ padNumber(returnTicket.selectedSeats[idx]?.carriageNumber, 2) }},
                        Место {{ padNumber(returnTicket.selectedSeats[idx]?.seatNumber, 3) }},
                        Купе {{ getCompartmentNumber(returnTicket.selectedSeats[idx]?.seatNumber) }}
                      </div>
                      <div class="seat-class">{{ returnTicket.selectedClass?.name }} {{ getClassCode(returnTicket) }}, ДОСС, {{ getSeatPosition(returnTicket.selectedSeats[idx]?.seatNumber) }}</div>
                      <div class="numbering-hint">Нумерация вагонов с хвоста поезда</div>
                    </div>
                    <div class="seat-amenities">
                      <v-icon size="28" title="Розетка">mdi-power-plug-outline</v-icon>
                      <v-icon size="28" title="Кондиционер">mdi-snowflake</v-icon>
                      <v-icon size="28" title="Биотуалет">mdi-toilet</v-icon>
                      <div class="luggage-info">
                        <v-icon size="28">mdi-leaf</v-icon>
                        <span>37.05 кг</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Insurance Section -->
                <div class="insurance-section">
                  <div class="insurance-header">
                    <v-icon size="24" color="#73ba5e">mdi-shield-check</v-icon>
                    <span>Пакет комплексного страхования на время поездки</span>
                  </div>
                  <div class="insurance-content">
                    <div class="insurance-company">
                      <span class="insurance-label">Страховая компания</span>
                      <div class="insurance-select">
                        <span>АльфаСтрахование</span>
                        <v-icon size="18">mdi-chevron-down</v-icon>
                      </div>
                    </div>
                  </div>
                  <div class="insurance-content insurance-info">
                    <div class="insurance-details">
                      <div class="insurance-price">250 ₽</div>
                      <p class="insurance-desc">Максимальные суммы покрытия для следующих рисков:</p>
                      <div class="insurance-coverage">
                        <div class="coverage-row">
                          <span>Медицинские расходы</span>
                          <span>200 000,00 ₽</span>
                        </div>
                        <div class="coverage-row">
                          <span>Несчастный случай</span>
                          <span>2 500 000,00 ₽</span>
                        </div>
                        <div class="coverage-row">
                          <span>Задержка прибытия</span>
                          <span>4 000,00 ₽</span>
                        </div>
                        <div class="coverage-row">
                          <span>Страхование багажа</span>
                          <span>3 000,00 ₽</span>
                        </div>
                        <div class="coverage-row">
                          <span>Гражданская ответственность</span>
                          <span>30 000,00 ₽</span>
                        </div>
                        <div class="coverage-row">
                          <span>Потеря стыковки</span>
                          <span>3 000,00 ₽</span>
                        </div>
                        <div class="coverage-row">
                          <span>Невозможность совершить поездку и опоздание</span>
                          <span>10 000,00 ₽</span>
                        </div>
                      </div>
                      <button class="insurance-select-btn">Выбрать</button>
                    </div>
                  </div>
                </div>
                </div>

                  <!-- Ticket Summary -->
                  <div class="ticket-summary mt-4">
                    <span class="tickets-count">{{ returnTicket.selectedSeats?.length || 1 }} билет</span>
                    <span class="tickets-price">{{ formatPrice(returnTicket.totalPrice || 0) }}</span>
                  </div>

              </div>
            </div>

            <!-- Total Section -->
            <div class="total-section">
              <span class="total-label">К оплате</span>
              <span class="total-price">{{ formatPrice(totalPrice) }}</span>
            </div>
            
            <div class="payment-amount-section mt-4">
              <!-- Payment Method -->
              <div class="payment-section">
                <div class="payment-methods">
                  <h3 class="section-title">Способ оплаты</h3>
                  <div class="payment-options">
                    <label class="payment-option" :class="{ active: paymentMethod === 'card' }">
                      <input type="radio" v-model="paymentMethod" value="card" />
                      <v-icon size="24" class="card-icon">mdi-credit-card-outline</v-icon>
                      <span>Банковская карта</span>
                    </label>
                    <label class="payment-option" :class="{ active: paymentMethod === 'yoomoney' }">
                      <input type="radio" v-model="paymentMethod" value="yoomoney" />
                      <img :src="paymentIcons.yoomoney" alt="ЮMoney" class="yoomoney-icon" />
                      <span>ЮMoney</span>
                    </label>
                  </div>
                </div>
                <div class="payment-cards">
                  <p>Принимаются банковские карты<br>платежных систем:</p>
                  <div class="card-icons">
                    <img :src="paymentIcons.master" alt="Mastercard" class="pay-icon" />
                    <img :src="paymentIcons.visaMaster" alt="Maestro" class="pay-icon" />
                    <img :src="paymentIcons.visaMaster" alt="Visa" class="pay-icon pay-icon-visa" />
                    <img :src="paymentIcons.mir" alt="Мир" class="pay-icon" />
                  </div>
                </div>
              </div>
              <!-- Receipt Section -->
              <div class="receipt-section">
                <div class="receipt-row">
                  <span class="receipt-label">Отправить чек</span>
                  <v-select
                    v-model="receiptType"
                    :items="receiptOptions"
                    item-title="text"
                    item-value="value"
                    variant="outlined"
                    density="compact"
                    hide-details
                    class="receipt-select"
                  />
                  <v-text-field
                    v-model="receiptEmail"
                    variant="outlined"
                    density="compact"
                    hide-details
                    class="receipt-email"
                    placeholder="email@example.com"
                  />
                </div>
                <p class="receipt-hint">Для поездов перевозчика АО «ФПК» возможна отправка чека только на электронную почту</p>
              </div>
            </div>

            <!-- Mobility Assistance Section -->
            <div class="mobility-section mt-4">
              <div class="mobility-header">
                <v-icon size="28" color="#888">mdi-wheelchair-accessibility</v-icon>
                <div class="mobility-title">
                  <h3>Центр содействия мобильности оператор</h3>
                  <p>Маломобильные пассажиры могут оформить заявку на сопровождение и оказание помощи</p>
                </div>
              </div>
            </div>

            <!-- Terms Checkboxes -->
            <div class="terms-section mt-4">
              <label class="terms-checkbox">
                <input type="checkbox" v-model="termsAccepted" />
                <span class="checkbox-box"></span>
                <span class="terms-text">
                  Подтверждаю, что с правилами и особенностями оформления заказа, его оплаты, оформления и переоформления проездного документа (билета), возврата неиспользованного проездного документа (билета), заказанного через Интернет, изложенными в
                  <a href="#" class="terms-link">оферте</a>, ознакомлен.
                </span>
              </label>
              <label class="terms-checkbox">
                <input type="checkbox" v-model="thirdPartyConsent" />
                <span class="checkbox-box"></span>
                <span class="terms-text">
                  Настоящим подтверждаю, что в случае оформления мною проездных документов на третьих лиц, предоставляю персональные данные с их согласия.
                </span>
              </label>

              <!-- Action Buttons -->
              <div class="action-buttons">
                <button class="cancel-btn" @click="cancelBooking">
                  Отменить бронирование
                </button>
                <button class="pay-btn" :disabled="!canPay" @click="processPayment">
                  Оплатить
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Timer Bar -->
      <div class="timer-bar">
        <v-icon size="20">mdi-clock-outline</v-icon>
        <span>Заказ должен быть оплачен до {{ paymentDeadline }}.</span>
        <span class="time-remaining">Осталось {{ timeRemaining }}</span>
      </div>

      <!-- Login Drawer -->
      <RailLoginDrawer
        v-model="loginDrawer"
        :is-logged-in="loggedIn"
        :login-credentials="loginCredentials"
        :user-data="loginCredentials"
        :current-user-name="currentUserName"
        :current-user-email="currentUserEmail"
        @login="handleLogin"
        @logout="handleLogout"
      />
    </template>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { railAssets } from "@/assets/rail-assets.js";
import payMaster from "@/assets/img/general/pay_master.svg";
import payMir from "@/assets/img/general/pay_mir.svg";
import payVisaMaster from "@/assets/img/general/pay_visa_master.svg";
import payYoomoney from "@/assets/img/general/pat_youmoney.svg";
import { setRailTicketLoggedIn, setRailTicketCurrentUser, setRailTicketUserData, getRailTicketUserData, clearRailTicketLogin, getRailTickets, clearRailTickets, clearRailBookingSession, syncRailTicketLoggedInFromTrack } from "@/utils/localCache.js";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";
import { benchUserContextMixin } from "@/common/benchUserContextMixin.js";
import RailSearchHeader from "./components/RailSearchHeader.vue";
import RailLoginDrawer from "./components/RailLoginDrawer.vue";

export default defineComponent({
  name: "RailTicketsCheckout",
  mixins: [benchUserContextMixin,StateDelayMixin],
  components: { RailSearchHeader, RailLoginDrawer },
  data() {
    return {
      loginDrawer: false,
      loggedIn: false,
      paymentMethod: "card",
      receiptType: "email",
      receiptEmail: "",
      termsAccepted: false,
      thirdPartyConsent: false,
      receiptOptions: [
        { text: "на почту", value: "email" },
        { text: "по SMS", value: "sms" },
      ],
      timerInterval: null,
      remainingSeconds: 720, // 12 minutes
    };
  },
  computed: {
    ...mapGetters(["trackConfig", "kvStore"]),
    configLoaded() {
      return this.trackConfig && Object.keys(this.trackConfig).length > 0;
    },
    common() {
      return (this.trackConfig && this.trackConfig.common_elements) || {};
    },
    testData() {
      return (this.trackConfig && this.trackConfig.test_data) || {};
    },
    loginCredentials() {
      return (this.testData && this.testData.login_data) || {};
    },
    configUserData() {
      return this.railPrimaryPassenger;
    },
    currentUserName() {
      if (!this.loggedIn) return "";
      const userData = getRailTicketUserData();
      return userData.name || "";
    },
    currentUserEmail() {
      if (!this.loggedIn) return "";
      const userData = getRailTicketUserData();
      return userData.email || "";
    },
    railLogo() {
      return railAssets["rail_logo"] || "";
    },
    paymentIcons() {
      return {
        master: payMaster,
        mir: payMir,
        visaMaster: payVisaMaster,
        yoomoney: payYoomoney,
      };
    },
    tickets() {
      const storedTickets = getRailTickets() || [];
      if (storedTickets.length > 0) return storedTickets;

      // Demo ticket for testing
      return [{
        train: {
          number: "022",
          name: "«Ночной экспресс»",
          fromStation: "Москва Октябрьская",
          toStation: "Санкт-Петербург-Главный",
          departureTime: "00:25",
          arrivalTime: "04:30",
          duration: "4 ч 05 мин"
        },
        departureDate: new Date().toISOString().split('T')[0],
        selectedClass: { name: "Купе", options: [{ code: "2Л" }] },
        selectedSeats: [{ carriageNumber: 5, seatNumber: 3, price: 3245.50 }],
        passengers: [{ name: this.configUserData?.name || this.personalInfo.fullName || "", documentType: "passport_rf", documentNumber: this.configUserData?.passport_number || "", birthDate: this.configUserData?.birthday || "", tariff: "full" }],
        totalPrice: 3245.50
      }];
    },
    outboundTicket() {
      return this.tickets[0] || null;
    },
    returnTicket() {
      return this.tickets[1] || null;
    },
    totalPrice() {
      return this.tickets.reduce((sum, ticket) => sum + (ticket.totalPrice || 0), 0);
    },
    canPay() {
      return this.termsAccepted && this.thirdPartyConsent && this.tickets.length > 0;
    },
    paymentDeadline() {
      const now = new Date();
      now.setMinutes(now.getMinutes() + 12);
      const day = now.getDate();
      const months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"];
      const hours = String(now.getHours()).padStart(2, "0");
      const minutes = String(now.getMinutes()).padStart(2, "0");
      return `${day}-го ${months[now.getMonth()]} ${hours}:${minutes}`;
    },
    timeRemaining() {
      const minutes = Math.floor(this.remainingSeconds / 60);
      const seconds = this.remainingSeconds % 60;
      return `${minutes}:${String(seconds).padStart(2, "0")}`;
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
        if (!this.trackConfig[this.$route.params.state_id]) {
          this.$router.push({ name: "state_not_found" });
        }
        this.applyStateDelay();
      });
    },
    openLoginDrawer() {
      this.loginDrawer = true;
    },
    handleLogin(formData) {
      this.loggedIn = true;
      setRailTicketLoggedIn(true);
      setRailTicketCurrentUser(formData.username || "guest");
      setRailTicketUserData(formData.userData || {});
    },
    handleLogout() {
      this.loggedIn = false;
      clearRailTicketLogin();
    },
    goBack() {
      this.$router.back();
    },
    getPassengerName(passenger) {
      if (!passenger) return this.configUserData?.name || this.personalInfo.fullName || "";
      if (passenger.name) return passenger.name;
      if (passenger.lastName && passenger.firstName) {
        return `${passenger.lastName} ${passenger.firstName} ${passenger.middleName || ""}`.trim();
      }
      return this.configUserData?.name || this.personalInfo.fullName || "";
    },
    getDocumentInfo(passenger) {
      if (!passenger) {
        const docNumber = this.configUserData?.passport_number || "";
        const birthDate = this.configUserData?.birthday || "";
        const formattedBirthDate = birthDate ? this.formatBirthDateLong(birthDate) : "";
        return `Паспорт РФ ${docNumber}${formattedBirthDate ? ", " + formattedBirthDate : ""}`;
      }
      const docType = passenger.documentType === "passport_rf" ? "Паспорт РФ" : "Документ";
      const docNumber = passenger.documentNumber || this.configUserData?.passport_number || "";
      const birthDate = passenger.birthDate || this.configUserData?.birthday || "";
      const formattedBirthDate = birthDate ? this.formatBirthDateLong(birthDate) : "";
      return `${docType} ${docNumber}${formattedBirthDate ? ", " + formattedBirthDate : ""}`;
    },
    getTariffName(passenger) {
      const tariff = (passenger && passenger.tariff) || "full";
      const tariffNames = {
        full: "Полный",
        round_trip: "«Туда-обратно»",
        child: "Детский",
        student: "Студенческий",
      };
      return tariffNames[tariff] || "Полный";
    },
    getTariffDesc(passenger) {
      const tariff = (passenger && passenger.tariff) || "full";
      const tariffDescs = {
        full: "Полная стоимость билета",
        round_trip: "Одновременно в направлении «туда» и «обратно»",
        child: "Скидка 50% для детей",
        student: "Скидка для студентов",
      };
      return tariffDescs[tariff] || "Полная стоимость билета";
    },
    getCompartmentNumber(seatNumber) {
      return Math.ceil((seatNumber || 1) / 4);
    },
    getBerthType(seatNumber) {
      return (seatNumber || 1) % 2 === 1 ? "Нижнее" : "Верхнее";
    },
    padNumber(num, length) {
      return String(num || 0).padStart(length, "0");
    },
    getSeatPosition(seatNumber) {
      const num = seatNumber || 1;
      const isLower = num % 2 === 1;
      const compartmentPosition = Math.ceil(num / 4);
      const isNearTable = (num % 4 === 1 || num % 4 === 2);
      const direction = num <= 18 ? "по ходу" : "против хода";
      return `${isNearTable ? "У стола" : "Не у стола"}, ${direction}`;
    },
    getClassCode(ticket) {
      const options = ticket?.selectedClass?.options || [];
      return options[0]?.code || "2Л";
    },
    getStationCode(stationName) {
      const codes = {
        "Санкт-Петербург-Главный": "С-ПЕТЕР-ГЛ",
        "Москва Октябрьская": "МОСКВА ОКТ",
        "Москва Курская": "МОСКВА КУР",
        "Москва Казанская": "МОСКВА КАЗ",
      };
      return codes[stationName] || stationName.substring(0, 10).toUpperCase();
    },
    formatPrice(price) {
      return price.toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).replace(",", ",") + " ₽";
    },
    formatDateFull(date) {
      if (!date) return "";
      const d = new Date(date);
      const day = d.getDate();
      const months = ["янв.", "февр.", "мар.", "апр.", "мая", "июн.", "июл.", "авг.", "сент.", "окт.", "нояб.", "дек."];
      const weekdays = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"];
      return `${day} ${months[d.getMonth()]}, ${weekdays[d.getDay()]}`;
    },
    formatBirthDateLong(date) {
      if (!date) return "";
      const d = new Date(date);
      const day = String(d.getDate()).padStart(2, "0");
      const months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"];
      const year = d.getFullYear();
      return `${day} ${months[d.getMonth()]} ${year}`;
    },
    cancelBooking() {
      clearRailTickets();
      clearRailBookingSession();
      this.$router.push({
        name: "bench_rail_main",
        params: {
          track_id: this.$route.params.track_id,
          state_id: this.$route.params.state_id,
        },
      });
    },
    processPayment() {
      if (!this.canPay) return;

      // Navigate to payment page
      this.$router.push({
        name: "bench_rail_tickets_payment",
        params: {
          track_id: this.$route.params.track_id,
          state_id: this.$route.params.state_id,
        },
      });
    },
    startTimer() {
      this.timerInterval = setInterval(() => {
        if (this.remainingSeconds > 0) {
          this.remainingSeconds--;
        } else {
          clearInterval(this.timerInterval);
        }
      }, 1000);
    },
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      const kvPath = this.testData.kv_store_path || "";
      if (kvPath) {
        this.$store.dispatch(GET_KV_STORE, { kvPath });
      }
      this.applyStateDelay();
    }
    this.loggedIn = syncRailTicketLoggedInFromTrack(this.trackConfig);

    // Prefill email from config
    this.receiptEmail = this.configUserData?.email || "";

    // Start countdown timer
    this.startTimer();
  },
  beforeUnmount() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
  },
});
</script>

<style src="@/assets/rail.css"></style>
<style scoped>
.bench-rail.rail-checkout-page {
  background: var(--bench-surface, #e9eaed);
  min-height: 100vh;
}

.rail-checkout-page :deep(.rail-header) {
  width: 100vw;
  margin-left: calc(50% - 50vw);
}

.rail-checkout-page :deep(.header-inner) {
  max-width: 1600px;
  margin: 0 auto;
}

.checkout-content {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  padding-bottom: 80px;
}

.checkout-container {
  background: transparent;
}

.top-card {
  background: var(--bench-surface-elevated, #fff);
  padding: 20px;
  margin-bottom: 16px;
}

.checkout-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 5px;
}

.back-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  color: #333;
}

.back-btn:hover {
  background: var(--bench-primary-light, #f0f0f0);
}

.steps-indicator {
  display: flex;
  gap: 8px;
}

.step {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--bench-primary-light, #d7d7d7);
  color: var(--bench-text, #fff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
}

.step.completed {
  background: #e21a1a;
  color: #fff !important;
}

.checkout-title {
  font-size: 24px;
  font-weight: 300;
  margin: 0 0 16px;
  color: var(--bench-text, #000);
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
  padding-left: 10px;
}

.checkout-main-block {
  background: var(--bench-surface-elevated, #fff);
  padding: 20px 30px;
}

.tickets-list {
  margin-bottom: 24px;
}

.ticket-group {
  margin-bottom: 24px;
}

.route-card {
  background: var(--bench-surface-elevated, #fff);
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 24px 28px;
  margin-bottom: 12px;
}

.ticket-card {
  background: var(--bench-surface-elevated, #fff);
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 20px 28px;
}

.ticket-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.train-info {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 26px;
  color: #000;
  line-height: 1.3;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.train-number {
  color: #e21a1a;
}

.train-name {
  color: #e21a1a;
}

.route-separator {
  color: #333;
  margin: 0 2px;
}

.train-route {
  color: #000;
}

.sapsan-icon {
  color: #e21a1a;
  flex-shrink: 0;
}

/* Timeline */
.trip-timeline {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  border-top: 1px solid #e8e8e8;
  padding-top: 20px;
}

.timeline-point {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.timeline-point.departure {
  align-items: flex-start;
}

.timeline-point.arrival {
  align-items: flex-end;
}

.timeline-point .date {
  font-size: 12px;
  color: #666;
  order: 1;
}

.timeline-point .time {
  font-size: 32px;
  font-weight: 400;
  color: #000;
  line-height: 1;
  order: 2;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.timeline-point .station-code {
  font-size: 11px;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  order: 3;
  margin-top: 4px;
}

.timeline-point .station-name {
  font-size: 13px;
  color: #000;
  order: 4;
  margin-top: 2px;
  max-width: 200px;
  font-weight: 500;
}

.timeline-line {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 20px;
  position: relative;
  margin-top: 28px;
}

.timeline-line::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 10px;
  height: 2px;
  background: #e21a1a;
}

.timeline-line::after {
  content: "";
  position: absolute;
  top: -2px;
  right: 5px;
  width: 0;
  height: 0;
  border-left: 5px solid #e21a1a;
  border-top: 3px solid transparent;
  border-bottom: 3px solid transparent;
}

.route-link {
  font-size: 13px;
  color: #e21a1a;
  cursor: pointer;
  position: relative;
  z-index: 1;
  background: var(--bench-surface-elevated, #fff);
  padding: 0 8px;
  margin-top: 8px;
  text-decoration: none;
}

.duration {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
  background: var(--bench-surface-elevated, #fff);
  padding: 0 8px;
  position: relative;
  z-index: 1;
}

/* Passenger Block */
.passenger-block {
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.passenger-block:not(:last-of-type) {
  border-bottom: 1px solid #e8e8e8;
}

.passenger-block:first-of-type {
  padding-top: 0;
}

.passenger-info {
  padding-bottom: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.passenger-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 12px;
}

.passenger-name {
  font-size: 22px;
  font-weight: 600;
  color: #000;
}

.passenger-price {
  font-size: 23px;
  font-weight: 400;
  color: #000;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.passenger-details {
  font-size: 16px;
  color: #888;
  line-height: 1.6;
}

.document-info {
  color: #888;
}

.tariff-info {
}

.tariff-desc {
  color: #888;
}


/* Seat Info */
.seat-info {
  padding-top: 16px;
}

.seat-details {
  margin-bottom: 12px;
}

.seat-location {
  font-size: 22px;
  font-weight: 500;
  color: #000;
  margin-bottom: 8px;
}

.seat-class {
  font-size: 16px;
  color: #888;
}

.numbering-hint {
  font-size: 16px;
  color: #888;
}

.seat-amenities {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #000;
  margin-top: 30px;
}

.luggage-info {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #000;
  margin-left: 15px;
}

.luggage-info .v-icon {
  color: #00a331;
}

/* Ticket Summary */
.ticket-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #e8e8e8;
  padding: 25px 30px;
  margin-top: 16px;
  background-color: var(--bench-surface-elevated, #fff);
}

.tickets-count {
  font-size: 20px;
  color: #000;
  font-weight: 700;
}

.tickets-price {
  font-size: 24px;
  font-weight: 500;
  color: #000;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

/* Return Label */
.return-label {
  font-size: 14px;
  color: #888;
  margin: 15px 0 15px;
  font-weight: 400;
  text-align: center;
}

/* Total Section */
.total-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #4e4e4e;
  color: #fff;
  padding: 22px 30px;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
  margin-top: -7px;
}

.total-label {
  font-size: 24px;
}

.total-price {
  font-size: 24px;
  font-weight: 400;
}

/* Payment Section */
.payment-section {
  display: flex;
  gap: 40px;
  padding: 25px 30px;
  background: var(--bench-surface-elevated, #fff);
  align-items: flex-start;
}

.payment-methods {
  flex: 0 0 auto;
}

.section-title {
  font-size: 22px;
  font-weight: 600;
  color: #000;
  margin: 0 0 16px;
}

.payment-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.payment-option {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 16px;
  color: #999;
  transition: color 0.2s;
}

.payment-option.active {
  color: #000;
}


.payment-option input[type="radio"] {
  appearance: none;
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border: 2px solid #ccc;
  border-radius: 50%;
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
}

.payment-option input[type="radio"]:checked {
  border-color: #e21a1a;
}

.payment-option input[type="radio"]:checked::after {
  content: "";
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 10px;
  height: 10px;
  background: #e21a1a;
  border-radius: 50%;
}

.payment-option .card-icon {
  color: #666;
}

.payment-option.active .card-icon {
  color: #5a8fc7;
}

.payment-option .yoomoney-icon {
  width: 24px;
  height: 24px;
  opacity: 0.5;
}

.payment-option.active .yoomoney-icon {
  opacity: 1;
}

.payment-cards {
  flex: 0 0 auto;
  background: var(--bench-primary-light, #f5f5f5);
  border-radius: 4px;
  padding: 20px 16px;
  margin-left: auto;
}

.payment-cards p {
  font-size: 14px;
  color: #666;
  margin: 0 0 10px;
  text-indent: 0;
  line-height: 1.4;
}

.card-icons {
  display: flex;
  align-items: center;
  gap: 0px;
  flex-wrap: wrap;
}

.pay-icon {
  height: 15px;
  width: auto;
}

.pay-icon-visa {
  filter: grayscale(100%) brightness(0.6);
}

.pay-icon-small {
  height: 20px;
}

/* Receipt Section */
.receipt-section {
  padding: 25px 30px;
  background: var(--bench-surface-elevated, #fff);
  border-top: 1px solid #e8e8e8;
}

.receipt-row {
  display: flex;
  align-items: center;
  gap: 25px;
  margin-bottom: 20px;
}

.receipt-label {
  font-size: 16px;
  color: #000;
  font-weight: 400;
  
}

.receipt-select {
  width: 130px;
}

.receipt-email {
  width: 240px;
}

.receipt-hint {
  font-size: 14px;
  color: #888;
  font-weight: 500;
  margin: 0;
  padding-bottom: 0;
  text-indent: 0;
}

/* Terms Section */
.terms-section {
  padding: 25px 30px;
  background: var(--bench-surface-elevated, #fff);
  border-top: 1px solid #e8e8e8;
}

.terms-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  margin-bottom: 20px;
}

.terms-checkbox input[type="checkbox"] {
  display: none;
}

.terms-checkbox .checkbox-box {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border: 1px solid #ccc;
  border-radius: 2px;
  background: var(--bench-surface-elevated, #fff);
  position: relative;
  margin-top: 2px;
}

.terms-checkbox input[type="checkbox"]:checked + .checkbox-box {
  background: var(--bench-surface-elevated, #fff);
  border-color: #999;
}

.terms-checkbox input[type="checkbox"]:checked + .checkbox-box::after {
  content: "";
  position: absolute;
  top: 2px;
  left: 5px;
  width: 5px;
  height: 10px;
  border: solid #333;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.terms-text {
  font-size: 16px;
  color: #555;
  line-height: 1.2;
  font-weight: 500;
}

.terms-link {
  color: #e8a024;
  text-decoration: none;
}

.terms-link:hover {
  text-decoration: underline;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding-top: 20px;
  border-top: 1px solid #e8e8e8;
  margin-top: 10px;
  font-size: 14px;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.cancel-btn {
  flex: 1;
  background: var(--bench-primary-light, #f5f5f5);
  color: var(--bench-text, #e21a1a);
  border: none;
  padding: 16px 20px;
  font-weight: 500;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cancel-btn:hover {
  background: var(--bench-primary-muted, #fef5f5);
}

.pay-btn {
  flex: 1;
  background: var(--bench-primary-light, #f5f5f5);
  color: var(--bench-text-muted, #999);
  border: none;
  border-bottom: 2px solid var(--bench-border, #ddd);
  padding: 16px 20px;
  font-weight: 500;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.pay-btn:hover:not(:disabled) {
  background: #e21a1a;
  color: #fff !important;
  border-bottom-color: #c91515;
}

.pay-btn:disabled {
  background: var(--bench-primary-light, #f5f5f5);
  color: var(--bench-text-muted, #999);
  border-bottom-color: var(--bench-border, #ddd);
  cursor: not-allowed;
}

.pay-btn:not(:disabled) {
  background: #e21a1a;
  color: #fff !important;
  border-bottom-color: #c91515;
}

/* Animal Transport Section */
.animal-transport-section {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 4px;
  margin-top: 20px;
}

.animal-transport-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.animal-transport-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.animal-transport-title h3 {
  font-size: 20px;
  font-weight:7600;
  color: #000;
  margin: 0;
}

.animal-transport-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--bench-primary-light, #efefef);
  color: var(--bench-text, #b51313);
  border: none;
  padding: 12px 25px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.animal-transport-btn:hover {
  background: #b51313;
}

.animal-transport-content {
  font-size: 16px;
  color: #333;
  margin-bottom: 12px;
}

.animal-transport-content p {
  margin: 0 0 6px;
  text-indent: 0;
}

.animal-transport-content ul {
  margin: 0;
  padding-left: 20px;
}

.animal-transport-content li {
  color: #666;
}

.animal-transport-notice {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 20px;
  font-size: 14px;
  line-height: 1.4;
  margin-top: 10px;
  font-family: 'Verdana', sans-serif;
}

.animal-transport-notice.warning {
  background: var(--bench-primary-light, #fff6e3);
  color: var(--bench-text, #000);
}

.animal-transport-notice.info {
  background: var(--bench-primary-light, #fff6e3);
  color: var(--bench-text, #000);
  margin-bottom: 20px;
  margin-top: 10px;
}

.animal-transport-notice .v-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

/* Insurance Section */
.insurance-section {
  background: var(--bench-surface-elevated, #fff);
  margin-top: 30px;
}

.insurance-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  font-size: 20px;
  font-weight: 700;
  color: #000;
}

.insurance-content {
  display: flex;
  gap: 24px;
}

.insurance-company {
  flex: 0 0 auto;
}

.insurance-label {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 6px;
}

.insurance-select {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #bdbdbd;
  font-size: 16px;
  color: #333;
  cursor: pointer;
  margin-bottom: 8px;
  width: 400px;
}

.insurance-link {
  font-size: 12px;
  color: #73ba5e;
  text-decoration: none;
}

.insurance-link:hover {
  text-decoration: underline;
}

.insurance-details {
  flex: 1;
  padding: 16px;
}

.insurance-info {
  max-width: 400px;
  border: 2px solid #bdbdbd;
  margin-top: 10px;
}

.insurance-price {
  font-size: 24px;
  font-weight: 500;
  color: #000;
  margin-bottom: 8px;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
  align-items: center;
  display: flex;
  justify-content: center;
}

.insurance-desc {
  font-size: 18px;
  color: #666;
  margin: 0 0 12px;
  text-indent: 0;
}

.insurance-coverage {
  margin-bottom: 16px;
}

.coverage-row {
  display: flex;
  flex-direction: column;
  font-size: 14px;
  padding: 8px 0;
  gap: 15px;
}

.coverage-row span:first-child {
  color: #666;
}

.coverage-row span:last-child {
  color: #000;
  font-weight: 500;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
  font-size: 18px;
}

.insurance-select-btn {
  background: var(--bench-primary-light, #f0f0f0);
  color: var(--bench-text, #db1010);
  border: none;
  border-radius: 4px;
  padding: 15px 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  width: 100%;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
  text-transform: uppercase;
}

/* Mobility Assistance Section */
.mobility-section {
  background: var(--bench-surface-elevated, #fff);
  padding: 20px 30px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.mobility-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.mobility-header .v-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.mobility-title h3 {
  font-size: 24px;
  font-weight: 500;
  color: #000;
  margin: 0 0 4px;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.mobility-title p {
  font-size: 14px;
  color: #666;
  margin: 0;
  text-indent: 0;
}

/* Timer Bar */
.timer-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #333;
  color: #fff;
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  z-index: 100;
}

.time-remaining {
  color: #e21a1a;
  font-weight: 500;
}
</style>
