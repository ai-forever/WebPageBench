<template>
  <div v-if="configLoaded" class="bench-grocery">
    <div class="auth-page">
      <div class="desktop-container">
        <div class="left-panel">
          <div class="content-wrapper">
            <!-- Loading Spinner -->
            <div class="spinner-container">
              <v-progress-circular
                :size="30"
                :width="2"
                color="grey"
                indeterminate
              ></v-progress-circular>
            </div>

            <!-- Loading Text -->
            <p class="loading-text">Телепортируем вас<br>в каталог</p>
          </div>
        </div>

        <div class="right-panel">
          <div class="illustration-container">
            <!-- UFO Illustration -->
            <svg width="256" height="160" fill="none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 160">
              <path opacity="0.25" d="M152.8 118.7c-3.5-2-8.7-3.7-14.9-4.7l-13.4 6.3-8.5-.6-3.3-6.9c-11.6.8-21.3 3.3-26.1 6.7-21.9 2.2-36.6 6.2-36.6 10.8 0 6.9 33.4 12.5 74.7 12.5 41.3 0 74.7-5.6 74.7-12.5 0-5.2-19.3-9.8-46.6-11.6ZM160.1 46.6c-28.8-12.7-54.8-17-58-9.5-2.4 5.4 7.8 15.5 24.6 25.5-.2.5-.4 1-.6 1.3-1.6 3.7 6.9 11.1 19.1 16.5 12.2 5.4 23.4 6.7 25.1 3 .1-.3.3-.7.6-1.3 18.7 5.7 33 6.4 35.4 1 3.2-7.5-17.4-23.8-46.2-36.5Z" fill="#8C9AA1"></path>
              <path d="M126.6 62.6c-16.8-10-27-20.1-24.6-25.5 3.3-7.5 29.3-3.2 58.1 9.5s49.4 29 46.1 36.5c-2.4 5.4-16.7 4.7-35.4-1" stroke="#8C9AA1" stroke-width="2" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path>
              <path d="M206.5 81.9c1.6-4.6-7.8-28.7-42.6-44.1-34.8-15.4-59-5.9-61.3-1.7" stroke="#8C9AA1" stroke-width="2" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path>
              <path d="M137.5 30.1c7.9-7.1 20.6-9 31.7-4.1 10.8 4.8 17.9 15 18.3 25.4M169.2 26l1.6-3.6M171.9 22.6a2.8 2.8 0 1 0 0-5.6 2.8 2.8 0 0 0 0 5.6Z" stroke="#8C9AA1" stroke-width="2" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path>
              <path d="M166.7 31.7c-.9-.4-2 0-2.4.9-.2.4-.2.9 0 1.4.2.4.5.8 1 1 .2.1.5.2.7.2.2 0 .4 0 .7-.1.4-.2.8-.5 1-1 .2-.5.2-.9 0-1.4-.3-.4-.6-.8-1-1ZM155 27.6c-.9-.4-2 0-2.4.9-.4.9 0 2 .9 2.4.2.1.5.2.7.2.7 0 1.4-.4 1.6-1.1.2-.4.2-.9 0-1.4 0-.5-.3-.8-.8-1ZM178.5 38.5c-.2-.4-.5-.8-1-1-.9-.4-2 0-2.4.9-.2.4-.2.9 0 1.4.2.4.5.8 1 1 .2.1.5.2.7.2.7 0 1.4-.4 1.6-1.1.3-.5.3-.9.1-1.4Z" fill="#8C9AA1"></path>
              <path d="M170.333 83.35c1.65-3.74-6.925-11.145-19.153-16.54-12.228-5.396-23.478-6.739-25.128-3-1.65 3.74 6.925 11.144 19.153 16.54 12.228 5.396 23.478 6.738 25.128 3Z" stroke="#8C9AA1" stroke-width="2" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path>
              <path d="M170.3 83.3c.4-.8 1.8-4 2.1-4.8 1.6-3.7-6.9-11.1-19.1-16.5-12.2-5.4-23.4-6.7-25.1-3-.4.8-1.8 4-2.1 4.8" stroke="#8C9AA1" stroke-width="2" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path>
              <path d="M132.1 57c-8-6.1-15.4-16.3-16.6-23.5M160.1 46.6 153.3 62M171.2 74.3c10 1.8 22.5.4 28.5-3.5M165.575 81.25c.758-1.718-6.41-6.545-16.01-10.78-9.601-4.237-17.998-6.278-18.756-4.56-.758 1.718 6.41 6.544 16.011 10.78 9.6 4.237 17.997 6.278 18.755 4.56Z" stroke="#8C9AA1" stroke-width="2" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path>
              <path d="m117 72.9-44 43.2M165 91.7l-5.7 23.7M152.6 90.1l-4.1 11.6M98 107.8l-17.7 21" stroke="#FF6B00" stroke-width="2" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path>
              <path opacity="0.25" d="m142.5 111.7-18 8.6-8.5-.6-8.5-18 18-8.6 8.4.7 8.6 17.9Z" fill="#FF6B00"></path>
              <path d="m133.878 93.804-17.972 8.545 8.545 17.971 17.972-8.545-8.545-17.971Z" stroke="#FF6B00" stroke-width="2" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path>
              <path d="m116 119.7 8.5.6-8.6-18-8.4-.6 8.5 18Z" stroke="#FF6B00" stroke-width="2" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path>
              <path d="m125.5 93.1 8.4.7-18 8.5-8.4-.6 18-8.6Z" stroke="#FF6B00" stroke-width="2" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path>
              <path d="m116.8 97.2 8.1.8 8.6 18" stroke="#FF6B00" stroke-width="2" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path>
              <path d="m111.9 111.1 8.3.2 18-8.6" stroke="#FF6B00" stroke-width="2" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path>
            </svg>

            <!-- Sber ID Logo -->
            <div class="sberid-logo">
              <svg width="105" height="22" xmlns="http://www.w3.org/2000/svg">
                <path fill-rule="evenodd" clip-rule="evenodd" d="m15.769 4.017 2.135-1.577a10.95 10.95 0 0 0-6.9-2.44h-.005a10.97 10.97 0 0 0-7.378 2.844v-.001a10.97 10.97 0 0 0-3.608 7.61l-.002.045c-.007.164-.011.33-.011.494v.01a10.97 10.97 0 0 0 2.907 7.448 10.969 10.969 0 0 0 7.544 3.536 10.963 10.963 0 0 0 7.928-2.83A10.97 10.97 0 0 0 22 10.999a11.06 11.06 0 0 0-.173-1.971l-2.367 1.745v.226a8.436 8.436 0 0 1-2.483 5.98h-.001a8.514 8.514 0 0 1-.287.274l-.017.015A8.433 8.433 0 0 1 11 19.46v-.002a8.435 8.435 0 0 1-5.98-2.48l.001-.001a8.31 8.31 0 0 1-.288-.302l-.003-.003a8.43 8.43 0 0 1-2.18-6.064l.002-.031H2.55a8.437 8.437 0 0 1 2.472-5.558l.002.002a8.429 8.429 0 0 1 5.969-2.48h.014c.139 0 .277.005.414.012V2.55a8.416 8.416 0 0 1 4.347 1.466Zm5.253 2.445a11.034 11.034 0 0 0-1.318-2.188l-8.702 6.416-4.188-2.625v3.158l4.188 2.625 10.02-7.386Zm66.163 11.165h2.357V4.43h-2.357v13.198Zm13.358-3.318c-.792.767-2.011 1.15-3.658 1.15h-2.13V6.598h2.15c1.67 0 2.893.364 3.666 1.093.773.73 1.16 1.829 1.16 3.3 0 1.445-.396 2.551-1.188 3.318Zm1.867-8.24c-1.195-1.093-3.017-1.64-5.468-1.64h-4.544v13.198h4.487c1.069 0 2.052-.132 2.951-.396s1.672-.672 2.319-1.225 1.15-1.264 1.509-2.13c.358-.868.537-1.905.537-3.112 0-2.036-.597-3.6-1.791-4.694Zm-38.512.557 2.983-2.198h-9.982v13.201h9.982v-2.198h-7.133v-3.38h6.084V9.854h-6.084V6.626h4.15Zm-18 8.805h2.97c1.759 0 2.65-.585 2.65-1.83 0-1.217-.842-1.83-2.65-1.83h-2.97v3.66Zm0-5.857h3.466c3.148 0 4.882 1.388 4.882 3.908 0 2.636-1.913 4.147-5.25 4.147H43.05V4.428h11.365L51.43 6.626h-5.533v2.948Zm29.01 2.118h-2.526V6.626h2.525c1.825 0 2.83.9 2.83 2.533s-1.005 2.533-2.83 2.533Zm.06-7.264h-5.434v13.201h2.848v-3.74h2.586c3.468 0 5.623-1.823 5.623-4.737s-2.155-4.724-5.623-4.724ZM35.7 15.387c.879 0 1.73-.213 2.46-.616l.631-.346 1.843 1.36c-1.215 1.302-3.008 2.018-5.062 2.018-1.963 0-3.753-.693-5.04-1.952-1.285-1.255-1.992-2.994-1.992-4.895 0-1.894.71-3.607 1.998-4.825 1.281-1.21 3.075-1.877 5.052-1.877 1.823 0 3.417.554 4.61 1.602l.135.119L38.29 7.48c-.748-.537-1.619-.81-2.59-.81-2.569 0-4.433 1.833-4.433 4.358 0 2.526 1.864 4.359 4.432 4.359Z" fill="#8C9AA1"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import { GET_TRACK_CONFIG } from "@/store/actions.type";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";
