<template>
  <!-- Keep `.bench-rail` mounted immediately so app-shell styles apply from first paint (prevents width blink) -->
  <div class="bench-rail">
    <div v-if="!configLoaded" class="loading-box">
      <v-progress-circular indeterminate color="#e21a1a" :size="48"></v-progress-circular>
    </div>

    <template v-else>
      <!-- Header -->
      <RailHeader :rail-logo="railLogo" :is-logged-in="loggedIn" :user-name="currentUserName" @open-login="openLoginDialog" @logout="handleLogout" />

      <!-- Hero -->
      <section class="hero">
        <div class="hero-inner">
          <h1 class="hero-title">
            <span class="red">КУПИТЬ БИЛЕТ</span>, ПОСМОТРЕТЬ РАСПИСАНИЕ
          </h1>
          <RailSearchWidget
            v-model="searchForm"
            @search="handleSearch"
          />
        </div>
      </section>

      <div v-if="!contentReady" class="loading-box">
        <v-progress-circular indeterminate color="#e21a1a" :size="48"></v-progress-circular>
      </div>

      <!-- Cards Section - First Row -->
      <section v-if="contentReady" class="cards-section">
        <!-- Announcements -->
        <div class="announcements">
          <p class="announcement">
            С 20 января 2026 года вносятся <a href="#">изменения <v-icon size="12">mdi-open-in-new</v-icon></a> в ФЗ «О порядке выезда из Российской Федерации и въезда в Российскую Федерацию».
          </p>
          <p class="announcement">
            Здание Ленинградского вокзала Москвы закрыто на ремонт. Схема прохода на посадку в поезда <a href="#">здесь <v-icon size="12">mdi-open-in-new</v-icon></a>
          </p>
        </div>

        <div class="cards-inner">
          <div class="cards-grid first-row">
            <!-- My Tickets -->
            <div class="info-card">
              <div class="card-head">
                <h3>Мои билеты</h3>
                <v-icon class="arrow" size="22">mdi-arrow-right</v-icon>
              </div>
              <ul class="card-links">
                <li><a href="#">Личный кабинет пассажира на tickets.example</a></li>
                <li><a href="#">Программа «Бонус»</a></li>
                <li><a href="#">Купить премиальный билет</a></li>
              </ul>
            </div>

            <!-- Support -->
            <div class="info-card support-card">
              <div class="card-head">
                <h3>Служба поддержки</h3>
                <v-icon class="arrow" size="22">mdi-arrow-right</v-icon>
              </div>
              <div class="phone">8 800 775-00-00</div>
              <div class="phone-hint">Центр поддержки клиентов оператор</div>
              <a href="#" class="email">служба поддержки</a>
              <div class="email-hint">Для вопросов по электронным билетам</div>
              <a href="#" class="svo-link">Участникам СВО</a>
            </div>

          </div>
        </div>
      </section>

      <!-- Bottom Info Cards -->
      <section v-if="contentReady" class="info-section">
        <div class="info-section-inner">
          <div class="info-grid">
            <div class="info-block">
              <h3>Перед поездкой</h3>
              <p>Информация в дорогу</p>
              <p class="phone-row"><strong>8 800 775-00-00</strong></p>
              <p class="hint">Заказ билета по телефону</p>
              <p class="phone-row mb-6"><strong>8 800 250-15-20</strong></p>
              <v-icon class="arrow-icon" size="26">mdi-arrow-right</v-icon>
            </div>
            <div class="info-block">
              <h3>В поезде</h3>
              <p>Услуги в поезде, доставка еды к поезду, категории поездов, типы вагонов</p>
              <v-icon class="arrow-icon" size="26">mdi-arrow-right</v-icon>
            </div>
            <div class="info-block">
              <h3>После поездки</h3>
              <p>Услуги после поездки, поиск забытых вещей</p>
              <v-icon class="arrow-icon" size="26">mdi-arrow-right</v-icon>
            </div>
          </div>
        </div>
      </section>

      <!-- Additional Promo Section - Row 1 -->
      <section v-if="contentReady" class="promo-section">
        <div class="promo-section-inner">
          <div class="promo-grid row1">
            <!-- Speed Trains - Large -->
            <div class="promo-card large" :style="{ backgroundImage: `url(${speedTrainsBg})` }">
              <div class="overlay">
                <div class="card-head">
                  <h3>Скоростные поезда</h3>
                </div>
                <ul class="promo-links">
                  <li>«экспресс», «Ласточка», «Финист»,</li>
                  <li>«Невский экспресс», «Аврора», «Буревестник»</li>
                </ul>
                <div class="card-bottom">
                  <v-icon class="arrow" size="22">mdi-arrow-right</v-icon>
                  <span class="bottom-text">ДЕЛОВЫЕ ПРОЕЗДНЫЕ</span>
                </div>
              </div>
            </div>

            <!-- Hotels Tours -->
            <div class="promo-card medium" :style="{ backgroundImage: `url(${hotelsToursBg})` }">
              <div class="overlay">
                <div class="card-head">
                  <h3>Отели, экскурсии,<br>туры</h3>
                </div>
                <p class="promo-text">Всё путешествие в одном сервисе</p>
                <v-icon class="arrow" size="22">mdi-arrow-right</v-icon>
              </div>
            </div>

            <!-- Auto Transport -->
            <div class="promo-card medium" :style="{ backgroundImage: `url(${autoTransportBg})` }">
              <div class="overlay">
                <div class="card-head">
                  <h3>Перевозка<br>автомобилей<br>и мотоциклов</h3>
                </div>
                <p class="promo-text">Будь всегда АВТОмобилен!</p>
                <v-icon class="arrow" size="22">mdi-arrow-right</v-icon>
              </div>
            </div>
          </div>

          <!-- Row 2 -->
          <div class="promo-grid row2">
            <!-- Museums -->
            <div class="promo-card small" :style="{ backgroundImage: `url(${museumsBg})` }">
              <div class="overlay">
                <div class="card-head">
                  <h3>Музеи железных<br>дорог</h3>
                </div>
                <p class="promo-text">Железнодорожные музеи, станции – музейные комплексы, исторические линии</p>
                <v-icon class="arrow" size="22">mdi-arrow-right</v-icon>
              </div>
            </div>

            <!-- Kids Railway -->
            <div class="promo-card small" :style="{ backgroundImage: `url(${kidsRailwayBg})` }">
              <div class="overlay">
                <div class="card-head">
                  <h3>Детские<br>железные дороги</h3>
                </div>
                <v-icon class="arrow" size="22">mdi-arrow-right</v-icon>
              </div>
            </div>

            <!-- Multimodal - Large -->
            <div class="promo-card wide" :style="{ backgroundImage: `url(${multimodalBg})` }">
              <div class="overlay">
                <div class="card-head">
                  <h3>Мультимодальные перевозки<br>(поезд+автобус,<br>поезд+самолет,<br>поезд+теплоход)</h3>
                </div>
                <div class="card-bottom">
                  <v-icon class="arrow" size="22">mdi-arrow-right</v-icon>
                  <span class="bottom-text">КУРОРТЫ КРАСНОДАРСКОГО КРАЯ (САМОЛЕТ+ПОЕЗД)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Cookie Bar -->
      <!-- <div v-if="showCookie" class="cookie-bar">
        <p>
          Мы используем cookie-файлы для улучшения пользовательского опыта и сбора статистики. 
          Для получения дополнительной информации вы можете ознакомиться с нашей 
          <a href="#">Политикой использования cookie-файлов</a>.
        </p>
        <button @click="showCookie = false">ПРИНЯТЬ</button>
      </div> -->

      <!-- Login Dialog -->
      <RailLoginDialog
        v-model="loginDialog"
        :login-credentials="loginCredentials"
        :user-data="loginCredentials"
        @login="handleLogin"
        @register="handleRegister"
      />
    </template>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { railAssets } from "@/assets/rail-assets.js";
