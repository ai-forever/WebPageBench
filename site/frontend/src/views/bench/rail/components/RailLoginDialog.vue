<template>
  <div v-if="modelValue" class="rail-login-overlay" @click.self="close">
    <div class="rail-login-card">
      <!-- Tabs -->
      <div class="rail-login-tabs">
        <div
          class="rail-login-tab"
          :class="{ active: activeTab === 'login' }"
          @click="activeTab = 'login'"
        >
          ВХОД
        </div>
        <div
          class="rail-login-tab"
          :class="{ active: activeTab === 'register' }"
          @click="activeTab = 'register'"
        >
          РЕГИСТРАЦИЯ
        </div>
      </div>

      <!-- Login Form -->
      <div v-if="activeTab === 'login'" class="rail-login-form">
        <div v-if="loginError" class="rail-login-error">{{ loginError }}</div>
        <div class="rail-form-row">
          <div class="rail-form-field">
            <label>Логин<span class="required">*</span></label>
            <input type="text" v-model="loginForm.username" placeholder="Логин" @keyup.enter="handleLogin" />
          </div>
          <div class="rail-form-field">
            <label>Пароль<span class="required">*</span></label>
            <input type="password" v-model="loginForm.password" placeholder="Пароль" @keyup.enter="handleLogin" />
            <a href="#" class="forgot-link">Забыли пароль?</a>
          </div>
        </div>
        <div class="rail-dialog-actions">
          <button class="btn-cancel" @click="close">ОТМЕНА</button>
          <button class="btn-submit" @click="handleLogin">ВОЙТИ</button>
        </div>
      </div>

      <!-- Registration Form -->
      <div v-if="activeTab === 'register'" class="rail-login-form rail-register-form">
        <div class="rail-form-row">
          <div class="rail-form-field">
            <label>Email<span class="required">*</span></label>
            <input type="email" v-model="registerForm.email" placeholder="Адрес электронной почты" />
          </div>
          <div class="rail-form-field">
            <label>Логин<span class="required">*</span> <span class="hint-icon" title="Логин должен быть уникальным">?</span></label>
            <input type="text" v-model="registerForm.username" placeholder="Логин" />
          </div>
        </div>
        <div class="rail-form-row">
          <div class="rail-form-field">
            <label>Пароль<span class="required">*</span> <span class="hint-icon" title="Минимум 8 символов">?</span></label>
            <input type="password" v-model="registerForm.password" placeholder="Пароль" />
          </div>
          <div class="rail-form-field">
            <label>Подтверждение пароля<span class="required">*</span></label>
            <input type="password" v-model="registerForm.confirmPassword" placeholder="Подтверждение пароля" />
          </div>
        </div>
        <div class="rail-form-row">
          <div class="rail-form-field">
            <label>Имя<span class="required">*</span></label>
            <input type="text" v-model="registerForm.firstName" placeholder="Имя" />
          </div>
          <div class="rail-form-field">
            <label>Фамилия<span class="required">*</span></label>
            <input type="text" v-model="registerForm.lastName" placeholder="Фамилия" />
          </div>
        </div>
        <div class="rail-form-row single">
          <div class="rail-form-field">
            <label>Телефон</label>
            <input type="tel" v-model="registerForm.phone" placeholder="Номер телефона" />
          </div>
        </div>

        <div class="rail-separator"></div>

        <div class="rail-checkbox-row">
          <input type="checkbox" id="consent1" v-model="registerForm.dataConsent" />
          <label for="consent1">
            Даю свое <a href="#">согласие</a> оператор на обработку представленных мной персональных данных. <a href="#">Политика обработки персональных данных в оператор</a><span class="required">*</span>
          </label>
        </div>

        <div class="rail-separator"></div>

        <div class="rail-checkbox-row">
          <input type="checkbox" id="consent2" v-model="registerForm.marketingConsent" />
          <label for="consent2">
            Даю свое <a href="#">согласие</a> на получение рекламно-информационных рассылок от АО «Федеральная пассажирская компания».
          </label>
        </div>

        <div class="rail-captcha-row">
          <div class="rail-form-field captcha-field">
            <label>Защитный код<span class="required">*</span></label>
            <input type="text" v-model="registerForm.captcha" placeholder="Защитный код" />
          </div>
          <div class="captcha-controls">
            <button type="button" class="captcha-btn" title="Обновить">
              <v-icon size="20">mdi-refresh</v-icon>
            </button>
            <button type="button" class="captcha-btn" title="Прослушать">
              <v-icon size="20">mdi-volume-high</v-icon>
              <span>Прослушать</span>
            </button>
            <div class="captcha-image">
              <span class="captcha-text">3A3B53</span>
            </div>
          </div>
        </div>

        <div class="rail-legal-text">
          <p>Сохраняя регистрационные данные, я соглашаюсь со следующим:</p>
          <ul>
            <li>регистрационные данные указаны мною добровольно.</li>
          </ul>
          <p><a href="#">Политика обработки персональных данных в оператор</a></p>
          <p><a href="#">Положение об обработке и защите персональных данных в АО «ФПК»</a></p>
        </div>

        <div class="rail-dialog-actions">
          <button class="btn-cancel" @click="close">ОТМЕНА</button>
          <button class="btn-submit" @click="handleRegister">ЗАРЕГИСТРОВАТЬСЯ</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from "vue";

export default defineComponent({
  name: "RailLoginDialog",
  props: {
    modelValue: {
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
  },
  emits: ["update:modelValue", "login", "register", "login-error"],
  data() {
    return {
      activeTab: "login",
      loginForm: {
        username: "",
        password: "",
      },
      registerForm: {
        email: "",
        username: "",
        password: "",
        confirmPassword: "",
        firstName: "",
        lastName: "",
        phone: "",
        dataConsent: false,
        marketingConsent: false,
        captcha: "",
      },
      loginError: "",
    };
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
    handleRegister() {
      this.$emit("register", { ...this.registerForm });
      this.close();
    },
  },
});
</script>

<style src="@/assets/rail.css"></style>
