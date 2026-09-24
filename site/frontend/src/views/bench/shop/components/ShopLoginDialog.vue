<template>
  <v-dialog v-model="dialogVisible" max-width="448" transition="shop-dialog-transition">
    <div class="bench-market-login-dialog">
      <!-- Close Button -->
      <v-btn
        icon
        class="close-btn"
        variant="text"
        size="small"
        @click="closeDialog"
      >
        <v-icon size="20">mdi-close</v-icon>
      </v-btn>

      <!-- ID покупателя Logo -->
      <div class="logo-container">
        <img :src="shopIdLogo" alt="ID покупателя" class="shop-id-logo" />
      </div>

      <!-- Phone Login View -->
      <div v-if="viewMode === 'phone'">
        <!-- Title -->
        <h1 class="dialog-title">Введите номер телефона</h1>

        <!-- Subtitle -->
        <p class="dialog-subtitle">
          Мы отправим код или позвоним. Отвечать на звонок не нужно. Код может прийти на почту или в СМС
        </p>

      <!-- Phone Input Container -->
      <div class="phone-input-container">
        <!-- Country Code Selector -->
        <v-menu offset-y>
          <template #activator="{ props }">
            <div class="country-selector" v-bind="props">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" class="flag-icon">
                <rect width="19" height="13" x="2.5" y="5.5" stroke="#001A34" stroke-opacity=".16" opacity=".75" rx="2.5"></rect>
                <path fill="white" d="M3 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2H3z"></path>
                <path fill="#0055CC" d="M3 10h18v4H3z"></path>
                <path fill="#F0121F" d="M3 14h18v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
              </svg>
              <span class="country-code">+7</span>
              <v-icon size="16" class="dropdown-icon">mdi-chevron-down</v-icon>
            </div>
          </template>
          <v-list class="country-list">
            <v-list-item>
              <v-list-item-title>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" class="flag-icon-small">
                  <rect width="19" height="13" x="2.5" y="5.5" stroke="#001A34" stroke-opacity=".16" opacity=".75" rx="2.5"></rect>
                  <path fill="white" d="M3 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2H3z"></path>
                  <path fill="#0055CC" d="M3 10h18v4H3z"></path>
                  <path fill="#F0121F" d="M3 14h18v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                </svg>
                +7
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>

        <!-- Phone Input Field -->
        <v-text-field
          v-model="phone"
          class="phone-input"
          placeholder="999 999 99 99"
          variant="outlined"
          :error-messages="phoneError"
          density="comfortable"
          @input="phoneError = ''"
          @keyup.enter="handleLogin"
        />
      </div>

      <!-- Login Button -->
      <v-btn
        class="login-btn"
        color="#005bff"
        size="x-large"
        block
        @click="handleLogin"
      >
        Войти
      </v-btn>

      <!-- Separator -->
      <div class="separator">
        <span class="separator-text">или</span>
      </div>

      <!-- Social Login Buttons -->
      <div class="social-buttons">
        <!-- Apple Login -->
        <v-btn
          class="social-btn apple-btn"
          size="x-large"
          variant="flat"
          block
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" class="social-icon">
            <path fill="currentColor" d="M19.459 7.818c-.122.09-2.26 1.244-2.26 3.81 0 2.969 2.72 4.019 2.801 4.045-.014.064-.433 1.438-1.435 2.838-.893 1.232-1.827 2.463-3.248 2.463s-1.787-.79-3.424-.79c-1.598 0-2.166.816-3.466.816-1.299 0-2.206-1.14-3.248-2.54C3.974 16.813 3 14.26 3 11.836c0-3.889 2.64-5.95 5.238-5.95 1.38 0 2.531.869 3.397.869.826 0 2.112-.92 3.682-.92.595 0 2.734.052 4.142 1.983m-4.886-3.63c.65-.738 1.11-1.762 1.11-2.786 0-.143-.014-.285-.041-.402-1.056.039-2.315.674-3.073 1.517-.595.648-1.15 1.672-1.15 2.709 0 .155.027.31.04.363.068.013.176.026.285.026.947 0 2.138-.61 2.829-1.426"></path>
          </svg>
          <span class="social-text">Вход с Apple</span>
        </v-btn>

        <!-- VK Login -->
        <v-btn
          class="social-btn vk-btn"
          size="x-large"
          variant="outlined"
          block
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" class="social-icon vk-icon">
            <path fill="#0077FF" d="M3.406 3.406C2 4.812 2 7.075 2 11.6v.8c0 4.525 0 6.788 1.406 8.194S7.075 22 11.6 22h.8c4.525 0 6.788 0 8.194-1.406S22 16.925 22 12.4v-.8c0-4.525 0-6.788-1.406-8.194S16.925 2 12.4 2h-.8C7.075 2 4.812 2 3.406 3.406m1.969 4.677h2.283c.075 3.817 1.759 5.434 3.092 5.767V8.083h2.15v3.292c1.317-.142 2.7-1.642 3.167-3.292h2.15c-.359 2.034-1.859 3.534-2.925 4.15 1.066.5 2.775 1.809 3.425 4.175H16.35c-.508-1.583-1.775-2.808-3.45-2.975v2.975h-.258c-4.559 0-7.159-3.125-7.267-8.325"></path>
          </svg>
          <span class="social-text">Войти с VK ID</span>
        </v-btn>

        <!-- Portal login -->
        <v-btn
          class="social-btn portal-btn"
          size="x-large"
          variant="outlined"
          block
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" class="social-icon">
            <path fill="url(#portal-gradient)" d="M14.51 2.486C13.666 2.204 12.788 2 12 2s-1.666.204-2.51.486c-.857.287-1.743.677-2.564 1.099a20 20 0 0 0-2.232 1.323c-.609.42-1.172.875-1.491 1.292-.585.763-.869 1.742-1.02 2.71C2.03 9.892 2 10.97 2 12s.03 2.108.183 3.09c.151.968.435 1.947 1.02 2.71.32.417.882.872 1.491 1.292.635.44 1.41.902 2.232 1.323.821.422 1.707.812 2.564 1.099.844.282 1.723.486 2.51.486.788 0 1.666-.204 2.51-.486a19 19 0 0 0 2.564-1.099 20 20 0 0 0 2.232-1.323c.609-.42 1.172-.875 1.491-1.292.585-.763.869-1.742 1.02-2.71.153-.982.183-2.06.183-3.09s-.03-2.108-.183-3.09c-.151-.968-.435-1.947-1.02-2.71-.32-.417-.882-.872-1.491-1.292a20 20 0 0 0-2.232-1.323 19 19 0 0 0-2.564-1.099M3 10a1 1 0 0 1 1-1h5a1 1 0 0 1 0 2H4a1 1 0 0 1-1-1m0 4a1 1 0 0 1 1-1h11a1 1 0 1 1 0 2H4a1 1 0 0 1-1-1"></path>
            <defs>
              <linearGradient id="portal-gradient" x1="12" x2="12" y1="4" y2="20" gradientUnits="userSpaceOnUse">
                <stop stop-color="#2A64AE"></stop>
                <stop offset="1" stop-color="#F1405A"></stop>
              </linearGradient>
            </defs>
          </svg>
          <span class="social-text">Вход через портал услуг</span>
        </v-btn>
      </div>

        <!-- Bottom Links -->
        <div class="bottom-links">
          <v-btn
            class="link-btn"
            variant="text"
            @click="loginByEmail"
          >
            Войти по почте
          </v-btn>
          <v-btn
            class="link-btn"
            variant="text"
            @click="cannotLogin"
          >
            Не могу войти
          </v-btn>
        </div>
      </div>

      <!-- Email Login View -->
      <div v-if="viewMode === 'email'">
        <!-- Title -->
        <h1 class="dialog-title">Войдите по почте</h1>

        <!-- Subtitle -->
        <p class="dialog-subtitle">
          Только для зарегистрированных пользователей
        </p>

        <!-- Email Input Container -->
        <div class="email-input-container">
          <v-text-field
            v-model="email"
            class="email-input"
            placeholder="Электронная почта"
            type="email"
            variant="outlined"
            :error-messages="emailError"
            density="comfortable"
            @keyup.enter="handleEmailLogin"
            @input="emailError = ''"
          />
        </div>

        <!-- Login Button -->
        <v-btn
          class="login-btn"
          color="#005bff"
          size="x-large"
          block
          @click="handleEmailLogin"
        >
          Войти
        </v-btn>

        <!-- Bottom Links -->
        <div class="bottom-links">
          <v-btn
            class="link-btn"
            variant="text"
            @click="backToPhone"
          >
            Вернуться на главный экран
          </v-btn>
          <v-btn
            class="link-btn"
            variant="text"
            @click="cannotLogin"
          >
            Не могу войти
          </v-btn>
        </div>
      </div>

      <!-- Code Verification View -->
      <div v-if="viewMode === 'code'">
        <!-- Title -->
        <h1 class="dialog-title">Введите последние 6 цифр входящего номера</h1>

        <!-- Example -->
        <p class="code-example">
          Например +X XXX X
          <span class="code-badge">12 34 56</span>
        </p>

        <!-- Subtitle -->
        <p class="code-subtitle">
          Отвечать на звонок не нужно
        </p>

        <!-- Phone with edit link -->
        <p class="phone-display">
          Уже звоним на {{ contactPhoneDisplay }}.
          <a href="javascript:void(0)" class="edit-link" @click="editPhone">Изменить</a>
        </p>

        <!-- Code Input -->
        <div class="code-input-container">
          <v-text-field
            v-model="code"
            class="code-input"
            variant="outlined"
            density="comfortable"
            :error-messages="codeError"
            maxlength="6"
            @input="onCodeInput"
          />
        </div>

        <!-- Countdown -->
        <p class="countdown-text">
          Получить новый код можно через {{ formatCountdown() }}
        </p>

        <!-- Bottom Links -->
        <div class="bottom-links">
          <v-btn
            class="link-btn"
            variant="text"
            @click="loginByEmail"
          >
            Войти по почте
          </v-btn>
          <v-btn
            class="link-btn"
            variant="text"
            @click="cannotLogin"
          >
            Не могу войти
          </v-btn>
        </div>
      </div>
    </div>
  </v-dialog>
