<template>
  <div class="bench-rail rail-booking-page rail-gray-bg">
    <div v-if="!configLoaded" class="loading-box">
      <v-progress-circular indeterminate color="#e21a1a" :size="48"></v-progress-circular>
    </div>

    <template v-else>
      <!-- Header -->
      <RailSearchHeader :rail-logo="railLogo" :is-logged-in="loggedIn" :user-name="currentUserName" @open-login="openLoginDrawer" @logout="handleLogout" />

      <!-- Main Content -->
      <div class="booking-content">
        <div class="booking-container">
          <!-- Back button and steps -->
          <div class="booking-header">
            <button class="back-btn" @click="goBack">
              <v-icon size="24">mdi-arrow-left</v-icon>
            </button>
            <div class="steps-indicator">
              <span v-for="step in 7" :key="step" :class="getStepClass(step)">{{ step }}</span>
            </div>
          </div>

          <h1 class="booking-title">Выберите класс обслуживания</h1>

          <!-- Train Info -->
          <div class="train-info-bar">
            <div class="train-info-content">
              <span class="train-number">{{ train.number }}</span>
              <span class="train-name" v-if="train.name">{{ train.name }}</span>
              <span class="train-route">{{ train.fromStation }} — {{ train.toStation }}</span>
              <span class="train-departure">, отпр. {{ train.departureTime }}, {{ formatDateShort(departureDate) }}</span>
            </div>
            <v-icon size="20" class="qr-icon">mdi-qrcode</v-icon>
          </div>
        </div>

            <div v-for="(tariff, idx) in tariffOptions" :key="tariff.type" class="booking-container service-class-card mt-4" :class="{ selected: selectedClass === tariff.type }" @click="selectClass(tariff.type)">
              <div class="class-radio">
                <input type="radio" :id="'class-' + idx" :value="tariff.type" v-model="selectedClass" />
              </div>
              <div class="class-content">
                <div class="tariff-grid">
                  <div class="tariff-left">
                    <h3 class="class-name">{{ tariff.type }}</h3>
                    <div class="class-price">
                      <span>{{ formatPrice(tariff.price * totalPassengers) }} ₽</span>
                    </div>
                  </div>
                  <div class="tariff-mid">
                    <div class="option-code">Класс {{ tariff.classCode }}</div>
                    <div class="option-seats">
                      <span class="seats-count">{{ tariff.seats }}</span>
                      <span class="seats-label">{{ getSeatsLabel(tariff.seats) }}</span>
                    </div>
                  </div>
                  <div class="tariff-right">
                    <div class="option-amenities">
                      <v-icon v-for="(amenity, aIdx) in tariff.amenities" :key="aIdx" size="20" class="amenity-icon">{{ amenity }}</v-icon>
                    </div>
                    <p class="option-description">{{ tariff.description }}</p>
                    <p v-if="tariff.petInfo" class="pet-info">
                      <span>{{ tariff.petInfo }}</span>
                      <a href="#" class="more-link">, подробнее</a>
                    </p>
                  </div>
                </div>
              </div>
            </div>

        <!-- Bottom Bar -->
        <div class="booking-bottom-bar">
          <div class="selected-info">
            <span class="selected-class">{{ selectedClassName }}</span>
          </div>
          <button class="continue-btn" :disabled="!selectedClass" @click="continueBooking">
            Продолжить
          </button>
        </div>
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
import { setRailTicketLoggedIn, setRailTicketCurrentUser, setRailTicketUserData, getRailTicketUserData, clearRailTicketLogin, getRailBookingSession, setRailBookingSession, syncRailTicketLoggedInFromTrack } from "@/utils/localCache.js";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";
import { benchUserContextMixin } from "@/common/benchUserContextMixin.js";
import { _logActivity } from "@/common/trackHelper";
import RailSearchHeader from "./components/RailSearchHeader.vue";
import RailLoginDrawer from "./components/RailLoginDrawer.vue";

