<template>
  <div class="bench-rail rail-profile-page">
    <div v-if="!configLoaded" class="loading-box">
      <v-progress-circular indeterminate color="#e21a1a" :size="48"></v-progress-circular>
    </div>

    <template v-else>
      <!-- Header -->
      <RailHeader :rail-logo="railLogo" :is-logged-in="loggedIn" :user-name="currentUserName" @open-login="openLoginDialog" @logout="handleLogout" />

      <!-- Hero with user name -->
      <section class="profile-hero">
        <div class="profile-hero-inner">
          <h1 class="profile-hero-title">{{ fullUserName }}</h1>
        </div>
      </section>

      <!-- Profile Content -->
      <section class="profile-content">
        <div class="profile-content-inner">
          <!-- Sidebar -->
          <aside class="profile-sidebar">
            <h2 class="sidebar-title">Мой профиль</h2>
            <ul class="sidebar-menu">
              <li :class="{ active: activeTab === 'data' }">
                <button @click="activeTab = 'data'">Мои данные</button>
              </li>
              <li :class="{ active: activeTab === 'password' }">
                <button @click="activeTab = 'password'">Смена пароля</button>
              </li>
              <li :class="{ active: activeTab === 'bonus' }">
                <button @click="activeTab = 'bonus'">Бонус</button>
              </li>
              <li :class="{ active: activeTab === 'subscriptions' }">
                <button @click="activeTab = 'subscriptions'">Подписки</button>
              </li>
            </ul>
          </aside>

          <!-- Main Content -->
          <div class="profile-main">
            <!-- My Data Tab -->
            <div v-if="activeTab === 'data'" class="profile-form-section">
              <h3 class="form-section-title">Мои данные</h3>

              <bench-profile-info-card :info="personalInfo" class="profile-summary-card" />

              <div class="form-group full-width">
                <label>Мой логин</label>
                <input type="text" :value="profileForm.login" readonly class="readonly-field" />
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label>Фамилия<span class="required">*</span></label>
                  <input type="text" v-model="profileForm.lastName" placeholder="Фамилия" />
                </div>
                <div class="form-group">
                  <label>Имя<span class="required">*</span></label>
                  <input type="text" v-model="profileForm.firstName" placeholder="Имя" />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label>Отчество</label>
                  <input type="text" v-model="profileForm.middleName" placeholder="Отчество" />
                </div>
                <div class="form-group">
                  <label>E-mail<span class="required">*</span></label>
                  <input type="email" v-model="profileForm.email" placeholder="Адрес электронной почты" />
                </div>
              </div>

              <div class="form-row three-cols">
                <div class="form-group">
                  <label>Телефон</label>
                  <input type="tel" v-model="profileForm.phone" placeholder="Номер телефона" />
                </div>
                <div class="form-group">
                  <label>Дата рождения</label>
                  <input type="text" v-model="profileForm.birthDate" placeholder="дд.мм.гггг" />
                </div>
                <div class="form-group">
                  <label>Пол</label>
                  <select v-model="profileForm.gender">
                    <option value="">Выберите</option>
                    <option value="male">Мужской</option>
                    <option value="female">Женский</option>
                  </select>
                </div>
              </div>

              <div class="form-checkbox">
                <input type="checkbox" id="marketing" v-model="profileForm.marketingConsent" />
                <label for="marketing">
                  Даю свое <a href="#">согласие</a> на получение рекламно-информационных рассылок от АО «Федеральная пассажирская компания».
                </label>
              </div>

              <div class="form-actions">
                <button class="btn-save" @click="saveProfile">СОХРАНИТЬ</button>
              </div>
            </div>

            <!-- Change Password Tab -->
            <div v-if="activeTab === 'password'" class="profile-form-section">
              <h3 class="form-section-title">Смена пароля</h3>

              <div class="form-group" style="max-width: 400px;">
                <label>Текущий пароль<span class="required">*</span></label>
                <input type="password" v-model="passwordForm.currentPassword" placeholder="Текущий пароль" />
              </div>

              <div class="form-group" style="max-width: 400px;">
                <label>Новый пароль<span class="required">*</span></label>
                <input type="password" v-model="passwordForm.newPassword" placeholder="Новый пароль" />
              </div>

              <div class="form-group" style="max-width: 400px;">
                <label>Подтверждение пароля<span class="required">*</span></label>
                <input type="password" v-model="passwordForm.confirmPassword" placeholder="Подтверждение пароля" />
              </div>

              <div class="form-actions">
                <button class="btn-save" @click="changePassword">СОХРАНИТЬ</button>
              </div>
            </div>

            <!-- ЖД Bonus Tab -->
            <div v-if="activeTab === 'bonus'" class="profile-form-section">
              <h3 class="form-section-title">Бонус</h3>

              <div class="bonus-card-info">
                <div class="bonus-number">
                  <label>Номер карты Бонус</label>
                  <div class="bonus-value">{{ userData.rail_bonus_number || 'Не привязана' }}</div>
                </div>
                <div class="bonus-points">
                  <label>Баллы</label>
                  <div class="bonus-value points">{{ formatPoints(userData.rail_bonus_points) }}</div>
                </div>
              </div>

              <p class="bonus-info-text">
                Программа лояльности «Бонус» позволяет накапливать баллы за поездки и обменивать их на премиальные билеты.
              </p>
            </div>

            <!-- Subscriptions Tab -->
            <div v-if="activeTab === 'subscriptions'" class="profile-form-section">
              <h3 class="form-section-title">Подписки</h3>

              <div class="subscription-item">
                <input type="checkbox" id="sub-news" v-model="subscriptions.news" />
                <label for="sub-news">Новости и акции</label>
              </div>

              <div class="subscription-item">
                <input type="checkbox" id="sub-schedule" v-model="subscriptions.schedule" />
                <label for="sub-schedule">Изменения в расписании</label>
              </div>

              <div class="subscription-item">
                <input type="checkbox" id="sub-bonus" v-model="subscriptions.bonus" />
                <label for="sub-bonus">Уведомления Бонус</label>
              </div>

              <div class="form-actions">
                <button class="btn-save" @click="saveSubscriptions">СОХРАНИТЬ</button>
              </div>
            </div>
          </div>
        </div>
      </section>

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
import { isRailLoggedIn, setRailLoggedIn, setRailCurrentUser, setRailUserData, getRailUserData, clearRailLogin, syncRailLoggedInFromTrack } from "@/utils/localCache.js";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";
import { benchUserContextMixin } from "@/common/benchUserContextMixin.js";
import RailHeader from "./components/RailHeader.vue";
import RailLoginDialog from "./components/RailLoginDialog.vue";
import BenchProfileInfoCard from "@/views/ui/BenchProfileInfoCard.vue";