</template>

<script>
import { shopAssets } from '@/assets/shop-assets.js';
import { setLoggedIn, setCurrentUsername } from '@/utils/localCache.js';
import { _logActivity } from '@/common/trackHelper';
import { mapGetters } from 'vuex';
import { getBenchPersonalInfo } from '@/common/benchPersonalInfo.js';

export default {
  name: 'ShopLoginDialog',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    loginData: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['update:modelValue', 'success'],
  data() {
    return {
      phone: '',
      countryCode: '+7',
      viewMode: 'phone', // 'phone', 'email', or 'code'
      email: '',
      emailError: '',
      phoneError: '',
      code: '',
      codeError: '',
      countdown: 60,
      countdownTimer: null
    };
  },
  computed: {
    ...mapGetters(['trackConfig']),
    personalInfo() {
      return getBenchPersonalInfo(this.trackConfig);
    },
    contactPhoneDigits() {
      return String(this.personalInfo.phone || '').replace(/\D/g, '');
    },
    contactPhoneDisplay() {
      const digits = this.contactPhoneDigits;
      if (digits.length >= 10) {
        return `+7 ${digits.slice(-10, -7)} ${digits.slice(-7, -4)}-${digits.slice(-4, -2)}-${digits.slice(-2)}`;
      }
      return this.personalInfo.phone || this.phone || '';
    },
    dialogVisible: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit('update:modelValue', value);
      }
    },
    shopIdLogo() {
      return shopAssets['shop_id'] || '';
    }
  },
  watch: {
    dialogVisible(newValue) {
      // Reset to phone view when dialog opens
      if (newValue) {
        this.viewMode = 'phone';
        this.phone = '';
        this.email = '';
        this.phoneError = '';
        this.emailError = '';
        this.code = '';
        this.codeError = '';
        this.stopCountdown();
      }
    },
    code(newValue) {
      // Auto-validate when user types 6 digits
      const cleanCode = newValue.replace(/\s/g, '');
      if (cleanCode.length === 6) {
        this.validateAndSubmitCode();
      }
    }
  },
  methods: {
    closeDialog() {
      this.dialogVisible = false;
      this.phoneError = '';
      this.emailError = '';
      this.viewMode = 'phone';
      this.stopCountdown();
    },
    handleLogin() {
      _logActivity(this, { type: 'submit_phone', value: this.phone || '' });
      // Validate phone number
      const phoneDigits = this.phone.replace(/\D/g, '');

      // Simple validation - just check if we have a phone number
      if (phoneDigits.length < 10) {
        this.phoneError = 'Некорректный формат телефона';
        return;
      }

      // Check against login data if provided
      if (this.loginData && this.loginData.login) {
        const expectedPhone = this.contactPhoneDigits;
        if (expectedPhone && phoneDigits !== expectedPhone) {
          this.phoneError = 'Некорректный формат телефона';
          return;
        }
      }

      // Clear error and go to code verification
      this.phoneError = '';
      this.viewMode = 'code';
      this.startCountdown();
    },
    loginByEmail() {
      // Switch to email view
      this.viewMode = 'email';
      this.emailError = '';
      this.email = '';
    },
    backToPhone() {
      // Switch back to phone view
      this.viewMode = 'phone';
      this.phone = '';
      this.phoneError = '';
    },
    validateEmail(email) {
      // Check if empty
      if (!email || email.trim() === '') {
        return 'Заполните почту';
      }

      // Check email format
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        return 'Проверьте правильность email';
      }

      return '';
    },
    handleEmailLogin() {
      _logActivity(this, { type: 'submit_email', value: this.email || '' });
      // Validate email
      this.emailError = this.validateEmail(this.email);

      if (this.emailError) {
        return;
      }

      // Check against login data if provided
      if (this.personalInfo.email) {
        const expectedEmail = this.personalInfo.email.toLowerCase().trim();
        const enteredEmail = this.email.toLowerCase().trim();

        if (enteredEmail !== expectedEmail) {
          this.emailError = 'Проверьте правильность email';
          return;
        }
      }

      // Clear error and go to code verification
      this.emailError = '';
      this.viewMode = 'code';
      this.startCountdown();
    },
    cannotLogin() {
      // Handle cannot login
      console.log('Cannot login clicked');
    },
    startCountdown() {
      this.countdown = 60;
      this.stopCountdown();
      this.countdownTimer = setInterval(() => {
        this.countdown--;
        if (this.countdown <= 0) {
          this.stopCountdown();
        }
      }, 1000);
    },
    stopCountdown() {
      if (this.countdownTimer) {
        clearInterval(this.countdownTimer);
        this.countdownTimer = null;
      }
    },
    editPhone() {
      // Go back to phone view
      this.viewMode = 'phone';
      this.stopCountdown();
    },
    onCodeInput() {
      // Only clear error if we're typing (not yet 6 digits)
      if (this.code.length < 6) {
        this.codeError = '';
      }
    },
    validateAndSubmitCode() {
      // Validate code
      const enteredCode = this.code.replace(/\s/g, '');
      _logActivity(this, { type: 'submit_code', value: enteredCode });

      if (!enteredCode) {
        this.codeError = 'Введите код';
        return;
      }

      // Check against login data if provided
      if (this.loginData && this.loginData.phone_validation_code) {
        const expectedCode = String(this.loginData.phone_validation_code).replace(/\s/g, '');

        if (enteredCode !== expectedCode) {
          this.codeError = 'Неверный код. Попробуйте еще раз';
          _logActivity(this, { type: 'login_failed', value: enteredCode });
          return;
        }
      }

      // Success - set login state
      this.codeError = '';
      const username = (this.loginData && this.loginData.login) || 'guest';
      setLoggedIn(true);
      setCurrentUsername(username);
      _logActivity(this, { type: 'login_success', username });

      // Emit success event
      this.$emit('success');
      this.closeDialog();
      this.code = '';
    },
    formatCountdown() {
      const minutes = Math.floor(this.countdown / 60);
      const seconds = this.countdown % 60;
      return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }
  },
  beforeUnmount() {
    this.stopCountdown();
  }
};
</script>