import { setRailLoggedIn, setRailCurrentUser, setRailUserData, getRailUserData, clearRailLogin, clearRailBookingSession, syncRailLoggedInFromTrack } from "@/utils/localCache.js";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";
import { benchUserContextMixin } from "@/common/benchUserContextMixin.js";
import RailHeader from "./components/RailHeader.vue";
import RailLoginDialog from "./components/RailLoginDialog.vue";
import RailSearchWidget from "./components/RailSearchWidget.vue";

export default defineComponent({
  name: "RailMain",
  mixins: [benchUserContextMixin,StateDelayMixin],
  components: { RailHeader, RailLoginDialog, RailSearchWidget },
  data() {
    return {
      loginDialog: false,
      loggedIn: false,
      kvStoreReady: false,
      showCookie: true,
      searchForm: {
        from: "",
        to: "",
        departureDate: null,
        returnDate: null,
        passengers: {
          adults: 1,
          childrenWithSeat: 0,
          childrenWithoutSeat: 0,
          forDisabled: false,
          forLargeFamilies: false,
          pet: false,
          car: false,
          motorcycle: false,
        },
      },
    };
  },
  computed: {
    ...mapGetters(["trackConfig", "kvStore"]),
    configLoaded() { return this.trackConfig && Object.keys(this.trackConfig).length > 0; },
    common() { return (this.trackConfig && this.trackConfig.common_elements) || {}; },
    testData() { return (this.trackConfig && this.trackConfig.test_data) || {}; },
    loginCredentials() { return (this.testData && this.testData.login_data) || {}; },
    configUserData() {
      return this.railPrimaryPassenger;
    },
    currentUserName() {
      if (!this.loggedIn) return "";
      const userData = getRailUserData();
      return userData.name || "";
    },
    travelBg() { return railAssets['travel_promo'] || ''; },
    dedMorozBg() { return railAssets['ded_moroz'] || ''; },
    accessibilityBg() { return railAssets['accessibility'] || ''; },
    discountsBg() { return railAssets['discounts'] || ''; },
    speedTrainsBg() { return railAssets['speed_trains'] || ''; },
    hotelsToursBg() { return railAssets['hotels_tours'] || ''; },
    autoTransportBg() { return railAssets['auto_transport'] || ''; },
    museumsBg() { return railAssets['museums'] || ''; },
    kidsRailwayBg() { return railAssets['kids_railway'] || ''; },
    multimodalBg() { return railAssets['multimodal'] || ''; },
    railLogo() { return railAssets['rail_logo'] || ''; },
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    handleLogin(formData) {
      this.loggedIn = true;
      setRailLoggedIn(true);
      setRailCurrentUser(formData.username || 'guest');
      setRailUserData(formData.userData || {});
    },
    handleRegister(formData) {
      this.loggedIn = true;
      setRailLoggedIn(true);
      setRailCurrentUser(formData.username || 'guest');
    },
    handleLogout() {
      this.loggedIn = false;
      clearRailLogin();
    },
    handleSearch(formData) {
      // Clear any existing booking session to ensure fresh outbound search
      clearRailBookingSession();

      const toLocalISO = (value) => {
        const d = value instanceof Date ? value : new Date(value);
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
      };

      // Navigate to search page with query parameters (local calendar date, not UTC)
      const query = {
        from: formData.from || '',
        to: formData.to || '',
        date: formData.departureDate ? toLocalISO(formData.departureDate) : '',
        adults: formData.passengers.adults || 1,
        children: (formData.passengers.childrenWithSeat || 0) + (formData.passengers.childrenWithoutSeat || 0),
      };
      if (formData.returnDate) {
        query.returnDate = toLocalISO(formData.returnDate);
      }
      this.$router.push({
        name: 'bench_rail_search',
        params: {
          track_id: this.$route.params.track_id,
          state_id: this.$route.params.state_id,
        },
        query,
      });
    },
    getTrackConfig() {
      this.$store.dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id }).then(() => {
        this.loggedIn = syncRailLoggedInFromTrack(this.trackConfig);
        if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
          this.$router.push({ name: "not_found" });
          return;
        }
        const kvPath = this.testData.kv_store_path || "";
        if (kvPath) {
          this.$store.dispatch(GET_KV_STORE, { kvPath }).then(() => { this.kvStoreReady = true; });
        } else {
          this.kvStoreReady = true;
        }
        if (!this.trackConfig[this.$route.params.state_id]) {
          this.$router.push({ name: "state_not_found" });
        }
        this.applyStateDelay();
      });
    },
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      const kvPath = this.testData.kv_store_path || "";
      if (kvPath && !this.kvStoreReady) {
        this.$store.dispatch(GET_KV_STORE, { kvPath }).then(() => { this.kvStoreReady = true; });
      } else if (!kvPath) {
        this.kvStoreReady = true;
      }
      this.applyStateDelay();
    }
    this.loggedIn = syncRailLoggedInFromTrack(this.trackConfig);
  },
});
</script>

<style src="@/assets/rail.css"></style>