export default defineComponent({
  name: "RailProfile",
  mixins: [benchUserContextMixin,StateDelayMixin],
  components: { RailHeader, RailLoginDialog, BenchProfileInfoCard },
  data() {
    return {
      loginDialog: false,
      loggedIn: false,
      kvStoreReady: false,
      activeTab: "data",
      profileForm: {
        login: "",
        lastName: "",
        firstName: "",
        middleName: "",
        email: "",
        phone: "",
        birthDate: "",
        gender: "",
        marketingConsent: false,
      },
      passwordForm: {
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      },
      subscriptions: {
        news: true,
        schedule: false,
        bonus: true,
      },
    };
  },
  computed: {
    ...mapGetters(["trackConfig", "kvStore"]),
    configLoaded() { return this.trackConfig && Object.keys(this.trackConfig).length > 0; },
    common() { return (this.trackConfig && this.trackConfig.common_elements) || {}; },
    testData() { return (this.trackConfig && this.trackConfig.test_data) || {}; },
    loginCredentials() { return this.benchLoginData; },
    configUserData() {
      return this.railPrimaryPassenger;
    },
    userData() { return getRailUserData(); },
    currentUserName() {
      if (!this.loggedIn) return "";
      return this.personalInfo.fullName;
    },
    fullUserName() {
      return this.personalInfo.fullName;
    },
    railLogo() { return railAssets['rail_logo'] || ''; },
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    handleLogin(formData) {
      this.loggedIn = true;
      setRailLoggedIn(true);
      setRailCurrentUser(formData.username || 'guest');
      setRailUserData(formData.userData || {});
      this.populateProfileForm();
    },
    handleRegister(formData) {
      this.loggedIn = true;
      setRailLoggedIn(true);
      setRailCurrentUser(formData.username || 'guest');
    },
    handleLogout() {
      this.loggedIn = false;
      clearRailLogin();
      // Redirect to main page after logout
      this.$router.push({
        name: 'bench_rail_main',
        params: {
          track_id: this.$route.params.track_id,
          state_id: this.$route.params.state_id,
        },
      });
    },
    populateProfileForm() {
      const personal = this.personalInfo;
      const userData = getRailUserData();
      const loginData = this.loginCredentials;

      this.profileForm.login = loginData.login || personal.email || "";
      this.profileForm.lastName = personal.surname || "";
      this.profileForm.firstName = personal.name || "";
      this.profileForm.middleName = personal.patronymic || "";
      this.profileForm.email = personal.email || userData.email || "";
      this.profileForm.phone = personal.phone || userData.phone || "";
      this.profileForm.birthDate = userData.birthDate || userData.birthday || "";
      this.profileForm.gender = userData.gender || "";
    },
    saveProfile() {
      // In a real app, this would save to backend
      console.log("Profile saved:", this.profileForm);
    },
    changePassword() {
      if (this.passwordForm.newPassword !== this.passwordForm.confirmPassword) {
        alert("Пароли не совпадают");
        return;
      }
      console.log("Password changed");
      this.passwordForm = { currentPassword: "", newPassword: "", confirmPassword: "" };
    },
    saveSubscriptions() {
      console.log("Subscriptions saved:", this.subscriptions);
    },
    formatPoints(points) {
      if (!points) return "0";
      return points.toLocaleString("ru-RU");
    },
    getTrackConfig() {
      return this.$store.dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id }).then(() => {
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
    const boot = () => {
      const kvPath = this.testData.kv_store_path || "";
      if (kvPath && !this.kvStoreReady) {
        this.$store.dispatch(GET_KV_STORE, { kvPath }).then(() => { this.kvStoreReady = true; });
      } else if (!kvPath) {
        this.kvStoreReady = true;
      }
      this.applyStateDelay();
      this.loggedIn = syncRailLoggedInFromTrack(this.trackConfig);
      if (!this.loggedIn) {
        this.$router.push({
          name: 'bench_rail_main',
          params: {
            track_id: this.$route.params.track_id,
            state_id: 'state_main',
          },
        });
        return;
      }
      this.populateProfileForm();
    };

    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig().then(boot);
    } else {
      boot();
    }
  },
});
</script>