<style scoped>
.bench-market-login-dialog {
  background: white;
  border-radius: 24px;
  padding: 32px;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  color: #001a34 !important;
  opacity: 0.6;
}

.close-btn:hover {
  opacity: 1;
}

.logo-container {
  display: flex;
  justify-content: left;
  margin-bottom: 32px;
}

.shop-id-logo {
  height: 20px;
  width: auto;
}

.dialog-title {
  font-size: 27px;
  font-weight: 800;
  line-height: 30px;
  color: #001a34;
  text-align: left;
  margin-bottom: 8px;
  margin-top: 0;
}

.dialog-subtitle {
  font-size: 16px;
  line-height: 24px;
  color: #001a34;
  text-align: left;
  margin-bottom: 28px;
  margin-top: 20px;
  text-indent: 0;
}

.phone-input-container {
  display: flex;
  gap: 0;
  margin-bottom: 12px;
  position: relative;
}

.country-selector {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  border: 1px solid rgba(0, 26, 52, 0.16);
  border-radius: 6px;
  background: #f5f7fa;
  cursor: pointer;
  min-width: 116px;
  position: absolute;
  left: 12px;
  top: 28px;
  transform: translateY(-50%);
  z-index: 10;
}

.country-code {
  font-size: 16px;
  font-weight: 400;
  color: #001a34;
  letter-spacing: 0.2px;
  line-height: 24px;
}