import { setGroceryLoggedIn, setGroceryCurrentUser, syncGrocerySessionFromTrackConfig } from "@/utils/localCache.js";
import { getBenchPersonalInfo, getBenchSessionUser } from "@/common/benchPersonalInfo.js";

export default defineComponent({
  name: "GroceryAuthorization",
  mixins: [StateDelayMixin],
  computed: {
    ...mapGetters(["trackConfig"]),
    configLoaded() {
      return this.trackConfig && Object.keys(this.trackConfig).length > 0;
    },
    common() {
      return (this.trackConfig && this.trackConfig.common_elements) || {};
    },
    testData() {
      return (this.trackConfig && this.trackConfig.test_data) || {};
    },
    userData() {
      return (this.testData && this.testData.user_data) || {};
    },
    loginData() {
      return (this.testData && this.testData.login_data) || {};
    },
    userShortName() {
      return getBenchPersonalInfo(this.trackConfig).shortName;
    },
    authDelay() {
      return (this.testData && this.testData.auth_delay) || 2;
    },
  },
  methods: {
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
            this.$router.push({ name: "not_found" });
            return;
          }
          this.startAuthProcess();
        });
    },
    startAuthProcess() {
      // Simulate authorization process
      setTimeout(() => {
        // Set user as logged in
        setGroceryLoggedIn(true);
        setGroceryCurrentUser(getBenchSessionUser(this.trackConfig));
        syncGrocerySessionFromTrackConfig(this.trackConfig);
        
        // Navigate back to main
        this.$router.back();
      }, this.authDelay * 1000);
    },
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      this.startAuthProcess();
    }
  },
});
</script>

