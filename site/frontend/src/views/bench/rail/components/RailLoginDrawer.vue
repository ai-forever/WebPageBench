<template>
  <Teleport to="body">
    <!-- Overlay -->
    <Transition name="fade">
      <div v-if="modelValue" class="rail-drawer-overlay" @click="close"></div>
    </Transition>

    <!-- Drawer -->
    <Transition name="slide">
      <div v-if="modelValue" class="rail-login-drawer">
        <!-- Close button -->
        <button class="drawer-close-btn" @click="close">
          <v-icon size="24">mdi-close</v-icon>
        </button>

        <!-- Content: Login Form or User Menu -->
        <div class="drawer-content">
          <!-- User Menu (when logged in) -->
          <template v-if="isLoggedIn">
            <div class="user-profile-section">
              <div class="user-avatar">
                <v-icon size="64" color="#ccc">mdi-account-circle-outline</v-icon>
              </div>
              <div class="user-info">
                <span class="user-name">{{ currentUserName }}</span>
                <span class="user-email">{{ currentUserEmail }}</span>
              </div>
            </div>

            <nav class="user-menu">
              <router-link :to="profileTo" class="menu-item" @click="close">
                <v-icon size="20">mdi-account-outline</v-icon>
                <span>Профиль</span>
              </router-link>
              <a href="#" class="menu-item" @click.prevent>
                <v-icon size="20">mdi-ticket-outline</v-icon>
                <span>Мои заказы</span>
              </a>
              <a href="#" class="menu-item" @click.prevent>
                <v-icon size="20">mdi-account-multiple-outline</v-icon>
                <span>Пассажиры</span>
                <span v-if="passengersCount > 0" class="menu-badge">{{ passengersCount }}</span>
              </a>
              <a href="#" class="menu-item" @click.prevent>
                <v-icon size="20">mdi-cog-outline</v-icon>
                <span>Мои предпочтения</span>
              </a>
              <a href="#" class="menu-item" @click.prevent>
                <v-icon size="20">mdi-heart-outline</v-icon>
                <span>Избранные маршруты</span>
              </a>
              <a href="#" class="menu-item" @click.prevent>
                <v-icon size="20">mdi-credit-card-outline</v-icon>
                <span>Проездные карты</span>
              </a>
              <a href="#" class="menu-item" @click.prevent>
                <v-icon size="20">mdi-gift-outline</v-icon>
                <span>Бонус</span>
              </a>
              <a href="#" class="menu-item" @click.prevent>
                <v-icon size="20">mdi-car-outline</v-icon>
                <span>Перевозка авто/мототранспорта</span>
              </a>
              <a href="#" class="menu-item" @click.prevent>
                <v-icon size="20">mdi-calendar-outline</v-icon>
                <span>Мероприятия</span>
              </a>
              <a href="#" class="menu-item" @click.prevent>
                <v-icon size="20">mdi-clock-outline</v-icon>
                <span>Заявки в лист ожидания</span>
              </a>
            </nav>

            <div class="drawer-divider"></div>

            <button class="logout-btn" @click="handleLogout">
              <v-icon size="20">mdi-logout</v-icon>
              <span>Выйти</span>
            </button>
          </template>

          <!-- Login Form (when not logged in) -->
          <template v-else>
            <h2 class="drawer-title">Вход в личный кабинет</h2>

            <div class="login-form">
              <div class="form-field">
                <label>Логин <span class="required">*</span></label>
                <input
                  type="text"
                  v-model="loginForm.username"
                  placeholder="Логин"
                  @keyup.enter="handleLogin"
                />
              </div>

              <div class="form-field">
                <label>Пароль <span class="required">*</span></label>
                <input
                  type="password"
                  v-model="loginForm.password"
                  placeholder="Пароль"
                  @keyup.enter="handleLogin"
                />
              </div>

              <div v-if="loginError" class="login-error">{{ loginError }}</div>

              <a href="#" class="forgot-link" @click.prevent>Забыли пароль?</a>

              <button class="login-btn" @click="handleLogin">ВОЙТИ</button>

              <div class="divider-row">
                <span class="divider-line"></span>
                <span class="divider-text">или через</span>
                <span class="divider-line"></span>
              </div>

              <button class="portal-btn" @click.prevent>портал услуг</button>

              <button class="register-btn" @click.prevent>СОЗДАТЬ ЛИЧНЫЙ КАБИНЕТ</button>
            </div>
          </template>

          <!-- Bottom Links -->
          <div class="drawer-bottom">
            <a href="#" class="bottom-link" @click.prevent>
              <v-icon size="18">mdi-help-circle-outline</v-icon>
              <span>Служба поддержки</span>
            </a>
            <a href="#" class="bottom-link" @click.prevent>
              <v-icon size="18">mdi-information-outline</v-icon>
              <span>О сайте</span>
            </a>
          </div>

          <!-- Footer -->
          <div class="drawer-footer">
            <p>&copy; 2003–2025 оператор</p>
            <p>Вы находитесь на новой версии портала оператор</p>
            <p class="version">v.10.143.1.3902</p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { defineComponent } from "vue";