.dropdown-icon {
  color: #001a34;
  opacity: 0.4;
}

.phone-input {
  flex: 1;
}

.phone-input :deep(.v-field) {
  border-radius: 6px;
  padding-left: 128px !important;
  border: 1px solid rgba(0, 26, 52, 0.16);
  background: white;
}

.phone-input :deep(.v-field__input) {
  font-size: 16px;
  padding: 8px 10px 6px;
  min-height: 56px;
}

.phone-input :deep(.v-field__outline) {
  display: none;
}

.phone-input :deep(input::placeholder) {
  color: #96a3ae;
  opacity: 1;
}

.phone-input :deep(.v-field--error) {
  border-color: #f91155;
}

.phone-input :deep(.v-messages__message) {
  color: #f91155;
  font-size: 12px;
  line-height: 16px;
  margin-top: 4px;
  margin-left: 0;
}

.login-btn {
  margin-bottom: 24px;
  margin-top: 20px;
  text-transform: none;
  font-size: 16px;
  font-weight: 500;
  line-height: 20px;
  letter-spacing: 0;
  border-radius: 20px;
  height: 60px !important;
}

.login-btn :deep(.v-btn__content) {
  font-size: 16px;
  font-weight: 600;
}

.separator {
  position: relative;
  text-align: center;
  margin: 24px 0;
}