<style scoped>
.bench-grocery {
  --grocery-primary: #f3345c;
  --grocery-bg: #f2f2f2;
  --grocery-text: #333;
  --grocery-text-grey: #595959;
  --grocery-border: #e0e0e0;
}

.auth-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #00d4d4 0%, #00ff7f 100%);
  font-family: SBSansInterface, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.desktop-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
}

.left-panel {
  background: #f9f9f9;
  border-radius: 24px 0 0 24px;
  padding: 80px 60px;
  width: 420px;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.content-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.spinner-container {
  margin-bottom: 24px;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 15px;
  font-weight: 400;
  line-height: 1.2;
  color: #aaa;
  margin: 0;
}

.right-panel {
  background: white;
  border-radius: 0 24px 24px 0;
  padding: 80px 60px;
  width: 420px;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.illustration-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
}

.sberid-logo {
  display: flex;
  align-items: center;
  justify-content: center;
}

.footer {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(10px);
  padding: 6px 40px;
  color: white;
  margin-top: auto;
}

.footer-content {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0 auto;
}

.footer-links {
  display: flex;
  gap: 24px;
  align-items: center;
  flex-wrap: wrap;
}

.footer-links a {
  color: white;
  text-decoration: none;
  font-size: 13px;
  white-space: nowrap;
  transition: opacity 0.2s;
}

.footer-links a:hover {
  opacity: 0.8;
}

.footer-info {
  display: flex;
  gap: 24px;
  align-items: center;
  flex-shrink: 0;
}

.footer-info span {
  font-size: 13px;
  color: white;
  white-space: nowrap;
}

.footer-info a {
  color: white;
  text-decoration: none;
}

.footer-info a:hover {
  text-decoration: underline;
}

@media (max-width: 1100px) {
  .footer-content {
    flex-direction: column;
    gap: 16px;
    align-items: center;
  }

  .footer-links {
    justify-content: center;
  }
}

@media (max-width: 968px) {
  .desktop-container {
    flex-direction: column;
  }

  .left-panel {
    border-radius: 24px 24px 0 0;
    width: 100%;
    max-width: 500px;
    padding: 60px 40px;
  }

  .right-panel {
    border-radius: 0 0 24px 24px;
    width: 100%;
    max-width: 500px;
    padding: 60px 40px;
  }

  .footer-links {
    flex-direction: column;
    gap: 12px;
  }

  .footer-info {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}
</style>

<style src="@/assets/grocery.css"></style>