export default defineComponent({
  name: "RailTarifSelection",
  mixins: [benchUserContextMixin,StateDelayMixin],
  components: { RailSearchHeader, RailLoginDrawer },
  data() {
    return {
      loginDrawer: false,
      loggedIn: false,
      selectedClass: null,
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
    bookingSession() {
      return getRailBookingSession() || {};
    },
    train() {
      return this.bookingSession.train || {
        id: "train_1",
        number: "022",
        name: "«Ночной экспресс»",
        fromStation: "Москва Октябрьская",
        toStation: "Санкт-Петербург-Главный",
        departureTime: "00:25",
        arrivalTime: "08:53",
        duration: "8ч 28м",
        durationMinutes: 508,
      };
    },
    departureDate() {
      return this.bookingSession.departureDate || new Date().toISOString().split('T')[0];
    },
    totalPassengers() {
      return (this.bookingSession.adults || 1) + (this.bookingSession.children || 0);
    },
    tariffMetadata() {
      return {
        "Купе": {
          classCode: "2Л",
          amenities: ["mdi-silverware-fork-knife", "mdi-bed", "mdi-snowflake", "mdi-toilet", "mdi-wifi", "mdi-power-plug", "mdi-gift-outline", "mdi-shoe-sneaker", "mdi-paw", "mdi-play-circle-outline"],
          description: "Купейный, 4-местные купе, кондиционер (работает в летний период), биотуалет, санитарно-гигиенический набор, розетки 220В, Wi-Fi (услуга не гарантирована), мультимедийный портал. Входит в программу «Динамическое ценообразование».",
          petInfo: "Возможен провоз мелких домашних животных за плату без выкупа отдельного места (вместе с пассажиром) или без платы с выкупом отдельного места по полному тарифу."
        },
        "СВ": {
          classCode: "1Б",
          amenities: ["mdi-silverware-fork-knife", "mdi-bed", "mdi-snowflake", "mdi-toilet", "mdi-wifi", "mdi-power-plug", "mdi-gift-outline", "mdi-shoe-sneaker", "mdi-food", "mdi-glass-wine"],
          description: "СВ с услугами бизнес-класса, 2-местные купе, кондиционер (работает в летний период), биотуалет, розетки 220В, Wi-Fi (услуга не гарантирована), мультимедийный портал. Входит в программу «Динамическое ценообразование».",
          petInfo: null
        },
        "Плацкартный": {
          classCode: "3Л",
          amenities: ["mdi-bed", "mdi-snowflake", "mdi-toilet", "mdi-power-plug"],
          description: "Плацкартный вагон с местами для лежания, кондиционер, биотуалет, розетки 220В. Входит в программу «Динамическое ценообразование».",
          petInfo: null
        },
        "Люкс": {
          classCode: "1А",
          amenities: ["mdi-silverware-fork-knife", "mdi-bed", "mdi-snowflake", "mdi-toilet", "mdi-wifi", "mdi-power-plug", "mdi-gift-outline", "mdi-shoe-sneaker", "mdi-food", "mdi-glass-wine", "mdi-television"],
          description: "Люкс, 2-местное купе повышенной комфортности, индивидуальный кондиционер, биотуалет, душ, телевизор, розетки 220В, Wi-Fi. Гарантированное питание. Дорожный набор, пресса, услуги бизнес-залов на вокзалах.",
          petInfo: null
        },
        "Базовый": {
          classCode: "2Р",
          amenities: ["mdi-seat-recline-normal", "mdi-power-plug", "mdi-wifi", "mdi-play-circle-outline"],
          description: "Кресла с подлокотниками, откидные или приоконные столики (кроме кресел, расположенных у входных групп).",
          petInfo: null
        },
        "Эконом": {
          classCode: "2С",
          amenities: ["mdi-seat-recline-normal", "mdi-power-plug", "mdi-wifi", "mdi-play-circle-outline", "mdi-sale"],
          description: "Кресла с подлокотниками и регулируемым основанием. Откидные или приоконные столики (кроме кресел, расположенных у входных групп). Доступ к медиацентру.",
          petInfo: null
        },
        "Эконом+": {
          classCode: "2С",
          amenities: ["mdi-seat-recline-normal", "mdi-power-plug", "mdi-wifi", "mdi-play-circle-outline", "mdi-sale", "mdi-gift-outline"],
          description: "Кресла с подлокотниками и регулируемым основанием. Увеличенное расстояние между креслами. Откидные или приоконные столики. Доступ к медиацентру.",
          petInfo: null
        },
        "Семейный": {
          classCode: "2Ю",
          amenities: ["mdi-seat-recline-normal", "mdi-power-plug", "mdi-wifi", "mdi-silverware-fork-knife", "mdi-play-circle-outline", "mdi-baby-carriage", "mdi-sale"],
          description: "Кресла с регулируемым основанием, подлокотниками и опорами для ног, откидной или приоконный столик. Гарантированное питание. Возможность предварительного выбора питания. Доступ к Медиацентру, розетка. Игровая зона для детей.",
          petInfo: null
        },
        "Вагон-бистро": {
          classCode: "2Е",
          amenities: ["mdi-silverware-fork-knife", "mdi-seat-recline-normal", "mdi-power-plug", "mdi-wifi", "mdi-play-circle-outline", "mdi-food"],
          description: "Кресла с регулируемым основанием и подлокотниками за столиками в вагоне-бистро. Гарантированное питание, напитки из меню вагона-бистро. Доступ к медиацентру.",
          petInfo: null
        },
        "Бизнес класс": {
          classCode: "1С",
          amenities: ["mdi-seat-recline-extra", "mdi-power-plug", "mdi-wifi", "mdi-silverware-fork-knife", "mdi-play-circle-outline", "mdi-gift-outline", "mdi-shoe-sneaker", "mdi-newspaper", "mdi-food"],
          description: "Кресла с регулируемым основанием, откидной или приоконный столик, возможность зарядки мобильных устройств и ноутбуков. Расстояние между креслами увеличено.",
          petInfo: null
        },
        "Бизнес": {
          classCode: "1С",
          amenities: ["mdi-seat-recline-extra", "mdi-power-plug", "mdi-wifi", "mdi-silverware-fork-knife", "mdi-play-circle-outline", "mdi-gift-outline", "mdi-shoe-sneaker", "mdi-newspaper", "mdi-food"],
          description: "Кресла с регулируемым основанием, откидной или приоконный столик, возможность зарядки мобильных устройств и ноутбуков. Расстояние между креслами увеличено.",
          petInfo: null
        },
        "Купе-сьют": {
          classCode: "1Ж",
          amenities: ["mdi-seat-recline-extra", "mdi-power-plug", "mdi-wifi", "mdi-silverware-fork-knife", "mdi-play-circle-outline", "mdi-gift-outline", "mdi-shoe-sneaker", "mdi-newspaper", "mdi-food", "mdi-bed"],
          description: "Купе-сьют — 2-х местное купе. Кресла повышенной комфортности, приоконный столик. Гарантированное питание. Возможность предварительного выбора питания. Дорожный набор, плед, подушка, пресса, доступ к Медиацентру, розетки, услуги бизнес-залов на вокзалах.",
          petInfo: null
        },
        "Первый класс": {
          classCode: "1В",
          amenities: ["mdi-seat-recline-extra", "mdi-power-plug", "mdi-wifi", "mdi-silverware-fork-knife", "mdi-play-circle-outline", "mdi-gift-outline", "mdi-shoe-sneaker", "mdi-newspaper", "mdi-food", "mdi-bed"],
          description: "Кресла повышенной комфортности с возможностью индивидуальной регулировки положения кресла и освещения. Возможность предварительного выбора питания. Дорожный набор, плед, подушка, пресса, доступ к медиацентру, розетка, услуги бизнес-залов на вокзалах.",
          petInfo: null
        },
        "Купе-переговорная": {
          classCode: "1Р",
          amenities: ["mdi-seat-recline-extra", "mdi-power-plug", "mdi-wifi", "mdi-silverware-fork-knife", "mdi-play-circle-outline", "mdi-gift-outline", "mdi-shoe-sneaker", "mdi-newspaper", "mdi-food", "mdi-bed", "mdi-paw"],
          description: "Купе-переговорная — 4-х местное купе с креслами первого класса повышенной комфортности. Возможность предварительного выбора питания. Дорожный набор, плед, подушка, пресса, доступ к медиацентру, розетки, услуги бизнес-залов на вокзалах.",
          petInfo: null
        },
        "Бизнес-купе": {
          classCode: "1Б",
          amenities: ["mdi-seat-recline-extra", "mdi-power-plug", "mdi-wifi", "mdi-silverware-fork-knife", "mdi-play-circle-outline", "mdi-gift-outline", "mdi-food", "mdi-bed"],
          description: "Бизнес-купе — 2-х местное купе с креслами бизнес-класса. Гарантированное питание. Возможность предварительного выбора питания. Дорожный набор, доступ к медиацентру, розетки, услуги бизнес-залов на вокзалах.",
          petInfo: null
        },
        "Сидячий": {
          classCode: "3С",
          amenities: ["mdi-seat-recline-normal", "mdi-power-plug", "mdi-wifi"],
          description: "Сидячий вагон, кресла с подлокотниками, розетки 220В, Wi-Fi (услуга не гарантирована). Входит в программу «Динамическое ценообразование».",
          petInfo: null
        },
        "Сидячий (бизнес)": {
          classCode: "1С",
          amenities: ["mdi-seat-recline-extra", "mdi-power-plug", "mdi-wifi", "mdi-silverware-fork-knife", "mdi-gift-outline"],
          description: "Сидячий бизнес-класс, кресла повышенной комфортности с увеличенным расстоянием, розетки 220В, Wi-Fi. Гарантированное питание.",
          petInfo: null
        },
        "Комфорт": {
          classCode: "2К",
          amenities: ["mdi-seat-recline-extra", "mdi-power-plug", "mdi-wifi", "mdi-play-circle-outline", "mdi-silverware-fork-knife"],
          description: "Кресла повышенной комфортности с увеличенным расстоянием между рядами, подлокотниками и опорами для ног. Гарантированное питание. Доступ к медиацентру.",
          petInfo: null
        },
        "Купе (для инвалидов)": {
          classCode: "2Л",
          amenities: ["mdi-wheelchair-accessibility", "mdi-bed", "mdi-snowflake", "mdi-toilet", "mdi-power-plug"],
          description: "Купейный вагон, специализированное купе для маломобильных пассажиров, 4-местные купе, кондиционер, биотуалет, розетки 220В.",
          petInfo: null
        },
        "Базовый (для инвалидов)": {
          classCode: "2Р",
          amenities: ["mdi-wheelchair-accessibility", "mdi-seat-recline-normal", "mdi-power-plug", "mdi-wifi"],
          description: "Специализированные места для маломобильных пассажиров. Кресла с подлокотниками, розетки 220В, Wi-Fi.",
          petInfo: null
        },
        "Эконом (для инвалидов)": {
          classCode: "2С",
          amenities: ["mdi-wheelchair-accessibility", "mdi-seat-recline-normal", "mdi-power-plug", "mdi-wifi", "mdi-play-circle-outline"],
          description: "Специализированные места для маломобильных пассажиров. Кресла с подлокотниками и регулируемым основанием. Откидные или приоконные столики. Доступ к медиацентру.",
          petInfo: null
        }
      };
    },
    tariffOptions() {
      const trainTickets = this.train.tickets || [];
      if (trainTickets.length === 0) {
        return [{
          type: "Купе",
          seats: 71,
          price: 5027,
          classCode: "2Л",
          amenities: ["mdi-silverware-fork-knife", "mdi-bed", "mdi-snowflake", "mdi-toilet", "mdi-wifi", "mdi-power-plug"],
          description: "Купейный, 4-местные купе, кондиционер, биотуалет, розетки 220В, Wi-Fi.",
          petInfo: null
        }];
      }
      return trainTickets.map(ticket => {
        const meta = this.tariffMetadata[ticket.type] || {};
        return {
          type: ticket.type,
          seats: ticket.seats,
          price: ticket.price,
          classCode: meta.classCode || "—",
          amenities: meta.amenities || [],
          description: meta.description || "",
          petInfo: meta.petInfo || null
        };
      });
    },
    selectedClassName() {
      return this.selectedClass || "";
    },
    isReturnTrip() {
      return !!this.bookingSession.isReturnTrip;
    },
    currentStep() {
      // For outbound trip: step 1 (tariff selection)
      // For return trip: step 4 (return tariff selection)
      return this.isReturnTrip ? 4 : 1;
    }
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
    selectClass(classType) {
      this.selectedClass = classType;
    },
    continueBooking() {
      if (!this.selectedClass) return;

      // Update booking session with selected tariff
      const session = getRailBookingSession() || {};
      const selectedTariff = this.tariffOptions.find(t => t.type === this.selectedClass);
      session.selectedClass = {
        type: this.selectedClass,
        name: this.selectedClass,
        price: selectedTariff?.price || 0,
        seats: selectedTariff?.seats || 0,
        classCode: selectedTariff?.classCode || ""
      };
      setRailBookingSession(session);

      // Log select_tariff event
      _logActivity(this, {
        type: "select_tariff",
        direction: this.isReturnTrip ? "return" : "outbound",
        tarif_name: this.selectedClass,
        price: selectedTariff?.price || 0,
      });

      // Navigate to seat selection
      this.$router.push({
        name: "bench_rail_seat_selection",
        params: {
          track_id: this.$route.params.track_id,
          state_id: this.$route.params.state_id,
        }
      });
    },
    formatPrice(price) {
      return price.toLocaleString("ru-RU");
    },
    formatDateShort(date) {
      if (!date) return "";
      const d = new Date(date);
      const day = d.getDate();
      const months = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
      const weekdays = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"];
      return `${day} ${months[d.getMonth()]}, ${weekdays[d.getDay()]}`;
    },
    getSeatsLabel(count) {
      if (count === 1) return "место";
      if (count >= 2 && count <= 4) return "места";
      if (count % 10 === 1 && count % 100 !== 11) return "место";
      if (count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 10 || count % 100 >= 20)) return "места";
      return "мест";
    },
    getStepClass(step) {
      const current = this.currentStep;
      if (step === current) return "step active";
      if (step < current) return "step completed";
      return "step";
    }
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

    // Check if we have a booking session
    const session = getRailBookingSession();
    if (!session || !session.train) {
      // No booking session, redirect back to search
      this.$router.push({
        name: "bench_rail_search",
        params: {
          track_id: this.$route.params.track_id,
          state_id: this.$route.params.state_id,
        }
      });
    } else {
      // Default select the first ticket type
      const tickets = (session.train && session.train.tickets) || [];
      if (tickets.length > 0) {
        this.selectedClass = tickets[0].type;
      }
    }
  }
});
</script>