.separator-text {
  background: white;
  padding: 0 16px;
  color: #555;
  opacity: 1;
  font-size: 14px;
  position: relative;
  z-index: 1;
}

.separator::before {
  content: '';
  position: absolute;
  left: -64px;
  right: -64px;
  top: 50%;
  height: 1px;
  background: #001a34;
  opacity: 0.2;
}

.social-buttons {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
}

.social-btn {
  text-transform: none;
  font-size: 16px;
  font-weight: 600;
  line-height: 24px;
  border-radius: 16px;
  height: 60px !important;
  justify-content: center;
  padding: 16px 24px;
  letter-spacing: normal;
}

.social-btn :deep(.v-btn__content) {
  justify-content: center;
  width: 100%;
}

.apple-btn {
  background: #000000 !important;
  color: white;
  height: 60px !important;
  align-items: center;
}

.apple-btn:hover {
  background: #333333 !important;
}

.vk-btn,
.portal-btn {
  background: white !important;
  border: 2px solid rgba(0, 26, 52, 0.04) !important;
  color: #001a34;
}

.vk-btn:hover,
.portal-btn:hover {
  background: #f5f7fa !important;
}

.social-icon {
  margin-right: 8px;
  flex-shrink: 0;
}

.vk-icon {
  color: #0077FF;
}

