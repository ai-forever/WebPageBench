<template>
  <v-dialog v-model="internalOpen" max-width="440">
    <v-card class="login-card">
      <div class="login-header">
        <v-btn v-if="step !== 'login'" class="login-back" icon variant="text" @click="goBack">
          <v-icon size="20">mdi-arrow-left</v-icon>
        </v-btn>
        <div class="login-title">{{ step === 'password' ? 'Ввести пароль' : 'Войти' }}</div>
        <v-btn class="login-close" icon variant="text" @click="close">
          <v-icon size="20">mdi-close</v-icon>
        </v-btn>
      </div>
      <div class="login-body">
        <template v-if="step === 'login'">
          <div class="login-label">Введите почту или логин</div>
          <v-text-field
            v-model="login"
            class="login-input"
            placeholder="Почта или логин"
            variant="solo"
            :error="loginError"
            :error-messages="loginError ? 'Поле не может быть пустым' : ''"
            hide-details="auto"
            density="comfortable"
          />

          <v-btn class="login-primary" block @click="continueLogin">Продолжить</v-btn>

          <div class="login-or">
            <span class="line"></span>
            <span class="or">или</span>
            <span class="line"></span>
          </div>

          <v-btn class="login-secondary" block @click="phoneLogin">Номер телефона</v-btn>
          <v-btn class="login-link" variant="text" block @click="otherLogin">Другие способы</v-btn>

          <div class="login-disclaimer">
            При входе на ресурс вы принимаете
            <a href="#">публичную оферту</a> и
            <a href="#">обработку персональных данных</a>
          </div>
        </template>

        <template v-else-if="step === 'phone'">
          <div class="login-label">Введите номер телефона</div>
          <v-text-field
            v-model="phone"
            class="login-input phone-input"
            placeholder="999 999 99 99"
            variant="solo"
            :error="phoneError"
            :error-messages="phoneError ? 'Поле не может быть пустым' : ''"
            hide-details="auto"
            density="comfortable"
            @keypress="allowOnlyDigits"
            @keyup.enter="submitPhone"
            @keydown.enter.prevent="submitPhone"
          >
            <template #prepend-inner>
              <v-menu v-model="countryMenu" location="bottom" :close-on-content-click="true" max-height="320">
                <template #activator="{ props }">
                  <button class="country-btn" v-bind="props" type="button">
                    <img class="flag-img" :src="selectedCountry.flagSrc" alt="" width="24" height="16" />
                    <v-icon size="16">mdi-chevron-down</v-icon>
                  </button>
                </template>
                <v-card class="country-menu">
                  <div class="country-menu-title">Код страны</div>
                  <!-- <v-text-field
                    v-model="countrySearch"
                    class="country-search"
                    placeholder="Страна или код"
                    variant="solo"
                    density="comfortable"
                    hide-details
                  /> -->
                  <v-list class="country-list" lines="one">
                    <v-list-item
                      v-for="c in filteredCountries"
                      :key="c.code"
                      @click="selectCountry(c)"
                    >
                      <template #prepend>
                        <img class="flag-img" :src="c.flagSrc" alt="" width="24" height="16" />
                      </template>
                      <v-list-item-title class="pl-2">{{ c.name }}</v-list-item-title>
                      <template #append>
                        <span class="dial-code">+{{ c.dialCode }}</span>
                      </template>
                    </v-list-item>
                  </v-list>
                </v-card>
              </v-menu>
              <span class="country-code">+{{ selectedCountry.dialCode }}</span>
            </template>
          </v-text-field>

          <v-btn class="login-primary" block @click="submitPhone">Продолжить</v-btn>
        </template>

        <template v-else>
          <div class="login-label">
            Введите пароль для <span class="login-email">{{ login }}</span>
          </div>

          <v-text-field
            v-model="password"
            class="login-input"
            placeholder="Пароль"
            :type="showPassword ? 'text' : 'password'"
            variant="solo"
            :error="passwordError"
            :error-messages="passwordError ? passwordErrorText : ''"
            hide-details="auto"
            density="comfortable"
            :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
            @click:append-inner="showPassword = !showPassword"
            @keyup.enter="submitPassword"
            @keydown.enter.prevent="submitPassword"
          />

          <v-btn class="login-primary" block @click="submitPassword">Войти</v-btn>

          <v-btn class="forgot-link" variant="text" @click="forgotPassword">Забыли пароль?</v-btn>
        </template>
      </div>
    </v-card>
  </v-dialog>
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import { setLoggedIn } from "@/utils/localCache.js";
import { _logActivity } from "@/common/trackHelper";
import { getBenchPersonalInfo } from "@/common/benchPersonalInfo.js";