<style src="@/assets/rail.css"></style>
<style scoped>
.bench-rail.rail-booking-page {
  background: #e9eaed;
  min-height: 100vh;
}

.rail-booking-page :deep(.rail-header) {
  width: 100vw;
  margin-left: calc(50% - 50vw);
}

.rail-booking-page :deep(.header-inner) {
  max-width: 1600px;
  margin: 0 auto;
}

.booking-content {
  max-width: 1064px;
  margin: 0 auto;
  padding: 20px;
}

.booking-container {
  background: #fff;
  padding: 20px;
}

.booking-header {
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
  background: #f0f0f0;
}

.steps-indicator {
  display: flex;
  gap: 8px;
}

.step {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #d7d7d7;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
}

.step.active {
  background: #e21a1a;
  color: #fff;
}

.step.completed {
  background: #e21a1a;
  color: #fff;
}

.booking-title {
  font-size: 24px;
  font-weight: 500;
  margin-left: 10px;
  color: #000;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.train-info-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px 0px 16px;
  border-radius: 8px;
  margin-bottom: 0px;
}

.train-info-content {
  font-size: 12px;
  color: #000;
}

.train-number {
  font-weight: 600;
  color: #000;
}

.train-name {
  color: #000;
  margin-left: 4px;
  font-weight: 600;
}