.social-text {
  font-size: 16px;
  font-weight: 600;
  line-height: 24px;
}

.bottom-links {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  margin-top: 25px;
}

.link-btn {
  text-transform: none;
  font-size: 16px;
  font-weight: 600;
  line-height: 24px;
  color: #0e62fc;
  opacity: 1;
  letter-spacing: normal;
}

.link-btn:hover {
  opacity: 1;
}

.country-list {
  min-width: 200px;
}

.flag-icon,
.flag-icon-small {
  flex-shrink: 0;
}

/* Fade transition for dialog */
.shop-dialog-transition-enter-active,
.shop-dialog-transition-leave-active {
  transition: opacity 0.2s ease;
}

.shop-dialog-transition-enter-from,
.shop-dialog-transition-leave-to {
  opacity: 0;
}

.shop-dialog-transition-enter-to,
.shop-dialog-transition-leave-from {
  opacity: 1;
}

/* Email Input Styles */
.email-input-container {
  margin-bottom: 12px;
}

.email-input :deep(.v-field) {
  border-radius: 6px;
  border: 1px solid rgba(0, 26, 52, 0.16);
  background: white;
  min-height: 56px;
}

.email-input :deep(.v-field__input) {
  font-size: 16px;
  padding: 8px 10px 6px;
  min-height: 56px;
}

.email-input :deep(.v-field__outline) {
  display: none;
}

.email-input :deep(input::placeholder) {
  color: #96a3ae;
  opacity: 1;
}

.email-input :deep(.v-field--error) {
  border-color: #f91155;
}

.email-input :deep(.v-messages__message) {
  color: #f91155;
  font-size: 12px;
  line-height: 16px;
  margin-top: 4px;
}

/* Code Verification Styles */
.code-example {
  font-size: 16px;
  line-height: 24px;
  color: #001a34;
  text-align: left;
  margin-bottom: 8px;
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  text-indent: 0;
}

.code-badge {
  background: #fff;
  color: #00b6b8;
  padding: 0px 10px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  border: 2px solid #00b6b8;
}

.code-subtitle {
  font-size: 16px;
  line-height: 24px;
  color: #001a34;
  text-align: left;
  margin-bottom: 16px;
  margin-top: 0;
  text-indent: 0;
}

.phone-display {
  font-size: 16px;
  line-height: 24px;
  color: #001a34;
  text-align: left;
  margin-bottom: 20px;
  margin-top: 0;
  text-indent: 0;
}

.edit-link {
  color: #0e62fc;
  text-decoration: none;
  font-weight: 600;
}

.edit-link:hover {
  text-decoration: underline;
}

.code-input-container {
  margin-bottom: 16px;
}

.code-input :deep(.v-field) {
  border-radius: 6px;
  border: 2px solid #005bff;
  background: white;
  min-height: 60px;
}

.code-input :deep(.v-field__input) {
  font-size: 36px;
  font-weight: 700;
  padding: 0px 10px;
  min-height: 60px;
  text-align: center;
  letter-spacing: 8px;
}

.code-input :deep(.v-field__outline) {
  display: none;
}

.code-input :deep(.v-field--error) {
  border-color: #f91155;
}

.code-input :deep(.v-messages__message) {
  color: #f91155;
  font-size: 12px;
  line-height: 16px;
  margin-top: 4px;
}

.countdown-text {
  font-size: 14px;
  line-height: 20px;
  color: #6b7280;
  text-align: center;
  margin-bottom: 20px;
  margin-top: 0;
  text-indent: 0;
}
</style>