export default defineComponent({
  name: "LoginDialog",
  props: {
    modelValue: { type: Boolean, default: false },
    loginData: { type: Object, default: null },
  },
  emits: ["update:modelValue", "success"],
  data() {
    return {
      login: "",
      password: "",
      showPassword: false,
      step: "login", // 'login' | 'phone' | 'password'
      loginError: false,
      passwordError: false,
      passwordErrorText: "",
      authMethod: null,
      // phone login state
      phone: "",
      phoneError: false,
      countries: [
        { name: "Россия", code: "RU", dialCode: "7", flagSrc: new URL('@/assets/img/general/flags/ru.svg', import.meta.url).href },
        { name: "Абхазия", code: "AB", dialCode: "79407", flagSrc: new URL('@/assets/img/general/flags/ab.svg', import.meta.url).href },
        { name: "Австралия", code: "AU", dialCode: "61", flagSrc: new URL('@/assets/img/general/flags/au.svg', import.meta.url).href },
        { name: "Австрия", code: "AT", dialCode: "43", flagSrc: new URL('@/assets/img/general/flags/at.svg', import.meta.url).href },
        { name: "Азербайджан", code: "AZ", dialCode: "994", flagSrc: new URL('@/assets/img/general/flags/az.svg', import.meta.url).href },
        { name: "Армения", code: "AM", dialCode: "374", flagSrc: new URL('@/assets/img/general/flags/am.svg', import.meta.url).href },
      ],
      selectedCountry: { name: "Россия", code: "RU", dialCode: "7", flagSrc: new URL('@/assets/img/general/flags/ru.svg', import.meta.url).href },
      countryMenu: false,
      countrySearch: "",
    };
  },
  computed: {
    ...mapGetters(["trackConfig"]),
    personalInfo() {
      return getBenchPersonalInfo(this.trackConfig);
    },
    contactPhoneDigits() {
      return String(this.personalInfo.phone || "").replace(/\D/g, "");
    },
    filteredCountries() {
      const q = (this.countrySearch || "").toLowerCase().trim();
      if (!q) return this.countries;
      return this.countries.filter(c =>
        c.name.toLowerCase().includes(q) ||
        c.code.toLowerCase().includes(q) ||
        (`+${c.dialCode}`).includes(q.replace(/[^0-9+]/g, ""))
      );
    },
    internalOpen: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit("update:modelValue", value);
      },
    },
  },
  methods: {
    selectCountry(c) {
      this.selectedCountry = c;
      this.countryMenu = false;
    },
    close() {
      this.internalOpen = false;
      this.resetState();
    },
    continueLogin() {
      this.loginError = !this.login;
      if (!this.login || this.login != this.loginData.login) {
        _logActivity(this, { type: 'submit_login', value: this.login || '', result: 'failed' });
      } else {
        _logActivity(this, { type: 'submit_login', value: this.login, result: 'success' });
      }
      if (!this.login) {
        return;
      }
      this.authMethod = 'email';
      this.step = "password";
    },
    phoneLogin() { this.step = 'phone'; _logActivity(this, { type: 'login_phone' }); },
    otherLogin() { 
      // alert('Другие способы входа'); 
    },
    goBack() {
      this.step = "login";
      this.password = "";
      this.showPassword = false;
      this.passwordError = false;
      this.phone = "";
      this.phoneError = false;
      this.authMethod = null;
    },
    allowOnlyDigits(event) {
      const char = String.fromCharCode(event.which || event.keyCode);
      if (!/[0-9]/.test(char)) {
        event.preventDefault();
      }
    },
    submitPhone() {
      this.phoneError = !this.phone;
      if (this.phoneError) { _logActivity(this, { type: 'submit_phone', phone: this.phone || '', value: this.phone || '', result: 'failed' }); return; }

      const expectedLocal = this.contactPhoneDigits
        ? this.contactPhoneDigits.slice(-10)
        : "";
      const enteredLocal = String(this.phone).replace(/\D/g, "");

      if (expectedLocal && enteredLocal !== expectedLocal) {
        // alert('fail');
        _logActivity(this, { type: 'submit_phone', phone: this.phone, value: this.phone, result: 'failed' });
        return;
      }

      this.authMethod = 'phone';
      this.step = 'password';
      this.login = `+${this.selectedCountry.dialCode} ${enteredLocal}`;
      _logActivity(this, { type: 'submit_phone', phone: this.phone, value: this.phone, result: 'success' });
    },
    submitPassword() {
      console.log("Password", this.password);
      console.log("LoginData", this.loginData);

      this.passwordError = !this.password;
      if (this.passwordError) {
        this.passwordErrorText = 'Поле не может быть пустым';
        _logActivity(this, { type: 'submit_pass', value: this.password || '', result: 'failed' });
        return;
      }
      if (this.loginData && this.loginData.password) {
        const okByEmail = this.authMethod === 'email' && this.login === this.loginData.login && this.password === this.loginData.password;
        const expectedPhone = this.contactPhoneDigits ? this.contactPhoneDigits.slice(-10) : "";
        const enteredPhone = String(this.phone).replace(/\D/g, "");
        const okByPhone = this.authMethod === 'phone' && expectedPhone && enteredPhone === expectedPhone && this.password === this.loginData.password;
        if (okByEmail || okByPhone) {
          _logActivity(this, { type: 'submit_pass', value: this.password, result: 'success' });
          setLoggedIn(true);
          this.$emit('success');
          this.close();
          return;
        } else {
          // alert('fail');
          _logActivity(this, { type: 'submit_pass', value: this.password, result: 'failed' });
          // show error message
          this.passwordErrorText = 'Введен неверный пароль';
          this.passwordError = true;
          return;
        }
      }
    },
    forgotPassword() {
      // alert("Забыли пароль? (test)");
    },
    resetState() {
      // this.step = "login";
      this.password = "";
      this.showPassword = false;
      this.loginError = false;
      this.passwordError = false;
      this.passwordErrorText = "";
      this.phone = "";
      this.phoneError = false;
      this.selectedCountry = this.countries[0];
    },
  },
  watch: {
    modelValue(val) {
      if (val) {
        this.resetState();
        _logActivity(this, { type: 'dialog_opened', name: 'login' });
      }
    },
  }
});
</script>