.train-route {
  color: #000;
  margin-left: 8px;
}

.train-departure {
  color: #000;
}

.qr-icon {
  color: #000;
}

.service-class-card {
  display: flex;
  padding: 20px;
  border: 2px solid #fff;
  cursor: pointer;
  transition: border-color 0.2s;
}

.service-class-card.selected {
  border: 2px solid #e21a1a;
}

.class-radio {
  margin-right: 16px;
  padding-top: 4px;
}

.class-radio input[type="radio"] {
  width: 20px;
  height: 20px;
  accent-color: #e21a1a;
  cursor: pointer;
}

.class-content {
  flex: 1;
}

.tariff-grid {
  display: grid;
  grid-template-columns: 200px 140px 1fr;
  column-gap: 24px;
  align-items: start;
}

.tariff-left {
  min-width: 0;
}

.class-name {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #000;
}

.class-price {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 500;
  color: #000;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.tariff-mid {
  min-width: 0;
  padding-top: 2px;
}

.option-code {
  font-size: 14px;
  font-weight: 400;
  color: #000;
}

.option-seats {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-top: 6px;
}

.seats-count {
  font-size: 18px;
  font-weight: 500;
  color: #000;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.seats-label {
  font-size: 14px;
  color: #000;
}

.tariff-right {
  min-width: 0;
}

.option-amenities {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.amenity-icon {
  color: #000;
}

.option-description {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  margin: 0 0 8px;
  text-indent: 0;
}

.pet-info {
  font-size: 14px;
  color: #666;
  margin: 0;
  text-indent: 0;
}

.more-link {
  color: #e21a1a;
  text-decoration: none;
}

.more-link:hover {
  text-decoration: underline;
}

@media (max-width: 760px) {
  .tariff-grid {
    grid-template-columns: 1fr;
    row-gap: 12px;
  }
}

.booking-bottom-bar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 16px 0;
  gap: 16px;
}

.selected-info {
  font-size: 16px;
  color: #222;
}

.selected-class {
  font-weight: 600;
}

.continue-btn {
  background: #e21a1a;
  color: #fff;
  border: none;
  padding: 14px 48px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  text-transform: uppercase;
  min-width: 420px;
}

.continue-btn:hover:not(:disabled) {
  background: #c91515;
}

.continue-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