<style src="@/assets/rail.css"></style>

<style scoped>
.rail-profile-page {
  background: #e9eaed;
  min-height: 100vh;
}

/* Profile Hero */
.profile-hero {
  background: var(--rail-gray);
  padding: 0 0 40px 0;
  position: relative;
}

.profile-hero-inner {
  max-width: 1260px;
  margin: 0 auto;
  padding: 40px 20px;
}

.profile-hero-title {
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
  font-size: 42px;
  font-weight: 400;
  color: #fff;
  margin: 0;
}

/* Profile Content */
.profile-content {
  max-width: 1260px;
  margin: 0 auto;
  padding: 0 20px 40px;
  margin-top: 50px;
}

.profile-content-inner {
  display: flex;
  gap: 24px;
  background: #fff;
}

/* Sidebar */
.profile-sidebar {
  width: 280px;
  flex-shrink: 0;
  padding: 24px;
  border-right: 1px solid #e0e0e0;
}

.sidebar-title {
  font-size: 18px;
  font-weight: 600;
  color: #000;
  margin: 0 0 20px;
}

.sidebar-menu {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sidebar-menu li {
  border-left: 3px solid transparent;
  margin-bottom: 0;
}

.sidebar-menu li.active {
  border-left-color: #e21a1a;
}

.sidebar-menu li button {
  display: block;
  width: 100%;
  text-align: left;
  padding: 12px 16px;
  background: none;
  border: none;
  font-size: 14px;
  color: #333;
  cursor: pointer;
}

.sidebar-menu li.active button {
  color: #e21a1a;
  font-weight: 500;
}

.sidebar-menu li button:hover {
  color: #e21a1a;
}

/* Main Content */
.profile-main {
  flex: 1;
  padding: 24px 32px;
}

.profile-form-section {
  max-width: 800px;
}

.profile-summary-card {
  margin-bottom: 24px;
}

.form-section-title {
  font-size: 20px;
  font-weight: 600;
  color: #000;
  margin: 0 0 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e0e0e0;
}

/* Form Groups */
.form-group {
  margin-bottom: 20px;
}

.form-group.full-width {
  max-width: 100%;
}

.form-group label {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 6px;
}

.form-group label .required {
  color: #e21a1a;
  margin-left: 2px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #ccc;
  font-size: 15px;
  background: #fff;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #e21a1a;
}

.form-group input.readonly-field {
  background: #f5f5f5;
  color: #666;
}

/* Form Rows */
.form-row {
  display: flex;
  gap: 20px;
}

.form-row .form-group {
  flex: 1;
}

.form-row.three-cols .form-group {
  flex: 1;
}

/* Checkbox */
.form-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin: 24px 0;
}

.form-checkbox input[type="checkbox"] {
  margin-top: 4px;
}

.form-checkbox label {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

.form-checkbox label a {
  color: #e21a1a;
}

/* Form Actions */
.form-actions {
  margin-top: 24px;
}

.btn-save {
  background: #e21a1a;
  color: #fff;
  border: none;
  padding: 14px 40px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.btn-save:hover {
  background: #c41515;
}

/* Bonus Card */
.bonus-card-info {
  display: flex;
  gap: 40px;
  margin-bottom: 24px;
  padding: 20px;
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
}

.bonus-number,
.bonus-points {
  display: flex;
  flex-direction: column;
}

.bonus-number label,
.bonus-points label {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.bonus-value {
  font-size: 20px;
  font-weight: 600;
  color: #000;
}

.bonus-value.points {
  color: #e21a1a;
}

.bonus-info-text {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

/* Subscriptions */
.subscription-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.subscription-item label {
  font-size: 14px;
  color: #333;
}
</style>