export default defineComponent({
  name: "RailLoginDrawer",
  props: {
    modelValue: {
      type: Boolean,
      default: false,
    },
    isLoggedIn: {
      type: Boolean,
      default: false,
    },
    loginCredentials: {
      type: Object,
      default: () => ({}),
    },
    userData: {
      type: Object,
      default: () => ({}),
    },
    currentUserName: {
      type: String,
      default: "",
    },
    currentUserEmail: {
      type: String,
      default: "",
    },
    passengersCount: {
      type: Number,
      default: 0,
    },
  },
  emits: ["update:modelValue", "login", "logout", "login-error"],
  data() {
    return {
      loginForm: {
        username: "",
        password: "",
      },
      loginError: "",
    };
  },
  computed: {
    profileTo() {
      const { track_id } = (this.$route && this.$route.params) || {};
      if (track_id) {
        return { name: "bench_rail_profile", params: { track_id, state_id: "state_profile" } };
      }
      return { name: "main" };
    },
  },
  watch: {
    modelValue(newVal) {
      if (newVal) {
        document.body.style.overflow = "hidden";
      } else {
        document.body.style.overflow = "";
      }
    },
  },
  methods: {
    close() {
      this.$emit("update:modelValue", false);
      this.loginError = "";
    },
    handleLogin() {
      const creds = this.loginCredentials || {};
      const expectedLogin = creds.login || "";
      const expectedPassword = creds.password || "";

      if (this.loginForm.username === expectedLogin && this.loginForm.password === expectedPassword) {
        this.$emit("login", { ...this.loginForm, userData: this.userData });
        this.loginForm.username = "";
        this.loginForm.password = "";
        this.loginError = "";
        this.close();
      } else {
        this.loginError = "Неверный логин или пароль";
        this.$emit("login-error", this.loginError);
      }
    },
    handleLogout() {
      this.$emit("logout");
      this.close();
    },
  },
  beforeUnmount() {
    document.body.style.overflow = "";
  },
});
</script>

<style scoped>
/* Overlay */
.rail-drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 2000;
}

/* Drawer */
.rail-login-drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 380px;
  max-width: 100vw;
  height: 100vh;
  background: #fff;
  z-index: 2001;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.15);
  overflow-y: auto;
}

.drawer-close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: #666;
  z-index: 1;
}

.drawer-close-btn:hover {
  color: #333;
}

/* Drawer Content */
.drawer-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px;
  padding-top: 48px;
}

/* User Profile Section (logged in) */
.user-profile-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 0 24px;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 8px;
}

.user-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 2px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.user-name {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.user-email {
  font-size: 14px;
  color: #666;
}

/* User Menu */
.user-menu {
  display: flex;
  flex-direction: column;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 0;
  color: #333;
  text-decoration: none;
  font-size: 15px;
  border-bottom: 1px solid #f0f0f0;
  transition: color 0.2s;
}

.menu-item:hover {
  color: #e21a1a;
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-badge {
  margin-left: auto;
  background: #e21a1a;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}

.drawer-divider {
  height: 1px;
  background: #e0e0e0;
  margin: 8px 0;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 0;
  background: none;
  border: none;
  cursor: pointer;
  color: #333;
  font-size: 15px;
  width: 100%;
  text-align: left;
}

.logout-btn:hover {
  color: #e21a1a;
}

/* Login Form (not logged in) */
.drawer-title {
  font-size: 22px;
  font-weight: 600;
  margin: 0 0 24px;
  color: #333;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-field label {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.form-field label .required {
  color: #e21a1a;
}

.form-field input {
  padding: 12px 14px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 15px;
  outline: none;
  transition: border-color 0.2s;
}

.form-field input:focus {
  border-color: #e21a1a;
}

.login-error {
  color: #e21a1a;
  font-size: 13px;
  padding: 8px 12px;
  background: #fff5f5;
  border-radius: 4px;
}

.forgot-link {
  font-size: 14px;
  color: #666;
  text-decoration: none;
  align-self: flex-start;
}

.forgot-link:hover {
  color: #e21a1a;
  text-decoration: underline;
}

.login-btn {
  background: #e21a1a;
  color: #fff;
  border: none;
  padding: 14px 24px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 8px;
}

.login-btn:hover {
  background: #c91515;
}

.divider-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 8px 0;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: #e0e0e0;
}

.divider-text {
  font-size: 13px;
  color: #999;
}

.portal-btn {
  background: #333;
  color: #fff;
  border: none;
  padding: 14px 24px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.portal-btn:hover {
  background: #444;
}

.register-btn {
  background: #fff;
  color: #333;
  border: 2px solid #333;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.register-btn:hover {
  background: #f5f5f5;
}

/* Bottom Links */
.drawer-bottom {
  margin-top: auto;
  padding-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bottom-link {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #333;
  text-decoration: none;
  font-size: 14px;
}

.bottom-link:hover {
  color: #e21a1a;
}

/* Footer */
.drawer-footer {
  padding-top: 24px;
  font-size: 11px;
  color: #999;
  line-height: 1.5;
}

.drawer-footer p {
  margin: 0 0 4px;
  text-indent: 0;
}

.drawer-footer a {
  color: #999;
}

.drawer-footer a:hover {
  color: #e21a1a;
}

.drawer-footer .version {
  margin-top: 8px;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