<style scoped>
/* Login dialog styles */
.login-card { border-radius: 16px; }
.login-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 30px 44px 0 44px;
}
.login-back { color: #9aa0a6; }
.login-title { font-size: 24px; font-weight: 800; }
.login-close { color: #9aa0a6; }
.login-body { padding: 12px 44px 44px 44px; }
.login-label { font-weight: 500; margin-bottom: 15px; margin-top: 15px; color: #1f1f1f; }
.login-email { font-weight: 800; }
.login-input .v-field {
  background: #f5f6fa;
  border: 1px solid #e2e3ea;
  border-radius: 10px;
  box-shadow: none;
}
.login-input .v-field__input { min-height: 44px; }
.login-primary {
  margin-top: 25px;
  height: 48px;
  border-radius: 10px;
  background: #3b3bd8;
  color: #ffffff;
  text-transform: none;
  font-weight: 800;
  font-size: 16px;
}
.login-or { margin: 20px 0; display: flex; align-items: center; justify-content: center; gap: 12px; }
.login-or .line { height: 2px; width: 36px; background: #eceef5; border-radius: 2px; }
.login-or .or { color: #a1a6b3; }
.login-secondary {
  height: 48px;
  border-radius: 10px;
  background: #ece9ff;
  color: #3b3bd8;
  text-transform: none;
  font-weight: 800;
  font-size: 16px;
}
.login-link { padding: 25px 20px; border-radius: 10px; font-weight: 800; font-size: 16px; margin: 20px 0; color: #3b3bd8; text-transform: none; justify-content: center; }
.login-disclaimer { font-size: 12px; color: #3f3f46; text-align: center; margin-top: 16px; }
.login-disclaimer a { color: #3b3bd8; text-decoration: underline; }
.forgot-link { margin-top: 12px; color: #3b3bd8; text-transform: none; font-weight: 700; }
/* Phone dropdown styles to match sample */
.phone-input .v-field__prepend-inner { padding-right: 8px; }
.country-btn { display: inline-flex; align-items: center; gap: 6px; background: transparent; border: none; cursor: pointer; padding: 0 6px; }
.country-btn .flag-img { display: inline-block; width: 24px; height: 16px; border-radius: 2px; box-shadow: inset 0 0 0 1px rgba(0,0,0,0.06); }
.country-menu { padding: 8px; width: 320px; }
.country-menu-title { font-weight: 600; padding: 6px 8px 8px 8px; }
.country-search .v-field { background: #ffffff; }
.country-list .dial-code { color: #6b7280; margin-left: 16px; }
.flag-img { width: 24px; height: 16px; border-radius: 2px; box-shadow: inset 0 0 0 1px rgba(0,0,0,0.06); }
/* Always-visible country code inside input */
.phone-input .v-field__prepend-inner { display: inline-flex; align-items: center; gap: 8px; }
.country-code { color: #1f2937; font-weight: 600; }
</style>
